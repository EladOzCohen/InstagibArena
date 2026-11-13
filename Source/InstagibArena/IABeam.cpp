// Instagib Arena

#include "IABeam.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

AIABeam::AIABeam()
{
	PrimaryActorTick.bCanEverTick = true;
	SetReplicates(false);

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CylinderFinder.Succeeded())
	{
		Mesh->SetStaticMesh(CylinderFinder.Object);
	}
}

void AIABeam::Init(const FVector& Start, const FVector& End, const FLinearColor& Color)
{
	const FVector Delta = End - Start;
	Length = Delta.Size();
	if (Length < 1.f)
	{
		Destroy();
		return;
	}

	// The cylinder's long axis is Z, so point Z along the shot.
	SetActorLocationAndRotation(Start + Delta * 0.5f, FRotationMatrix::MakeFromZ(Delta).Rotator());

	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody")))
	{
		Material = UMaterialInstanceDynamic::Create(Base, this);
		// A thin, whitened core ...
		Material->SetVectorParameterValue(TEXT("Color"), FMath::Lerp(Color, FLinearColor::White, 0.45f));
		Material->SetScalarParameterValue(TEXT("Glow"), 8.f);
		Mesh->SetMaterial(0, Material);
	}

	// ... inside a soft coloured sleeve that fades towards its silhouette (child of the core: it thins out with it).
	UStaticMesh* Cylinder = Mesh->GetStaticMesh();
	if (UMaterialInterface* ShellBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAGlowShell.M_IAGlowShell")))
	{
		Shell = NewObject<UStaticMeshComponent>(this);
		Shell->SetStaticMesh(Cylinder);
		Shell->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Shell->SetCastShadow(false);
		Shell->SetupAttachment(Mesh);
		Shell->SetRelativeScale3D(FVector(4.5f, 4.5f, 1.f));
		Shell->RegisterComponent();
		ShellMaterial = UMaterialInstanceDynamic::Create(ShellBase, this);
		ShellMaterial->SetVectorParameterValue(TEXT("Color"), Color);
		ShellMaterial->SetScalarParameterValue(TEXT("Glow"), 2.2f);
		ShellMaterial->SetScalarParameterValue(TEXT("Exponent"), 1.8f);
		ShellMaterial->SetScalarParameterValue(TEXT("HideCaps"), 1.f);
		Shell->SetMaterial(0, ShellMaterial);
	}

	Mesh->SetWorldScale3D(FVector(StartThickness / 100.f, StartThickness / 100.f, Length / 100.f));
}

void AIABeam::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	Age += DeltaSeconds;
	if (Age >= Lifetime)
	{
		Destroy();
		return;
	}

	// Thins out quickly at first, then lingers.
	const float Alpha = FMath::Pow(1.f - Age / Lifetime, 1.6f);
	const float Thickness = FMath::Max(0.2f, StartThickness * Alpha);
	Mesh->SetWorldScale3D(FVector(Thickness / 100.f, Thickness / 100.f, Length / 100.f));
	if (Material)
	{
		Material->SetScalarParameterValue(TEXT("Glow"), 8.f * Alpha);
	}
	if (ShellMaterial)
	{
		ShellMaterial->SetScalarParameterValue(TEXT("Glow"), 2.2f * Alpha);
	}
}
