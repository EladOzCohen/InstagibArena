// Instagib Arena

#include "IABeam.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const FLinearColor Rainbow[6] = {
		FLinearColor(1.f, 0.06f, 0.06f), FLinearColor(1.f, 0.42f, 0.02f), FLinearColor(1.f, 0.9f, 0.05f),
		FLinearColor(0.1f, 1.f, 0.2f), FLinearColor(0.1f, 0.4f, 1.f), FLinearColor(0.7f, 0.15f, 1.f) };
}

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

void AIABeam::Init(const FVector& Start, const FVector& End, const FLinearColor& Color, uint8 Style, bool bTeamColors)
{
	const FVector Delta = End - Start;
	Length = Delta.Size();
	if (Length < 1.f)
	{
		Destroy();
		return;
	}
	BeamStart = Start;
	BeamEnd = End;

	// The look of each style: thickness of the hot core, how long it stays, how bright it is, how wide the soft sleeve is.
	float ShellScale = 4.5f;
	switch (Style)
	{
	case 1: StartThickness = 1.1f; Lifetime = 0.34f; CoreGlow = 11.f; ShellGlow = 2.6f; ShellScale = 3.2f; break;   // Needle
	case 2: StartThickness = 5.2f; Lifetime = 0.55f; CoreGlow = 7.f;  ShellGlow = 2.0f; ShellScale = 3.4f; break;   // Lance
	case 3: StartThickness = 3.0f; Lifetime = 0.45f; CoreGlow = 9.f;  ShellGlow = 2.4f; break;                       // Pulse
	case 4: StartThickness = 2.4f; Lifetime = 0.5f;  CoreGlow = 7.f;  ShellGlow = 1.2f; break;                       // Confetti
	default: break;
	}

	// The cylinder's long axis is Z, so point Z along the shot.
	SetActorLocationAndRotation(Start + Delta * 0.5f, FRotationMatrix::MakeFromZ(Delta).Rotator());

	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody")))
	{
		Material = UMaterialInstanceDynamic::Create(Base, this);
		// A thin, whitened core ...
		Material->SetVectorParameterValue(TEXT("Color"), FMath::Lerp(Color, FLinearColor::White, 0.45f));
		Material->SetScalarParameterValue(TEXT("Glow"), CoreGlow);
		Mesh->SetMaterial(0, Material);
	}

	// ... inside a soft coloured sleeve that fades towards its silhouette (child of the core: it thins out with it).
	UStaticMesh* Cylinder = Mesh->GetStaticMesh();
	UMaterialInterface* ShellBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAGlowShell.M_IAGlowShell"));
	if (ShellBase)
	{
		Shell = NewObject<UStaticMeshComponent>(this);
		Shell->SetStaticMesh(Cylinder);
		Shell->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Shell->SetCastShadow(false);
		Shell->SetupAttachment(Mesh);
		Shell->SetRelativeScale3D(FVector(ShellScale, ShellScale, 1.f));
		Shell->RegisterComponent();
		ShellMaterial = UMaterialInstanceDynamic::Create(ShellBase, this);
		ShellMaterial->SetVectorParameterValue(TEXT("Color"), Color);
		ShellMaterial->SetScalarParameterValue(TEXT("Glow"), ShellGlow);
		ShellMaterial->SetScalarParameterValue(TEXT("Exponent"), 1.8f);
		ShellMaterial->SetScalarParameterValue(TEXT("HideCaps"), 1.f);
		Shell->SetMaterial(0, ShellMaterial);
	}

	Mesh->SetWorldScale3D(FVector(StartThickness / 100.f, StartThickness / 100.f, Length / 100.f));

	if (Style == 3)
	{
		// Pulse: dashes of light with dark gaps (about 160 dashes at most, longer ones on long shots).
		BuildDashes(Color, false, FMath::Max(64.f, Length / 160.f), 0.55f, ShellBase);
	}
	else if (Style == 4)
	{
		// Confetti: short dashes in the colours of the rainbow, and paper flakes that flutter down.
		BuildDashes(Color, !bTeamColors, FMath::Max(26.f, Length / 180.f), 0.8f, nullptr);
		BuildFlakes(FMath::Clamp(FMath::RoundToInt(Length / 45.f), 12, 70));
	}
}

