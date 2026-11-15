// Instagib Arena

#include "IAFlagBase.h"
#include "IAFlag.h"
#include "IAGameState.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Net/UnrealNetwork.h"

namespace
{
	TArray<TWeakObjectPtr<AIAFlagBase>> GBases;
}

AIAFlagBase::AIAFlagBase()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.5f;   // only decides whether the pad is shown
	bReplicates = true;
	bAlwaysRelevant = true;
	SetReplicateMovement(false);
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
}

void AIAFlagBase::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIAFlagBase, FlagTeam);
	DOREPLIFETIME(AIAFlagBase, CaptureRadius);
}

AIAFlagBase* AIAFlagBase::Find(const UWorld* World, uint8 Team)
{
	for (const TWeakObjectPtr<AIAFlagBase>& Base : GBases)
	{
		if (AIAFlagBase* B = Base.Get(); B && B->GetWorld() == World && B->FlagTeam == Team)
		{
			return B;
		}
	}
	return nullptr;
}

void AIAFlagBase::BeginPlay()
{
	Super::BeginPlay();
	GBases.AddUnique(this);
	if (GetNetMode() != NM_DedicatedServer)
	{
		BuildVisuals();
	}
	RefreshLook();
}

void AIAFlagBase::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	GBases.Remove(this);
	Super::EndPlay(EndPlayReason);
}

AIAFlag* AIAFlagBase::SpawnFlag()
{
	if (!HasAuthority())
	{
		return nullptr;
	}
	if (AIAFlag* Existing = AIAFlag::Find(GetWorld(), FlagTeam))
	{
		return Existing;
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AIAFlag* Flag = GetWorld()->SpawnActor<AIAFlag>(AIAFlag::StaticClass(), GetFlagHome(), FRotator::ZeroRotator, Params);
	if (Flag)
	{
		Flag->InitFlag(FlagTeam, GetFlagHome());
	}
	return Flag;
}

void AIAFlagBase::OnRep_Base()
{
	RefreshLook();
}

void AIAFlagBase::BuildVisuals()
{
	if (bVisualsBuilt)
	{
		return;
	}
	bVisualsBuilt = true;

	UStaticMesh* PadMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/CTF/SM_IABasePad.SM_IABasePad"), nullptr, LOAD_NoWarn | LOAD_Quiet);
	if (!PadMesh)
	{
		PadMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"), nullptr, LOAD_NoWarn | LOAD_Quiet);
	}
	Pad = NewObject<UStaticMeshComponent>(this, TEXT("Pad"));
	Pad->SetupAttachment(GetRootComponent());
	Pad->SetStaticMesh(PadMesh);
	Pad->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Pad->SetGenerateOverlapEvents(false);
	Pad->SetCanEverAffectNavigation(false);
	Pad->SetCastShadow(false);
	Pad->bReceivesDecals = false;
	Pad->RegisterComponent();
	if (UMaterialInterface* M = Pad->GetMaterial(0))
	{
		PadMaterial = UMaterialInstanceDynamic::Create(M, this);
		Pad->SetMaterial(0, PadMaterial);
	}
}

void AIAFlagBase::RefreshLook()
{
	if (!bVisualsBuilt || !Pad)
	{
		return;
	}
	if (AppliedTeam != FlagTeam && PadMaterial)
	{
		AppliedTeam = FlagTeam;
		PadMaterial->SetVectorParameterValue(TEXT("TeamColor"), AIAFlag::TeamColor(FlagTeam));
	}
	if (AppliedRadius != CaptureRadius)
	{
		AppliedRadius = CaptureRadius;
		// The pad mesh has a radius of 100 cm and a height of 4 cm; the engine cylinder (fallback) is 100 x 100 x 100 cm.
		const bool bOwnMesh = Pad->GetStaticMesh() && Pad->GetStaticMesh()->GetPathName().Contains(TEXT("/Game/CTF/"));
		const float Scale = CaptureRadius / 100.f;
		Pad->SetRelativeScale3D(bOwnMesh ? FVector(Scale, Scale, 1.f) : FVector(Scale * 2.f, Scale * 2.f, 0.03f));
		Pad->SetRelativeLocation(FVector(0.f, 0.f, bOwnMesh ? 1.f : 2.f));
	}
}

void AIAFlagBase::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Only Capture the Flag has bases.
	const AIAGameState* GS = GetWorld() ? GetWorld()->GetGameState<AIAGameState>() : nullptr;
	if (!GS)
	{
		return;
	}
	const int32 Mode = GS->IsCTF() ? 1 : 0;
	if (Mode != ShownMode)
	{
		ShownMode = Mode;
		SetActorHiddenInGame(Mode == 0);
	}
	RefreshLook();
}
