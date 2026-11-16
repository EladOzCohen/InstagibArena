// Instagib Arena

#include "IAFlag.h"
#include "InstagibArena.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Net/UnrealNetwork.h"

namespace
{
	TArray<TWeakObjectPtr<AIAFlag>> GFlags;

	// How the flag sits on a carrier: bone, offset and rotation in the bone's space, scale of the whole flag.
	// (-IAFlagCarry=x,y,z,pitch,yaw,roll,scale changes it for tuning.)
	// The offset is in character space (x forward, z up, from the middle of the capsule); pitch = how far the pole leans back,
	// yaw = how the cloth is turned (90: it streams out behind the carrier). The bone only carries the flag: its own axes do
	// not matter, the relative transform is worked out from the character's orientation when the flag is attached.
	const FName CarryBone(TEXT("spine_03"));
	FVector CarryLocation(-24.f, 0.f, 8.f);
	FRotator CarryRotation(9.f, 90.f, 0.f);
	float CarryScale = 0.5f;
	bool bCarryTuned = false;

	void ReadCarryTuning()
	{
#if !UE_BUILD_SHIPPING
		if (bCarryTuned)
		{
			return;
		}
		bCarryTuned = true;
		FString Text;
		if (FParse::Value(FCommandLine::Get(), TEXT("IAFlagCarry="), Text, /*bShouldStopOnSeparator*/ false))
		{
			TArray<FString> P;
			Text.ParseIntoArray(P, TEXT(","));
			if (P.Num() == 7)
			{
				CarryLocation = FVector(FCString::Atof(*P[0]), FCString::Atof(*P[1]), FCString::Atof(*P[2]));
				CarryRotation = FRotator(FCString::Atof(*P[3]), FCString::Atof(*P[4]), FCString::Atof(*P[5]));
				CarryScale = FCString::Atof(*P[6]);
			}
		}
#endif
	}

	UStaticMesh* LoadMesh(const TCHAR* Path)
	{
		return LoadObject<UStaticMesh>(nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet);
	}
}

AIAFlag::AIAFlag()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	bReplicates = true;
	bAlwaysRelevant = true;
	SetReplicateMovement(false);   // every machine places the flag itself from RestLocation or the carrier
	SetNetUpdateFrequency(10.f);
	SetMinNetUpdateFrequency(2.f);

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	Visual = CreateDefaultSubobject<USceneComponent>(TEXT("Visual"));
	Visual->SetupAttachment(Root);
}

void AIAFlag::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIAFlag, Team);
	DOREPLIFETIME(AIAFlag, State);
	DOREPLIFETIME(AIAFlag, Carrier);
	DOREPLIFETIME(AIAFlag, RestLocation);
	DOREPLIFETIME(AIAFlag, HomeLocation);
	DOREPLIFETIME(AIAFlag, DropEndTime);
}

FLinearColor AIAFlag::TeamColor(uint8 Team)
{
	// The same colours as the players' bodies.
	return Team == 0 ? FLinearColor(1.f, 0.08f, 0.08f) : FLinearColor(0.1f, 0.3f, 1.f);
}

// ---------------------------------------------------------------- registry

AIAFlag* AIAFlag::Find(const UWorld* World, uint8 Team)
{
	for (const TWeakObjectPtr<AIAFlag>& Flag : GFlags)
	{
		if (AIAFlag* F = Flag.Get(); F && F->GetWorld() == World && F->Team == Team)
		{
			return F;
		}
	}
	return nullptr;
}

AIAFlag* AIAFlag::FindCarriedBy(const UWorld* World, const AActor* Pawn)
{
	if (!Pawn)
	{
		return nullptr;
	}
	for (const TWeakObjectPtr<AIAFlag>& Flag : GFlags)
	{
		if (AIAFlag* F = Flag.Get(); F && F->GetWorld() == World && F->State == EIAFlagState::Carried && F->Carrier == Pawn)
		{
			return F;
		}
	}
	return nullptr;
}

// ---------------------------------------------------------------- life cycle

void AIAFlag::BeginPlay()
{
	Super::BeginPlay();
	GFlags.AddUnique(this);
	ReadCarryTuning();
	if (GetNetMode() != NM_DedicatedServer)
	{
		BuildVisuals();
	}
	AppliedTeam = 255;
	ApplyState();
}

void AIAFlag::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	GFlags.Remove(this);
	Super::EndPlay(EndPlayReason);
}

