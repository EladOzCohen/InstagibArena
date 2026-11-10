// Instagib Arena

#include "IAJumpPad.h"
#include "IAAudioSubsystem.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

AIAJumpPad::AIAJumpPad()
{
	PrimaryActorTick.bCanEverTick = true;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeFinder(TEXT("/Engine/BasicShapes/Cone.Cone"));

	// The pad has no blocking collision: the floor below stays the walkable surface, and the pad is only a trigger.
	auto MakeMesh = [&](const TCHAR* Name, UStaticMesh* Mesh, const FVector& Location, const FVector& Scale)
	{
		UStaticMeshComponent* Comp = CreateDefaultSubobject<UStaticMeshComponent>(Name);
		Comp->SetupAttachment(Root);
		Comp->SetStaticMesh(Mesh);
		Comp->SetRelativeLocation(Location);
		Comp->SetRelativeScale3D(Scale);
		Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Comp->SetCastShadow(false);
		return Comp;
	};

	Base = MakeMesh(TEXT("Base"), CylinderFinder.Object, FVector(0.f, 0.f, 4.f), FVector(1.9f, 1.9f, 0.08f));
	GlowDisc = MakeMesh(TEXT("GlowDisc"), CylinderFinder.Object, FVector(0.f, 0.f, 9.f), FVector(1.5f, 1.5f, 0.02f));
	Beam = MakeMesh(TEXT("Beam"), ConeFinder.Object, FVector(0.f, 0.f, 70.f), FVector(1.1f, 1.1f, 1.2f));

	Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
	Trigger->SetupAttachment(Root);
	Trigger->SetBoxExtent(FVector(85.f, 85.f, 55.f));
	Trigger->SetRelativeLocation(FVector(0.f, 0.f, 55.f));
	Trigger->SetCollisionProfileName(TEXT("OverlapOnlyPawn"));
	Trigger->SetGenerateOverlapEvents(true);

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Root);
	Light->SetRelativeLocation(FVector(0.f, 0.f, 60.f));
	Light->SetAttenuationRadius(450.f);
	Light->SetIntensity(40.f);
	Light->SetCastShadows(false);
}

void AIAJumpPad::BeginPlay()
{
	Super::BeginPlay();

	Trigger->OnComponentBeginOverlap.AddDynamic(this, &AIAJumpPad::OnPadOverlap);
	Light->SetLightColor(PadColor);

	if (GetNetMode() == NM_DedicatedServer)
	{
		SetActorTickEnabled(false);
		return;
	}

	if (UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody")))
	{
		UMaterialInstanceDynamic* BaseMaterial = UMaterialInstanceDynamic::Create(Material, this);
		BaseMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.05f, 0.06f, 0.08f));
		BaseMaterial->SetScalarParameterValue(TEXT("Metallic"), 0.6f);
		Base->SetMaterial(0, BaseMaterial);

		GlowMaterial = UMaterialInstanceDynamic::Create(Material, this);
		GlowMaterial->SetVectorParameterValue(TEXT("Color"), PadColor);
		GlowMaterial->SetScalarParameterValue(TEXT("Glow"), 4.f);
		GlowDisc->SetMaterial(0, GlowMaterial);

		BeamMaterial = UMaterialInstanceDynamic::Create(Material, this);
		BeamMaterial->SetVectorParameterValue(TEXT("Color"), PadColor);
		BeamMaterial->SetScalarParameterValue(TEXT("Glow"), 1.5f);
		Beam->SetMaterial(0, BeamMaterial);
	}
	Phase = FMath::FRand() * 6.28f;
}

void AIAJumpPad::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!GlowMaterial)
	{
		return;
	}

	Phase += DeltaSeconds * 3.2f;
	const double Now = GetWorld()->GetTimeSeconds();
	const float Pulse = 0.5f + 0.5f * FMath::Sin(Phase);
	const float Flash = Now < FlashUntil ? static_cast<float>((FlashUntil - Now) / 0.35) : 0.f;

	GlowMaterial->SetScalarParameterValue(TEXT("Glow"), 2.5f + 4.f * Pulse + 14.f * Flash);
	if (BeamMaterial)
	{
		BeamMaterial->SetScalarParameterValue(TEXT("Glow"), 0.6f + 2.f * Pulse + 6.f * Flash);
	}
	Light->SetIntensity(30.f + 25.f * Pulse + 120.f * Flash);

	// The cone breathes upwards like a pointer.
	Beam->SetRelativeLocation(FVector(0.f, 0.f, 60.f + 10.f * Pulse));
	Beam->SetRelativeScale3D(FVector(1.0f - 0.2f * Pulse, 1.0f - 0.2f * Pulse, 1.1f + 0.3f * Pulse));
}

void AIAJumpPad::OnPadOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
	int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	ACharacter* Character = Cast<ACharacter>(OtherActor);
	if (!Character || !Cast<UCapsuleComponent>(OtherComp) || !GetWorld())
	{
		return;
	}

	const double Now = GetWorld()->GetTimeSeconds();
	double& Last = LastLaunch.FindOrAdd(Character);
	if (Now - Last < 0.5)
	{
		return;
	}
	Last = Now;

	// Cosmetics on every machine.
	FlashUntil = Now + 0.35;
	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
	{
		Audio->PlayAt(EIASound::JumpPad, GetActorLocation(), 1.f, 0.05f);
	}

	// The server launches everyone it simulates; the controlling client launches its own character at the
	// same moment so that prediction and server agree.
	if (HasAuthority() || Character->IsLocallyControlled())
	{
		Character->LaunchCharacter(LaunchVelocity, true, true);
	}
}
