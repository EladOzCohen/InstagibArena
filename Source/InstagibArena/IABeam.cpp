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
		Material->SetVectorParameterValue(TEXT("Color"), Color);
		Material->SetScalarParameterValue(TEXT("Glow"), 10.f);
		Mesh->SetMaterial(0, Material);
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
		Material->SetScalarParameterValue(TEXT("Glow"), 10.f * Alpha);
	}
}