void AIAFlag::BuildVisuals()
{
	if (bVisualsBuilt)
	{
		return;
	}
	bVisualsBuilt = true;

	auto MakePart = [this](const TCHAR* Name) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(this, Name);
		Comp->SetupAttachment(Visual);
		Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Comp->SetGenerateOverlapEvents(false);
		Comp->SetCanEverAffectNavigation(false);
		Comp->SetCastShadow(false);
		Comp->bReceivesDecals = false;
		Comp->RegisterComponent();
		return Comp;
	};

	UStaticMesh* PoleMesh = LoadMesh(TEXT("/Game/CTF/SM_IAFlagPole.SM_IAFlagPole"));
	UStaticMesh* ClothMesh = LoadMesh(TEXT("/Game/CTF/SM_IAFlagCloth.SM_IAFlagCloth"));
	UStaticMesh* BeamMesh = LoadMesh(TEXT("/Game/CTF/SM_IAFlagBeam.SM_IAFlagBeam"));

	Pole = MakePart(TEXT("Pole"));
	Cloth = MakePart(TEXT("Cloth"));
	if (PoleMesh)
	{
		Pole->SetStaticMesh(PoleMesh);
	}
	else if (UStaticMesh* Cylinder = LoadMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder")))
	{
		// Fallback: a thin cylinder (100 cm tall, centred) standing on the ground.
		Pole->SetStaticMesh(Cylinder);
		Pole->SetRelativeScale3D(FVector(0.06f, 0.06f, 2.5f));
		Pole->SetRelativeLocation(FVector(0.f, 0.f, 125.f));
	}
	if (ClothMesh)
	{
		Cloth->SetStaticMesh(ClothMesh);
	}
	else if (UStaticMesh* Plane = LoadMesh(TEXT("/Engine/BasicShapes/Plane.Plane")))
	{
		Cloth->SetStaticMesh(Plane);
		Cloth->SetRelativeScale3D(FVector(0.7f, 1.1f, 1.f));
		Cloth->SetRelativeRotation(FRotator(0.f, 0.f, 90.f));
		Cloth->SetRelativeLocation(FVector(0.f, 55.f, 205.f));
	}
	if (BeamMesh)
	{
		Beam = MakePart(TEXT("Beam"));
		Beam->SetStaticMesh(BeamMesh);
		Beam->bReceivesDecals = false;
		Beam->SetCastShadow(false);
	}
	Pole->SetCastShadow(PoleMesh != nullptr);

	// Materials: the cloth and the beam get their team colour through dynamic instances.
	if (UMaterialInterface* M = Cloth->GetMaterial(0))
	{
		ClothMaterial = UMaterialInstanceDynamic::Create(M, this);
		Cloth->SetMaterial(0, ClothMaterial);
	}
	if (Beam)
	{
		if (UMaterialInterface* M = Beam->GetMaterial(0))
		{
			BeamMaterial = UMaterialInstanceDynamic::Create(M, this);
			Beam->SetMaterial(0, BeamMaterial);
		}
	}

	Light = NewObject<UPointLightComponent>(this, TEXT("FlagLight"));
	Light->SetupAttachment(Visual);
	Light->SetRelativeLocation(FVector(0.f, 40.f, 200.f));
	Light->SetMobility(EComponentMobility::Movable);
	Light->SetCastShadows(false);
	Light->SetIntensityUnits(ELightUnits::Candelas);
	Light->SetIntensity(40.f);
	Light->SetAttenuationRadius(420.f);
	Light->SetSourceRadius(0.f);
	Light->SetSpecularScale(0.2f);
	Light->RegisterComponent();
}

float AIAFlag::GetDropSecondsLeft() const
{
	if (State != EIAFlagState::Dropped)
	{
		return 0.f;
	}
	const AGameStateBase* GS = GetWorld() ? GetWorld()->GetGameState() : nullptr;
	return GS ? FMath::Max(0.f, DropEndTime - GS->GetServerWorldTimeSeconds()) : 0.f;
}

float AIAFlag::GetCarriedSeconds() const
{
	return State == EIAFlagState::Carried ? static_cast<float>(FPlatformTime::Seconds() - CarriedSince) : 0.f;
}

// ---------------------------------------------------------------- server operations

void AIAFlag::InitFlag(uint8 InTeam, const FVector& InHome)
{
	Team = InTeam;
	HomeLocation = InHome;
	ServerReturnHome();
}

void AIAFlag::ServerPickUp(ACharacter* NewCarrier)
{
	if (!HasAuthority() || !NewCarrier)
	{
		return;
	}
	State = EIAFlagState::Carried;
	Carrier = NewCarrier;
	SetOwner(NewCarrier);
	DropEndTime = 0.f;
	LastCarrierLocation = NewCarrier->GetActorLocation();
	CarriedSince = FPlatformTime::Seconds();
	ApplyState();
	ForceNetUpdate();
}