void AIABeam::BuildDashes(const FLinearColor& Color, bool bRainbow, float Period, float DashFraction, UMaterialInterface* ShellBase)
{
	UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody"));
	UStaticMesh* Cylinder = Mesh->GetStaticMesh();
	if (!Base || !Cylinder)
	{
		return;
	}
	// The continuous core and sleeve are hidden; the dashes are children of the core (in its unit space: Z from -50 to 50 = the whole shot).
	Mesh->SetVisibility(false, false);
	if (Shell)
	{
		Shell->SetVisibility(false);
	}

	const int32 Colors = bRainbow ? 6 : 1;
	for (int32 C = 0; C < Colors; ++C)
	{
		UMaterialInstanceDynamic* DashMaterial = UMaterialInstanceDynamic::Create(Base, this);
		const FLinearColor Tint = bRainbow ? Rainbow[C] : Color;
		DashMaterial->SetVectorParameterValue(TEXT("Color"), FMath::Lerp(Tint, FLinearColor::White, bRainbow ? 0.15f : 0.45f));
		DashMaterial->SetScalarParameterValue(TEXT("Glow"), CoreGlow);
		DashMaterials.Add(DashMaterial);

		UInstancedStaticMeshComponent* Batch = NewObject<UInstancedStaticMeshComponent>(this);
		Batch->SetStaticMesh(Cylinder);
		Batch->SetMaterial(0, DashMaterial);
		Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Batch->SetCastShadow(false);
		Batch->SetupAttachment(Mesh);
		Batch->RegisterComponent();
		Dashes.Add(Batch);
	}

	// A dashed sleeve in the same rhythm (Pulse only).
	UInstancedStaticMeshComponent* SleeveBatch = nullptr;
	if (ShellBase && ShellMaterial)
	{
		SleeveBatch = NewObject<UInstancedStaticMeshComponent>(this);
		SleeveBatch->SetStaticMesh(Cylinder);
		SleeveBatch->SetMaterial(0, ShellMaterial);
		SleeveBatch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		SleeveBatch->SetCastShadow(false);
		SleeveBatch->SetupAttachment(Mesh);
		SleeveBatch->RegisterComponent();
		Dashes.Add(SleeveBatch);
	}

	const int32 Count = FMath::Max(1, FMath::FloorToInt(Length / Period));
	const float DashLocal = 100.f * (Period * DashFraction) / Length;
	for (int32 I = 0; I < Count; ++I)
	{
		const float CentreLocal = -50.f + 100.f * ((I + 0.5f) * Period) / Length;
		const FVector Scale(1.f, 1.f, DashLocal / 100.f);
		Dashes[I % Colors]->AddInstance(FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, CentreLocal), Scale), false);
		if (SleeveBatch)
		{
			SleeveBatch->AddInstance(FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, CentreLocal), FVector(4.5f, 4.5f, Scale.Z)), false);
		}
	}
}

