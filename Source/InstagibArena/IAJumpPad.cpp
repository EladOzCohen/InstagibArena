// Instagib Arena

#include "IAJumpPad.h"
#include "IAAudioSubsystem.h"
#include "InstagibArena.h"
#include "EngineUtils.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "GameFramework/PlayerController.h"
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

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> PlaneFinder(TEXT("/Engine/BasicShapes/Plane.Plane"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));

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

	// Sizes in cm: a 190 cm steel slab 5 cm thick, a 178 cm painted deck on top, a 7 cm wide rim 3.5 cm above the slab.
	Base = MakeMesh(TEXT("Base"), CubeFinder.Object, FVector(0.f, 0.f, 2.5f), FVector(1.9f, 1.9f, 0.05f));
	Deck = MakeMesh(TEXT("Deck"), PlaneFinder.Object, FVector(0.f, 0.f, 5.15f), FVector(1.78f, 1.78f, 1.f));
	const float RimZ = 5.f + 1.75f;
	const TCHAR* RimNames[4] = { TEXT("RimN"), TEXT("RimS"), TEXT("RimE"), TEXT("RimW") };
	const FVector RimLoc[4] = { FVector(0.f, 91.5f, RimZ), FVector(0.f, -91.5f, RimZ), FVector(91.5f, 0.f, RimZ), FVector(-91.5f, 0.f, RimZ) };
	const FVector RimScale[4] = { FVector(1.9f, 0.07f, 0.035f), FVector(1.9f, 0.07f, 0.035f), FVector(0.07f, 1.76f, 0.035f), FVector(0.07f, 1.76f, 0.035f) };
	for (int32 I = 0; I < 4; ++I)
	{
		Rim.Add(MakeMesh(RimNames[I], CubeFinder.Object, RimLoc[I], RimScale[I]));
	}

	// The light column: 150 cm wide, 260 cm tall, no shadow, never blocks anything.
	Column = MakeMesh(TEXT("Column"), CylinderFinder.Object, FVector(0.f, 0.f, 8.5f + 130.f), FVector(1.5f, 1.5f, 2.6f));
	Column->SetCullDistance(6000.f);

	Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
	Trigger->SetupAttachment(Root);
	Trigger->SetBoxExtent(FVector(85.f, 85.f, 55.f));
	Trigger->SetRelativeLocation(FVector(0.f, 0.f, 55.f));
	Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Trigger->SetCollisionObjectType(ECC_WorldDynamic);
	Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Trigger->SetGenerateOverlapEvents(true);

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Root);
	Light->SetRelativeLocation(FVector(0.f, 0.f, 70.f));
	Light->SetAttenuationRadius(420.f);
	Light->SetIntensity(18.f);
	Light->SetCastShadows(false);
}

void AIAJumpPad::BeginPlay()
{
	Super::BeginPlay();

	Trigger->OnComponentBeginOverlap.AddDynamic(this, &AIAJumpPad::OnPadOverlap);
	Light->SetLightColor(PadColor);

#if !UE_BUILD_SHIPPING
	bPadTest = FParse::Param(FCommandLine::Get(), TEXT("IAPadTest"));
	if (bPadTest && HasAuthority())
	{
		// Only the first pad of the level runs the test.
		bool bFirst = true;
		for (TActorIterator<AIAJumpPad> It(GetWorld()); It; ++It)
		{
			if (*It != this && It->GetName() < GetName())
			{
				bFirst = false;
			}
		}
		if (bFirst)
		{
			GetWorldTimerManager().SetTimer(PadTestTimer, this, &AIAJumpPad::PadTestStep, 7.f, true, 10.f);
		}
	}
#endif

	if (GetNetMode() == NM_DedicatedServer
#if !UE_BUILD_SHIPPING
		&& !bPadTest
#endif
		)
	{
		SetActorTickEnabled(false);
		return;
	}

	Phase = FMath::FRand() * 6.28f;

	UMaterialInterface* PadMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAPad.M_IAPad"));
	UMaterialInterface* ColumnMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAPadColumn.M_IAPadColumn"));
	if (PadMaterial)
	{
		DeckMaterial = UMaterialInstanceDynamic::Create(PadMaterial, this);
		DeckMaterial->SetVectorParameterValue(TEXT("PadColor"), PadColor);
		DeckMaterial->SetScalarParameterValue(TEXT("Rim"), 0.f);
		DeckMaterial->SetScalarParameterValue(TEXT("Phase"), Phase);
		Deck->SetMaterial(0, DeckMaterial);

		UMaterialInstanceDynamic* RimMaterial = UMaterialInstanceDynamic::Create(PadMaterial, this);
		RimMaterial->SetVectorParameterValue(TEXT("PadColor"), PadColor);
		RimMaterial->SetScalarParameterValue(TEXT("Rim"), 1.f);
		Base->SetMaterial(0, RimMaterial);
		for (UStaticMeshComponent* Bar : Rim)
		{
			Bar->SetMaterial(0, RimMaterial);
		}
	}
	if (ColumnMat)
	{
		ColumnMaterial = UMaterialInstanceDynamic::Create(ColumnMat, this);
		ColumnMaterial->SetVectorParameterValue(TEXT("PadColor"), PadColor);
		ColumnMaterial->SetScalarParameterValue(TEXT("Phase"), Phase);
		Column->SetMaterial(0, ColumnMaterial);
	}
	else
	{
		Column->SetVisibility(false);
	}
}