bool AIAFlag::ServerDrop(const FVector& Where, float ReturnDelaySeconds)
{
	if (!HasAuthority())
	{
		return false;
	}

	// The flag falls to the floor under the carrier. No floor, or a floor below the kill height: it goes home at once.
	UWorld* World = GetWorld();
	const float KillZ = World && World->GetWorldSettings() ? World->GetWorldSettings()->KillZ : -100000.f;
	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(FlagDrop), false, this);
	if (Carrier)
	{
		Params.AddIgnoredActor(Carrier);
	}
	const FVector Start = Where + FVector(0.f, 0.f, 60.f);
	const bool bFloor = World && World->LineTraceSingleByChannel(Hit, Start, Start - FVector(0.f, 0.f, 8000.f), ECC_Visibility, Params);
	if (!bFloor || Hit.ImpactPoint.Z < KillZ + 150.f || Where.Z < KillZ + 100.f)
	{
		UE_LOG(LogInstagib, Log, TEXT("CTF: the %s flag was dropped over nothing (z %.0f, kill z %.0f): back home"), Team == 0 ? TEXT("red") : TEXT("blue"), Where.Z, KillZ);
		ServerReturnHome();
		return false;
	}

	const float StartZ = Where.Z;
	State = EIAFlagState::Dropped;
	Carrier = nullptr;
	SetOwner(nullptr);
	RestLocation = Hit.ImpactPoint + FVector(0.f, 0.f, 1.f);
	const AGameStateBase* GS = World->GetGameState();
	DropEndTime = (GS ? GS->GetServerWorldTimeSeconds() : World->GetTimeSeconds()) + ReturnDelaySeconds;
	ApplyState();
	FallOffset = FMath::Clamp(StartZ - RestLocation.Z, 0.f, 600.f);
	FallVelocity = 0.f;
	ForceNetUpdate();
	return true;
}

void AIAFlag::ServerReturnHome()
{
	if (!HasAuthority())
	{
		return;
	}
	State = EIAFlagState::Home;
	Carrier = nullptr;
	SetOwner(nullptr);
	RestLocation = HomeLocation;
	DropEndTime = 0.f;
	ApplyState();
	ForceNetUpdate();
}

// ---------------------------------------------------------------- placement (every machine)

void AIAFlag::OnRep_Flag()
{
	ApplyState();
}

void AIAFlag::ApplyState()
{
	USceneComponent* Root = GetRootComponent();
	if (!Root)
	{
		return;
	}

	if (ClothMaterial && AppliedTeam != Team)
	{
		AppliedTeam = Team;
		const FLinearColor Color = TeamColor(Team);
		ClothMaterial->SetVectorParameterValue(TEXT("TeamColor"), Color);
		if (BeamMaterial)
		{
			BeamMaterial->SetVectorParameterValue(TEXT("TeamColor"), Color);
		}
		if (Light)
		{
			Light->SetLightColor(FLinearColor(FMath::Lerp(Color.R, 1.f, 0.15f), FMath::Lerp(Color.G, 1.f, 0.15f), FMath::Lerp(Color.B, 1.f, 0.15f)));
		}
	}

	if (State == EIAFlagState::Carried)
	{
		USkeletalMeshComponent* Mesh = Carrier ? Carrier->GetMesh() : nullptr;
		// The bone exists once the carrier's look has been applied on this machine; until then Tick asks again.
		if (Mesh && Mesh->GetSkeletalMeshAsset() && Mesh->DoesSocketExist(CarryBone))
		{
			if (Root->GetAttachParent() != Mesh)
			{
				// Where the flag should be in the world (behind the back, upright, leaning back a little) ...
				const FQuat ActorQuat = FRotator(0.f, Carrier->GetActorRotation().Yaw, 0.f).Quaternion();
				const FQuat DesiredQuat = ActorQuat * FRotator(CarryRotation.Pitch, 0.f, 0.f).Quaternion() * FRotator(0.f, CarryRotation.Yaw, 0.f).Quaternion();
				const FVector DesiredLocation = Carrier->GetActorLocation() + ActorQuat.RotateVector(CarryLocation);
				// ... and the same place expressed in the bone's space, so that it follows the back from now on.
				const FTransform BoneWorld = Mesh->GetSocketTransform(CarryBone, RTS_World);
				AttachToComponent(Mesh, FAttachmentTransformRules::KeepRelativeTransform, CarryBone);
				Root->SetRelativeLocationAndRotation(BoneWorld.InverseTransformPositionNoScale(DesiredLocation),
					(BoneWorld.GetRotation().Inverse() * DesiredQuat).Rotator());
			}
			bAttachedToCarrier = true;
			Visual->SetRelativeLocation(FVector::ZeroVector);
			Visual->SetRelativeRotation(FRotator::ZeroRotator);
			Visual->SetRelativeScale3D(FVector(CarryScale));
			FallOffset = 0.f;
		}
		else
		{
			bAttachedToCarrier = false;   // the carrier has not arrived on this machine yet: Tick tries again
		}
	}
	else
	{
		if (Root->GetAttachParent())
		{
			// Left the carrier (it died, or the flag went home): remember how high it was for the fall animation.
			const float FromZ = GetActorLocation().Z;
			DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
			if (State == EIAFlagState::Dropped && !HasAuthority())
			{
				FallOffset = FMath::Clamp(FromZ - RestLocation.Z, 0.f, 600.f);
				FallVelocity = 0.f;
			}
		}
		bAttachedToCarrier = false;
		SetActorLocationAndRotation(RestLocation, FRotator(0.f, Team == 0 ? 90.f : -90.f, 0.f));
		Visual->SetRelativeScale3D(FVector::OneVector);
		if (State != EIAFlagState::Dropped)
		{
			FallOffset = 0.f;
		}
	}
	AppliedState = State;
}