void AIABeam::BuildFlakes(int32 Count)
{
	UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody"));
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (!Base || !Cube)
	{
		return;
	}
	for (int32 C = 0; C < 6; ++C)
	{
		UMaterialInstanceDynamic* FlakeMaterial = UMaterialInstanceDynamic::Create(Base, this);
		FlakeMaterial->SetVectorParameterValue(TEXT("Color"), Rainbow[C]);
		FlakeMaterial->SetScalarParameterValue(TEXT("Glow"), 2.5f);

		// World space: the flakes must not follow the stretched core.
		UInstancedStaticMeshComponent* Batch = NewObject<UInstancedStaticMeshComponent>(this);
		Batch->SetStaticMesh(Cube);
		Batch->SetMaterial(0, FlakeMaterial);
		Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Batch->SetCastShadow(false);
		Batch->SetUsingAbsoluteLocation(true);
		Batch->SetUsingAbsoluteRotation(true);
		Batch->SetUsingAbsoluteScale(true);
		Batch->SetupAttachment(Mesh);
		Batch->RegisterComponent();
		Batch->SetWorldTransform(FTransform::Identity);
		Flakes.Add(Batch);
	}
	FlakeLife = 1.5f;
	for (int32 I = 0; I < Count; ++I)
	{
		FFlake Flake;
		Flake.Batch = I % 6;
		Flake.Location = FMath::Lerp(BeamStart, BeamEnd, FMath::FRand()) + FMath::VRand() * 6.f;
		Flake.Velocity = FMath::VRand() * FMath::FRandRange(40.f, 140.f) + FVector(0.f, 0.f, 60.f);
		Flake.Rotation = FRotator(FMath::FRandRange(0.f, 360.f), FMath::FRandRange(0.f, 360.f), FMath::FRandRange(0.f, 360.f));
		Flake.Spin = FRotator(FMath::FRandRange(-500.f, 500.f), FMath::FRandRange(-500.f, 500.f), FMath::FRandRange(-500.f, 500.f));
		Flake.Instance = Flakes[Flake.Batch]->AddInstance(FTransform(Flake.Rotation, Flake.Location, FVector(0.022f, 0.016f, 0.003f)), true);
		FlakeState.Add(Flake);
	}
}

void AIABeam::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	Age += DeltaSeconds;
	if (Age >= FMath::Max(Lifetime, FlakeLife))
	{
		Destroy();
		return;
	}

	// Thins out quickly at first, then lingers.
	const float Alpha = Age < Lifetime ? FMath::Pow(1.f - Age / Lifetime, 1.6f) : 0.f;
	const float Thickness = FMath::Max(0.2f, StartThickness * Alpha);
	Mesh->SetWorldScale3D(FVector(Thickness / 100.f, Thickness / 100.f, Length / 100.f));
	if (Material)
	{
		Material->SetScalarParameterValue(TEXT("Glow"), CoreGlow * Alpha);
	}
	if (ShellMaterial)
	{
		ShellMaterial->SetScalarParameterValue(TEXT("Glow"), ShellGlow * Alpha);
	}
	for (UMaterialInstanceDynamic* DashMaterial : DashMaterials)
	{
		DashMaterial->SetScalarParameterValue(TEXT("Glow"), CoreGlow * Alpha);
	}
	if (Age >= Lifetime)
	{
		for (UInstancedStaticMeshComponent* Batch : Dashes)
		{
			Batch->SetVisibility(false);
		}
		Mesh->SetVisibility(false, false);
		if (Shell)
		{
			Shell->SetVisibility(false);
		}
	}

	// Confetti flakes: they flutter (strong air drag, a little sideways sway) and shrink away at the end.
	if (FlakeState.Num() > 0)
	{
		const float Dt = FMath::Min(DeltaSeconds, 0.05f);
		const float Shrink = FMath::Clamp((FlakeLife - Age) / 0.4f, 0.f, 1.f);
		for (int32 I = 0; I < FlakeState.Num(); ++I)
		{
			FFlake& Flake = FlakeState[I];
			Flake.Velocity.Z -= 260.f * Dt;
			Flake.Velocity *= FMath::Max(0.f, 1.f - 2.6f * Dt);
			Flake.Location += (Flake.Velocity + FVector(FMath::Sin(Age * 7.f + I) * 30.f, FMath::Cos(Age * 5.f + I) * 30.f, 0.f)) * Dt;
			Flake.Rotation += Flake.Spin * Dt;
			Flakes[Flake.Batch]->UpdateInstanceTransform(Flake.Instance, FTransform(Flake.Rotation, Flake.Location, FVector(0.022f, 0.016f, 0.003f) * Shrink), true, false);
		}
		for (UInstancedStaticMeshComponent* Batch : Flakes)
		{
			Batch->MarkRenderStateDirty();
		}
	}
}