void AIAJumpPad::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
#if !UE_BUILD_SHIPPING
	for (int32 I = Watched.Num() - 1; I >= 0; --I)
	{
		ACharacter* Watch = Watched[I].Key.Get();
		const double Age = GetWorld()->GetTimeSeconds() - Watched[I].Value;
		if (!Watch || Age > 3.0)
		{
			Watched.RemoveAtSwap(I);
			continue;
		}
		UE_LOG(LogInstagib, Log, TEXT("PADWATCH %s t=%.2f pos=%s vel=%s %s"), *Watch->GetName(), Age,
			*Watch->GetActorLocation().ToCompactString(), *Watch->GetVelocity().ToCompactString(),
			GetNetMode() == NM_Client ? TEXT("client") : TEXT("server"));
	}
#endif
	if (!DeckMaterial && !ColumnMaterial)
	{
		return;
	}

	// The materials animate themselves from the time node; the code only breathes the light and reports the launch flash.
	Phase += DeltaSeconds * 2.4f;
	const double Now = GetWorld()->GetTimeSeconds();
	const float Pulse = 0.5f + 0.5f * FMath::Sin(Phase);
	const float Flash = Now < FlashUntil ? static_cast<float>((FlashUntil - Now) / 0.4) : 0.f;

	if (Flash > 0.f || bFlashShown)
	{
		if (DeckMaterial)
		{
			DeckMaterial->SetScalarParameterValue(TEXT("Flash"), Flash);
		}
		if (ColumnMaterial)
		{
			ColumnMaterial->SetScalarParameterValue(TEXT("Flash"), Flash);
		}
		bFlashShown = Flash > 0.f;
	}
	Light->SetIntensity(14.f + 8.f * Pulse + 90.f * Flash);
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
	FlashUntil = Now + 0.4;
	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
	{
		Audio->PlayAt(EIASound::JumpPad, GetActorLocation(), 1.f, 0.05f);
	}

	// The server launches everyone it simulates; the controlling client launches its own character at the
	// same moment so that prediction and server agree.
	const bool bLaunch = HasAuthority() || Character->IsLocallyControlled();
	if (bLaunch)
	{
		Character->LaunchCharacter(LaunchVelocity, true, true);
	}
#if !UE_BUILD_SHIPPING
	if (bPadTest)
	{
		UE_LOG(LogInstagib, Log, TEXT("PADLAUNCH %s on %s %s at %s"), *GetName(), *Character->GetName(),
			bLaunch ? TEXT("launched") : TEXT("saw (not launched here)"), *Character->GetActorLocation().ToCompactString());
		Watched.Add(TPair<TWeakObjectPtr<ACharacter>, double>(Character, Now));
	}
#endif
}

#if !UE_BUILD_SHIPPING
void AIAJumpPad::PadTestStep()
{
	for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
	{
		if (APawn* Pawn = It->IsValid() ? It->Get()->GetPawn() : nullptr)
		{
			Pawn->SetActorLocation(GetActorLocation() + FVector(0.f, 0.f, 100.f), false, nullptr, ETeleportType::None);
			UE_LOG(LogInstagib, Log, TEXT("PADTEST dropped %s on %s"), *Pawn->GetName(), *GetName());
		}
	}
}
#endif