void AIAFlag::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	LookClock += DeltaSeconds;

	if (HasAuthority() && State == EIAFlagState::Carried && Carrier)
	{
		LastCarrierLocation = Carrier->GetActorLocation();
	}

	// A carrier that was not there yet when the state arrived.
	if (State == EIAFlagState::Carried && !bAttachedToCarrier)
	{
		ApplyState();
	}

	if (GetNetMode() != NM_DedicatedServer && bVisualsBuilt)
	{
		UpdateLook(DeltaSeconds);
	}
}

void AIAFlag::UpdateLook(float DeltaSeconds)
{
	// The player who carries the flag does not see it behind his own head.
	bool bHide = false;
	if (State == EIAFlagState::Carried && Carrier && Carrier->IsLocallyControlled())
	{
		const APlayerController* PC = Cast<APlayerController>(Carrier->GetController());
		bHide = PC && PC->GetViewTarget() == Carrier;   // only while the camera is in his own head
	}
	if (bHide != bHiddenForCarrier)
	{
		bHiddenForCarrier = bHide;
		Visual->SetVisibility(!bHide, true);
	}

	// Dropped: falls with a bounce and leans over.
	if (State == EIAFlagState::Dropped)
	{
		if (FallOffset > 0.f || FMath::Abs(FallVelocity) > 1.f)
		{
			FallVelocity -= 1400.f * DeltaSeconds;
			FallOffset += FallVelocity * DeltaSeconds;
			if (FallOffset <= 0.f)
			{
				FallOffset = 0.f;
				FallVelocity = FMath::Abs(FallVelocity) > 120.f ? -FallVelocity * 0.28f : 0.f;
			}
		}
		Visual->SetRelativeLocation(FVector(0.f, 0.f, FallOffset));
		Visual->SetRelativeRotation(FRotator(0.f, 0.f, 14.f));
	}
	else if (State == EIAFlagState::Home)
	{
		Visual->SetRelativeLocation(FVector::ZeroVector);
		Visual->SetRelativeRotation(FRotator::ZeroRotator);
	}

	// Material: the cloth waves more when it moves; the beam breathes (and flickers in the last seconds of a dropped flag).
	if (ClothMaterial)
	{
		ClothMaterial->SetScalarParameterValue(TEXT("WaveStrength"), State == EIAFlagState::Carried ? 1.6f : (State == EIAFlagState::Dropped ? 0.5f : 1.f));
	}
	if (BeamMaterial)
	{
		float Intensity = 0.8f + 0.2f * FMath::Sin(LookClock * 2.f);
		if (State == EIAFlagState::Dropped)
		{
			const float Left = GetDropSecondsLeft();
			Intensity = Left < 5.f ? (FMath::Fmod(LookClock, 0.4f) < 0.2f ? 1.2f : 0.3f) : 1.f;
		}
		else if (State == EIAFlagState::Carried)
		{
			Intensity = 0.9f;
		}
		BeamMaterial->SetScalarParameterValue(TEXT("Intensity"), Intensity);
	}
	if (Beam)
	{
		// Carried: the beam is shorter (it rides on the player).
		Beam->SetRelativeScale3D(State == EIAFlagState::Carried ? FVector(1.f, 1.f, 0.67f) : FVector::OneVector);
	}
}
