// Instagib Arena

#include "IAPlayerCharacter.h"
#include "IAPlayerController.h"
#include "IAPlayerState.h"
#include "IAGameState.h"
#include "IAGameMode.h"
#include "IAAudioSubsystem.h"
#include "IACharacterRoster.h"
#include "IABeam.h"
#include "IASettings.h"
#include "IAImpactEffect.h"
#include "IAAnimInstance.h"
#include "IAScorch.h"
#include "Engine/DamageEvents.h"
#include "IAHUD.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "InstagibArena.h"
#include "Animation/AnimInstance.h"
#include "AnimationRuntime.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "InputActionValue.h"
#include "DrawDebugHelpers.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/DamageType.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AIAPlayerCharacter::AIAPlayerCharacter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer.SetDefaultSubobjectClass<UIACharacterMovement>(ACharacter::CharacterMovementComponentName))
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(34.f, 92.f);
	BaseEyeHeight = 64.f;
	CrouchedEyeHeight = 34.f; // from the capsule center, which is lower while crouching

	// The body turns with the view, like in a classic arena shooter.
	bUseControllerRotationYaw = true;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;

	JumpMaxCount = 2; // double jump

	FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
	FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
	FirstPersonCamera->SetRelativeLocation(FVector(0.f, 0.f, BaseEyeHeight));
	FirstPersonCamera->bUsePawnControlRotation = true;

	// Placeholder body from engine shapes. Real characters replace this later.
	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	BodyMesh->SetupAttachment(GetCapsuleComponent());
	BodyMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	BodyMesh->SetOwnerNoSee(true);
	BodyMesh->SetRelativeScale3D(FVector(0.68f, 0.68f, 1.84f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CylinderFinder.Succeeded())
	{
		BodyMesh->SetStaticMesh(CylinderFinder.Object);
	}

	// The skeletal mesh stays hidden until a character look is applied (see ApplyLook).
	// Its offset is set here because ACharacter remembers it as the base for network smoothing.
	GetMesh()->SetRelativeLocationAndRotation(FVector(0.f, 0.f, -92.f), FRotator(0.f, -90.f, 0.f));
	GetMesh()->SetVisibility(false);
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AIAPlayerCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIAPlayerCharacter, bDead);
	DOREPLIFETIME(AIAPlayerCharacter, DeathShotDir);
	DOREPLIFETIME(AIAPlayerCharacter, DeathHitLocation);
}

void AIAPlayerCharacter::BeginPlay()
{
	Super::BeginPlay();

	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
	{
		Audio->PlayAt(EIASound::Spawn, GetActorLocation(), 0.6f);
	}
}

void AIAPlayerCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	UpdateBodyColor();
	UpdateLook();
	UpdateMovementAudio(DeltaSeconds);
	UpdateWeaponView(DeltaSeconds);
	UpdateCamera(DeltaSeconds);
	UpdateDeath(DeltaSeconds);
}

void AIAPlayerCharacter::UpdateDeath(float DeltaSeconds)
{
	if (!bDead)
	{
		return;
	}
	DeathAge += DeltaSeconds;

	// The body lies there for a moment, then bursts into sparks of its color and is gone.
	if (!bDeathBurstDone && DeathAge > 3.6f)
	{
		bDeathBurstDone = true;
		if (GetNetMode() != NM_DedicatedServer && GetWorld())
		{
			FVector Where = GetMesh() ? GetMesh()->GetBoneLocation(TEXT("pelvis")) : GetActorLocation();
			if (AIAImpactEffect* Burst = GetWorld()->SpawnActor<AIAImpactEffect>(Where, FRotator::ZeroRotator))
			{
				Burst->Init(FVector::UpVector, GetBodyColor(), 1.2f, 22);
			}
		}
		SetActorHiddenInGame(true);
		if (GetMesh())
		{
			GetMesh()->SetSimulatePhysics(false);
			GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		}
	}
}

float AIAPlayerCharacter::GetAimPitchForAnimation() const
{
	if (DevAimPitch > -900.f)
	{
		return DevAimPitch;
	}
	// The controller knows the view of the local player and of bots; other machines get it through RemoteViewPitch.
	return FRotator::NormalizeAxis(GetBaseAimRotation().Pitch);
}

// ---------------------------------------------------------------- camera feel

void AIAPlayerCharacter::UpdateCamera(float DeltaSeconds)
{
	if (!IsLocalHuman() || !FirstPersonCamera || DeltaSeconds <= 0.f)
	{
		return;
	}
	const float Dt = FMath::Min(DeltaSeconds, 0.1f);

	// Settings are read twice a second, not every frame.
	CamSettingsTimer -= Dt;
	if (CamSettingsTimer <= 0.f)
	{
		CamSettingsTimer = 0.5f;
		bCamReduced = IASettings::IsReducedMotion();
		bCamBob = IASettings::IsCameraBobEnabled() && !bCamReduced;
		bCamRoll = IASettings::IsViewRollEnabled() && !bCamReduced;
	}

	UIACharacterMovement* Move = Cast<UIACharacterMovement>(GetCharacterMovement());
	if (!Move || bDead)
	{
		FirstPersonCamera->ClearAdditiveOffset();
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();
	const FVector Velocity = GetVelocity();
	const float Speed2D = Velocity.Size2D();
	const bool bGrounded = Move->IsMovingOnGround();
	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

	// Pause menu open: let go of crouch and walk, the key release may not arrive.
	if (IsPauseMenuOpen())
	{
		Move->SetWantsToWalk(false);
		UnCrouch();
	}

	// ---- eye height: crouching and stair steps are smoothed, not snapped.
	const float EyeZ = GetActorLocation().Z + BaseEyeHeight;
	if (bCamHavePrev)
	{
		const float Jump = EyeZ - CamPrevEyeZ - Velocity.Z * Dt;
		const bool bCapsuleChanged = !FMath::IsNearlyEqual(HalfHeight, CamPrevHalfHeight, 0.1f);
		const bool bStep = bGrounded && bCamPrevGrounded && FMath::Abs(Jump) > 2.5f && FMath::Abs(Jump) < 60.f
			&& Move->CurrentFloor.HitResult.ImpactNormal.Z > 0.98f;
		if (bCapsuleChanged || bStep)
		{
			CamEyeOffset = FMath::Clamp(CamEyeOffset - Jump, -70.f, 70.f);
		}
	}
	CamPrevEyeZ = EyeZ;
	CamPrevHalfHeight = HalfHeight;
	bCamPrevGrounded = bGrounded;
	bCamHavePrev = true;
	CamEyeOffset = bCamReduced ? 0.f : FMath::FInterpTo(CamEyeOffset, 0.f, Dt, 11.f);

	// ---- head bob: once per step, scaled by speed, quieter when crouched or walking slowly.
	const float BobTarget = (bCamBob && bGrounded) ? FMath::Clamp(Speed2D / 600.f, 0.f, 1.f) : 0.f;
	CamBobAlpha = FMath::FInterpTo(CamBobAlpha, BobTarget, Dt, 8.f);
	CamBobPhase += Speed2D * Dt / 270.f * PI; // one step per 270 units, like the footsteps
	const float StanceScale = bIsCrouched ? 0.5f : 1.f;
	const float BobZ = FMath::Sin(CamBobPhase * 2.f) * 0.9f * CamBobAlpha * StanceScale;
	const float BobRoll = FMath::Sin(CamBobPhase) * 0.3f * CamBobAlpha * StanceScale;

	// ---- landing dip: a damped spring pushed down by the impact.
	if (Move->LastLandingTime > CamSeenLandingTime)
	{
		CamSeenLandingTime = Move->LastLandingTime;
		if (!bCamReduced && Move->LastLandingSpeed > 350.f)
		{
			CamDipVelocity -= FMath::Min(Move->LastLandingSpeed, 1500.f) * 0.1f;
		}
	}
	{
		constexpr float Stiffness = 320.f;
		const float Damping = 2.f * FMath::Sqrt(Stiffness) * 0.6f;
		CamDipVelocity += (-Stiffness * CamDip - Damping * CamDipVelocity) * Dt;
		CamDip += CamDipVelocity * Dt;
		CamDip = FMath::Clamp(CamDip, -9.f, 4.f);
		if (bCamReduced)
		{
			CamDip = 0.f;
			CamDipVelocity = 0.f;
		}
	}

	// ---- dodge: a roll to the side and a short field of view kick.
	if (Move->DodgeCounter != CamSeenDodgeCount)
	{
		CamSeenDodgeCount = Move->DodgeCounter;
		// Replayed moves after a correction count again; ignore those.
		if (Now - CamLastKickTime > 0.3f)
		{
			CamLastKickTime = Now;
			CamKick = 1.f;
			CamKickRoll = Move->LastDodgeDir == EIADodgeDir::Left ? -1.f : (Move->LastDodgeDir == EIADodgeDir::Right ? 1.f : 0.f);
		}
	}
	CamKick = FMath::Max(0.f, CamKick - Dt * 3.f);
	const float Kick = bCamReduced ? 0.f : CamKick * CamKick;

	// ---- strafing roll: lean a little into the direction of the sideways speed.
	const float SideSpeed = FVector::DotProduct(Velocity, GetActorRightVector());
	const float RollTarget = bCamRoll ? FMath::Clamp(SideSpeed / 600.f, -1.f, 1.f) * 1.4f : 0.f;
	CamRoll = FMath::FInterpTo(CamRoll, RollTarget, Dt, 9.f);

	const float Roll = CamRoll + (bCamRoll ? CamKickRoll * 4.f * Kick : 0.f) + BobRoll;
	const float Punch = bCamReduced ? 0.f : 0.7f * Recoil * Recoil; // fire kick, display only

	FirstPersonCamera->SetRelativeLocation(FVector(0.f, 0.f, BaseEyeHeight + CamEyeOffset + BobZ + CamDip));
	FirstPersonCamera->AddAdditiveOffset(FTransform(FRotator(Punch, 0.f, Roll)), 6.f * Kick);
}

// ---------------------------------------------------------------- movement sounds

void AIAPlayerCharacter::UpdateMovementAudio(float DeltaSeconds)
{
	if (DeltaSeconds <= 0.f || GetNetMode() == NM_DedicatedServer)
	{
		return;
	}

	const FVector Velocity = GetVelocity();
	const float Speed2D = Velocity.Size2D();
	const bool bGrounded = GetCharacterMovement()->IsMovingOnGround();

	if (!bDead)
	{
		if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
		{
			// Your own movement is quieter than other players'.
			const float Scale = IsLocalHuman() ? 0.45f : 1.f;
			const FVector Feet = GetActorLocation() - FVector(0.f, 0.f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());

			// A sudden speed gain means a dodge, a sudden upward gain means a jump.
			const float SpeedGain = Speed2D - PrevSpeed2D;
			const float UpGain = Velocity.Z - PrevVelocityZ;
			if (SpeedGain > 300.f)
			{
				Audio->PlayAt(EIASound::Dodge, GetActorLocation(), 0.8f * Scale, 0.05f);
			}
			else if (UpGain > 300.f)
			{
				Audio->PlayAt(bWasGrounded ? EIASound::Jump : EIASound::DoubleJump, Feet, 0.7f * Scale, 0.04f);
			}

			// Footsteps: one per stretch of ground covered.
			constexpr float StepLength = 270.f;
			if (bGrounded && Speed2D > 150.f)
			{
				StepDistance += Speed2D * DeltaSeconds;
				if (StepDistance >= StepLength)
				{
					StepDistance = 0.f;
					Audio->PlayAt(EIASound::Footstep, Feet, 0.7f * Scale, 0.08f);
				}
			}
			else
			{
				StepDistance = StepLength * 0.6f; // first step comes quickly after starting to move
			}
		}
	}

	PrevSpeed2D = Speed2D;
	PrevVelocityZ = Velocity.Z;
	bWasGrounded = bGrounded;
}

void AIAPlayerCharacter::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);

	if (!bDead && PrevVelocityZ < -450.f && GetNetMode() != NM_DedicatedServer)
	{
		if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
		{
			const float Scale = IsLocalHuman() ? 0.5f : 1.f;
			const float Loudness = FMath::Clamp(FMath::Abs(PrevVelocityZ) / 1200.f, 0.4f, 1.f);
			Audio->PlayAt(EIASound::Land, Hit.ImpactPoint, Loudness * Scale, 0.05f);
		}
	}
}

// ---------------------------------------------------------------- input

void AIAPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	AIAPlayerController* PC = Cast<AIAPlayerController>(GetController());
	if (!Input || !PC)
	{
		UE_LOG(LogInstagib, Warning, TEXT("%s: no enhanced input or wrong controller class"), *GetNameSafe(this));
		return;
	}

	Input->BindAction(PC->MoveAction, ETriggerEvent::Triggered, this, &AIAPlayerCharacter::Move);
	Input->BindAction(PC->LookAction, ETriggerEvent::Triggered, this, &AIAPlayerCharacter::Look);
	Input->BindAction(PC->JumpAction, ETriggerEvent::Started, this, &AIAPlayerCharacter::JumpPressed);
	Input->BindAction(PC->JumpAction, ETriggerEvent::Completed, this, &AIAPlayerCharacter::JumpReleased);
	Input->BindAction(PC->FireAction, ETriggerEvent::Started, this, &AIAPlayerCharacter::FirePressed);
	Input->BindAction(PC->CrouchAction, ETriggerEvent::Started, this, &AIAPlayerCharacter::CrouchPressed);
	Input->BindAction(PC->CrouchAction, ETriggerEvent::Completed, this, &AIAPlayerCharacter::CrouchReleased);
	Input->BindAction(PC->WalkAction, ETriggerEvent::Started, this, &AIAPlayerCharacter::WalkPressed);
	Input->BindAction(PC->WalkAction, ETriggerEvent::Completed, this, &AIAPlayerCharacter::WalkReleased);
	Input->BindAction(PC->DodgeForwardAction, ETriggerEvent::Started, this, &AIAPlayerCharacter::DodgeForwardTap);
	Input->BindAction(PC->DodgeBackAction, ETriggerEvent::Started, this, &AIAPlayerCharacter::DodgeBackTap);
	Input->BindAction(PC->DodgeLeftAction, ETriggerEvent::Started, this, &AIAPlayerCharacter::DodgeLeftTap);
	Input->BindAction(PC->DodgeRightAction, ETriggerEvent::Started, this, &AIAPlayerCharacter::DodgeRightTap);
}

void AIAPlayerCharacter::Move(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	AddMovementInput(GetActorForwardVector(), Axis.Y);
	AddMovementInput(GetActorRightVector(), Axis.X);
}

void AIAPlayerCharacter::Look(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	const float Sensitivity = IASettings::GetMouseSensitivity();
	AddControllerYawInput(Axis.X * Sensitivity);
	AddControllerPitchInput(Axis.Y * Sensitivity);
}

bool AIAPlayerCharacter::IsPauseMenuOpen() const
{
	const AIAPlayerController* PC = Cast<AIAPlayerController>(GetController());
	return PC && PC->IsMenuOpen();
}

void AIAPlayerCharacter::JumpPressed()
{
	if (!bDead && !IsPauseMenuOpen())
	{
		Jump();
	}
}

void AIAPlayerCharacter::JumpReleased()
{
	StopJumping();
}

void AIAPlayerCharacter::FirePressed()
{
	if (!IsPauseMenuOpen())
	{
		TryFire();
	}
}

void AIAPlayerCharacter::CrouchPressed()
{
	if (!bDead && !IsPauseMenuOpen())
	{
		Crouch();
	}
}

void AIAPlayerCharacter::CrouchReleased()
{
	UnCrouch();
}

void AIAPlayerCharacter::WalkPressed()
{
	if (!bDead && !IsPauseMenuOpen())
	{
		if (UIACharacterMovement* Move = Cast<UIACharacterMovement>(GetCharacterMovement()))
		{
			Move->SetWantsToWalk(true);
		}
	}
}

void AIAPlayerCharacter::WalkReleased()
{
	if (UIACharacterMovement* Move = Cast<UIACharacterMovement>(GetCharacterMovement()))
	{
		Move->SetWantsToWalk(false);
	}
}

void AIAPlayerCharacter::RegisterTap(int32 DirIndex)
{
	if (bDead || IsPauseMenuOpen())
	{
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();
	if (Now - LastTapTime[DirIndex] <= DoubleTapWindow)
	{
		LastTapTime[DirIndex] = -10.f;
		Dodge(static_cast<EIADodgeDir>(DirIndex));
	}
	else
	{
		LastTapTime[DirIndex] = Now;
	}
}

void AIAPlayerCharacter::Dodge(EIADodgeDir Direction)
{
	if (bDead)
	{
		return;
	}
	if (UIACharacterMovement* Move = Cast<UIACharacterMovement>(GetCharacterMovement()))
	{
		Move->RequestDodge(Direction);
	}
}

// ---------------------------------------------------------------- weapon

void AIAPlayerCharacter::TryFire()
{
	if (bDead)
	{
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();
	if (Now - LastFireTime < FireInterval)
	{
		return;
	}
	LastFireTime = Now;
	Recoil = 1.f; // the rifle kicks back on screen

	ServerFire();
}

void AIAPlayerCharacter::ServerFire_Implementation()
{
	if (bDead)
	{
		return;
	}

	// Server-side rate limit, with a small tolerance for network jitter.
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now - LastFireTime < FireInterval * 0.5f && !IsLocallyControlled())
	{
		return;
	}
	LastFireTime = Now;

	if (const AIAPlayerState* ShooterState = GetPlayerState<AIAPlayerState>())
	{
		if (!ShooterState->bIsBotPlayer)
		{
			UE_LOG(LogInstagib, Verbose, TEXT("Shot fired by %s"), *ShooterState->GetPlayerName());
		}
	}

	FVector Eye;
	FRotator ViewRotation;
	GetActorEyesViewPoint(Eye, ViewRotation);

	const FVector Direction = ViewRotation.Vector();
	const FVector End = Eye + Direction * 30000.f;

	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(InstagibShot), true, this);
	const bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, Eye, End, ECC_Pawn, Params);
	const FVector ImpactPoint = bHit ? Hit.ImpactPoint : End;

	if (bHit && Hit.GetActor())
	{
		const float Dealt = UGameplayStatics::ApplyPointDamage(Hit.GetActor(), ShotDamage, Direction, Hit, GetController(), this, UDamageType::StaticClass());
		if (const AIAPlayerCharacter* Victim = Cast<AIAPlayerCharacter>(Hit.GetActor()))
		{
			if (Dealt > 0.f)
			{
				ClientHitConfirm(Victim->IsDead());
			}
		}
	}

	// HitType: 0 = nothing hit, 1 = the world, 2 = a player.
	const uint8 HitType = !bHit ? 0 : (Cast<AIAPlayerCharacter>(Hit.GetActor()) ? 2 : 1);
	const FVector Normal = bHit ? FVector(Hit.ImpactNormal) : -Direction;

	const FVector Muzzle = Eye + ViewRotation.RotateVector(FVector(40.f, 14.f, -12.f));
	MulticastShotEffect(Muzzle, ImpactPoint, Normal, HitType);
}

void AIAPlayerCharacter::MulticastShotEffect_Implementation(FVector Start, FVector End, FVector Normal, uint8 HitType)
{
	// Sparks and a flash where the shot landed.
	if (HitType != 0 && GetNetMode() != NM_DedicatedServer && GetWorld())
	{
		if (AIAImpactEffect* Impact = GetWorld()->SpawnActor<AIAImpactEffect>(End + Normal * 3.f, FRotator::ZeroRotator))
		{
			Impact->Init(Normal, GetBodyColor(), HitType == 2 ? 1.4f : 1.f, HitType == 2 ? 24 : 12);
		}
		// A shot that hits the level leaves a scorch mark.
		if (HitType == 1)
		{
			if (UIAScorchSubsystem* Scorch = UIAScorchSubsystem::Get(this))
			{
				Scorch->AddMark(End + Normal * 0.5f, Normal, GetBodyColor());
			}
		}
	}

	// The visible trail starts at the barrel of the rifle that is on screen.
	if (GetNetMode() != NM_DedicatedServer && GetWorld())
	{
		if (AIABeam* Beam = GetWorld()->SpawnActor<AIABeam>(GetMuzzleLocation(Start), FRotator::ZeroRotator))
		{
			Beam->Init(GetMuzzleLocation(Start), End, GetBodyColor());
		}
	}

	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
	{
		// Your own shots are flat and clear, other players' shots come from where they stand.
		if (IsLocalHuman())
		{
			Audio->Play2D(EIASound::InstagibFire, 0.9f);
		}
		else
		{
			Audio->PlayAt(EIASound::InstagibFire, Start, 1.f, 0.04f);
		}
	}
}

void AIAPlayerCharacter::ClientHitConfirm_Implementation(bool bKilled)
{
	// Bots also run this on the server, only a human's machine should play it.
	if (!IsLocalHuman())
	{
		return;
	}
	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
	{
		Audio->Play2D(bKilled ? EIASound::KillConfirm : EIASound::HitConfirm, 0.9f);
	}
	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (AIAHUD* Hud = Cast<AIAHUD>(PC->GetHUD()))
		{
			Hud->ShowHitMarker(bKilled);
		}
	}
}

// ---------------------------------------------------------------- damage and death

float AIAPlayerCharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (bDead || !HasAuthority() || DamageAmount <= 0.f)
	{
		return 0.f;
	}

	// No friendly fire in team games. Self damage is allowed.
	if (const AIAGameState* GS = GetWorld()->GetGameState<AIAGameState>())
	{
		if (GS->IsTeamGame() && EventInstigator && EventInstigator != GetController())
		{
			const AIAPlayerState* KillerState = EventInstigator->GetPlayerState<AIAPlayerState>();
			const AIAPlayerState* MyState = GetPlayerState<AIAPlayerState>();
			if (KillerState && MyState && KillerState->Team == MyState->Team)
			{
				return 0.f;
			}
		}
	}

	// Remember where the shot came from, the ragdoll is pushed that way.
	DeathHitLocation = GetActorLocation();
	DeathShotDir = FVector::ZeroVector;
	if (DamageEvent.IsOfType(FPointDamageEvent::ClassID))
	{
		const FPointDamageEvent& Point = static_cast<const FPointDamageEvent&>(DamageEvent);
		DeathHitLocation = Point.HitInfo.ImpactPoint;
		DeathShotDir = Point.ShotDirection.GetSafeNormal();
	}

	Die(EventInstigator);
	return DamageAmount;
}

void AIAPlayerCharacter::Die(AController* Killer)
{
	if (bDead)
	{
		return;
	}

	bDead = true;
	OnRep_Dead();

	AController* VictimController = GetController();
	if (AIAGameMode* GameMode = GetWorld()->GetAuthGameMode<AIAGameMode>())
	{
		GameMode->OnPlayerKilled(Killer, VictimController);
	}

	DetachFromControllerPendingDestroy();
	SetLifeSpan(4.2f); // the body is removed (with sparks) at 3.6 s, see UpdateDeath
}

void AIAPlayerCharacter::FellOutOfWorld(const UDamageType& DamageType)
{
	// Falling below the map's kill height counts as a suicide, then the normal respawn applies.
	if (HasAuthority() && !bDead)
	{
		Die(nullptr);
	}
}

void AIAPlayerCharacter::OnRep_Dead()
{
	if (bDead)
	{
		GetCharacterMovement()->DisableMovement();
		GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		BodyMesh->SetVisibility(false);

		if (FPWeaponRoot)
		{
			FPWeaponRoot->SetVisibility(false, true);
		}

		// Real characters collapse as a ragdoll; their accessories ride along on the bones.
		// The body starts from the pose it had, and is pushed by the shot that killed it.
		if (GetMesh() && GetMesh()->GetSkeletalMeshAsset() && AppliedLookKey != INT32_MIN && GetNetMode() != NM_DedicatedServer)
		{
			USkeletalMeshComponent* Skel = GetMesh();
			// Bodies collide with the level only: shots and players pass through, nothing jitters against the capsule.
			Skel->SetCollisionObjectType(ECC_PhysicsBody);
			Skel->SetCollisionResponseToAllChannels(ECR_Ignore);
			Skel->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
			Skel->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Block);
			Skel->SetCollisionEnabled(ECollisionEnabled::PhysicsOnly);
			Skel->SetAllBodiesSimulatePhysics(true);
			Skel->SetSimulatePhysics(true);
			Skel->SetAllUseCCD(true);           // fast bodies do not tunnel through floors
			Skel->SetLinearDamping(0.6f);
			Skel->SetAngularDamping(2.0f);
			Skel->WakeAllRigidBodies();

			const FVector Dir = DeathShotDir.IsNearlyZero() ? FVector::ZeroVector : FVector(DeathShotDir);
			if (!Dir.IsZero())
			{
				const FName Bone = Skel->FindClosestBone(DeathHitLocation);
				Skel->AddImpulse(Dir * 520.f + FVector(0.f, 0.f, 160.f), Bone, /*bVelChange*/ true);
				Skel->AddImpulse(Dir * 140.f, NAME_None, /*bVelChange*/ true);
			}
			else
			{
				// A fall or a suicide: the body just drops.
				Skel->AddImpulse(FVector(0.f, 0.f, 60.f), NAME_None, /*bVelChange*/ true);
			}
		}

		if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
		{
			Audio->PlayAt(EIASound::Death, GetActorLocation(), 1.f, 0.06f);
		}

		// The character bursts into sparks of its own color.
		if (GetNetMode() != NM_DedicatedServer && GetWorld())
		{
			if (AIAImpactEffect* Burst = GetWorld()->SpawnActor<AIAImpactEffect>(GetActorLocation() + FVector(0.f, 0.f, 20.f), FRotator::ZeroRotator))
			{
				Burst->Init(FVector::UpVector, GetBodyColor(), 2.2f, 44);
			}
		}
	}
}

// ---------------------------------------------------------------- look

FLinearColor AIAPlayerCharacter::GetBodyColor() const
{
	if (const AIAPlayerState* PS = GetPlayerState<AIAPlayerState>())
	{
		if (PS->Team == 0)
		{
			return FLinearColor(1.f, 0.08f, 0.08f);
		}
		if (PS->Team == 1)
		{
			return FLinearColor(0.1f, 0.3f, 1.f);
		}
		// Free for all: shots take the accent color of the character.
		return IACharacters::GetLook(PS->CharacterIndex).Accent;
	}
	return FLinearColor::White;
}

void AIAPlayerCharacter::UpdateBodyColor()
{
	const AIAPlayerState* PS = GetPlayerState<AIAPlayerState>();
	if (!PS)
	{
		return;
	}
	if (PS->Team == ColoredTeam && PS->GetPlayerId() == ColoredId)
	{
		return;
	}
	ColoredTeam = PS->Team;
	ColoredId = PS->GetPlayerId();

	if (!BodyMaterial && BodyMesh->GetStaticMesh())
	{
		UMaterialInterface* Base = BodyMesh->GetMaterial(0);
		if (Base)
		{
			BodyMaterial = BodyMesh->CreateDynamicMaterialInstance(0, Base);
		}
	}
	if (BodyMaterial)
	{
		BodyMaterial->SetVectorParameterValue(TEXT("Color"), GetBodyColor());
	}
}

// ---------------------------------------------------------------- character looks

void AIAPlayerCharacter::UpdateLook()
{
	int32 Index = ForcedLook;
	uint8 Team = IA_NoTeam;
	if (const AIAPlayerState* PS = GetPlayerState<AIAPlayerState>())
	{
		Index = PS->CharacterIndex;
		Team = PS->Team;
	}
	else if (ForcedLook < 0)
	{
		return; // nothing to show yet, the placeholder stays
	}

	const int32 Key = Index * 1000 + Team;
	if (Key == AppliedLookKey)
	{
		return;
	}
	AppliedLookKey = Key;
	ApplyLook(Index, Team);
}

void AIAPlayerCharacter::ApplyLook(int32 CharacterIndex, uint8 Team)
{
	const FIACharacterLook& Look = IACharacters::GetLook(CharacterIndex);

	USkeletalMesh* MeshAsset = LoadObject<USkeletalMesh>(nullptr, Look.bQuinn
		? TEXT("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple")
		: TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
	UMaterialInterface* BaseMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody"));
	if (!MeshAsset || !BaseMaterial)
	{
		UE_LOG(LogInstagib, Warning, TEXT("Look: character assets missing, keeping the placeholder body"));
		AppliedLookKey = INT32_MIN;
		return;
	}

	USkeletalMeshComponent* Skel = GetMesh();
	Skel->SetSkeletalMesh(MeshAsset);
	// Location and rotation of the mesh are set in the constructor (the character class remembers
	// them for network smoothing), so only the scale changes here.
	Skel->SetRelativeScale3D(FVector(Look.MeshScale));
	Skel->SetVisibility(true);
	Skel->SetOwnerNoSee(true);
	Skel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	// Third-person animation is done in code (rifle poses, 8-way locomotion, aim, crouch, jump and landing).
	Skel->SetAnimationMode(EAnimationMode::AnimationBlueprint);
	Skel->SetAnimInstanceClass(UIAAnimInstance::StaticClass());
	BodyMesh->SetVisibility(false);

	// Colors. Roster entries past the first five reuse a look with the hue turned.
	FLinearColor Body = Look.Body;
	FLinearColor Accent = Look.Accent;
	const int32 Variant = CharacterIndex / IACharacters::LookCount;
	if (Variant > 0)
	{
		auto Turn = [Variant](const FLinearColor& C, float Degrees)
		{
			FLinearColor Hsv = C.LinearRGBToHSV();
			Hsv.R = FMath::Fmod(Hsv.R + Degrees * Variant, 360.f);
			Hsv.G = FMath::Max(Hsv.G, 0.5f);
			return Hsv.HSVToLinearRGB();
		};
		Body = Turn(Body, 50.f);
		Accent = Turn(Accent, 80.f);
	}

	FLinearColor TeamColor = Accent;
	if (Team == 0) { TeamColor = FLinearColor(1.f, 0.06f, 0.06f); }
	else if (Team == 1) { TeamColor = FLinearColor(0.08f, 0.28f, 1.f); }
	if (Team != IA_NoTeam)
	{
		Body = FMath::Lerp(Body, TeamColor * 0.5f, 0.35f);
	}

	auto MakeMaterial = [&](const FLinearColor& Color, float Roughness, float Metallic, float Glow)
	{
		UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, this);
		Material->SetVectorParameterValue(TEXT("Color"), Color);
		Material->SetScalarParameterValue(TEXT("Roughness"), Roughness);
		Material->SetScalarParameterValue(TEXT("Metallic"), Metallic);
		Material->SetScalarParameterValue(TEXT("Glow"), Glow);
		return Material;
	};

	UMaterialInstanceDynamic* BodyMat = MakeMaterial(Body, Look.Roughness, Look.Metallic, Look.BodyGlow);
	for (int32 Slot = 0; Slot < Skel->GetNumMaterials(); ++Slot)
	{
		Skel->SetMaterial(Slot, BodyMat);
	}

	UMaterialInstanceDynamic* AccentMat = MakeMaterial(Accent, 0.4f, 0.15f, 0.f);
	UMaterialInstanceDynamic* TeamMat = MakeMaterial(TeamColor, 0.4f, 0.1f, Team == IA_NoTeam ? 0.f : 0.8f);
	UMaterialInstanceDynamic* GlowMat = MakeMaterial(Accent, 0.3f, 0.f, 6.f);
	UMaterialInstanceDynamic* LightMat = MakeMaterial(FLinearColor(0.92f, 0.92f, 0.88f), 0.7f, 0.f, 0.f);

	// Accessories: rebuilt from scratch whenever the look changes.
	for (UStaticMeshComponent* Old : Accessories)
	{
		if (Old)
		{
			Old->DestroyComponent();
		}
	}
	Accessories.Reset();

	const FReferenceSkeleton& RefSkeleton = MeshAsset->GetRefSkeleton();
	const FQuat MeshToActor = FRotator(0.f, -90.f, 0.f).Quaternion(); // the mesh component's rotation inside the actor

	for (const FIAAccessory& Part : Look.Parts)
	{
		const int32 BoneIndex = RefSkeleton.FindBoneIndex(Part.Bone);
		if (BoneIndex == INDEX_NONE)
		{
			UE_LOG(LogInstagib, Warning, TEXT("Look %s: bone %s not found"), Look.Name, Part.Bone);
			continue;
		}

		const TCHAR* ShapePath = TEXT("/Engine/BasicShapes/Cube.Cube");
		switch (Part.Shape)
		{
		case EIAShape::Cylinder: ShapePath = TEXT("/Engine/BasicShapes/Cylinder.Cylinder"); break;
		case EIAShape::Sphere:   ShapePath = TEXT("/Engine/BasicShapes/Sphere.Sphere"); break;
		case EIAShape::Cone:     ShapePath = TEXT("/Engine/BasicShapes/Cone.Cone"); break;
		default: break;
		}
		UStaticMesh* ShapeMesh = LoadObject<UStaticMesh>(nullptr, ShapePath);
		if (!ShapeMesh)
		{
			continue;
		}

		// Character-space offset and rotation, converted into the bone's own space using the reference pose.
		const FTransform BoneInMesh = FAnimationRuntime::GetComponentSpaceTransformRefPose(RefSkeleton, BoneIndex);
		const FVector OffsetInMesh = MeshToActor.UnrotateVector(Part.Offset);
		const FVector LocalOffset = BoneInMesh.GetRotation().UnrotateVector(OffsetInMesh);
		const FQuat LocalRotation = BoneInMesh.GetRotation().Inverse() * MeshToActor.Inverse() * Part.Rotation.Quaternion();

		UMaterialInstanceDynamic* Material = AccentMat;
		switch (Part.Color)
		{
		case EIAPartColor::Body:   Material = BodyMat; break;
		case EIAPartColor::Accent: Material = AccentMat; break;
		case EIAPartColor::Team:   Material = TeamMat; break;
		case EIAPartColor::Glow:   Material = GlowMat; break;
		case EIAPartColor::Light:  Material = LightMat; break;
		}

		UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(this);
		Comp->SetStaticMesh(ShapeMesh);
		Comp->SetMaterial(0, Material);
		Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Comp->SetOwnerNoSee(true);
		Comp->SetCastShadow(false);
		Comp->SetRelativeLocationAndRotation(LocalOffset, LocalRotation.Rotator());
		Comp->SetRelativeScale3D(Part.Size / 100.f);
		Comp->RegisterComponent();
		Comp->AttachToComponent(Skel, FAttachmentTransformRules::KeepRelativeTransform, Part.Bone);
		Accessories.Add(Comp);
	}

	// The rifle follows the character's accent color.
	CurrentAccent = Accent;
	DestroyWeapon(false);
	BuildWeapon(false, MeshAsset);
	if (FPWeaponRoot)
	{
		DestroyWeapon(true);
		BuildWeapon(true, MeshAsset);
	}
}

// ---------------------------------------------------------------- the rifle

namespace
{
	/** One piece of the rifle, in rifle space: X forward, Y right, Z up, centimeters. */
	struct FRiflePart
	{
		EIAShape Shape;
		FVector Location;
		FRotator Rotation;
		FVector Size;   // for cylinders: diameter, diameter, length (the axis is local Z)
		int32 Kind;     // 0 body, 1 accent, 2 glow core, 3 glow flash
	};

	const FRotator AlongX(-90.f, 0.f, 0.f); // turns a cylinder's Z axis into the X axis

	const FRiflePart RifleParts[] = {
		{ EIAShape::Cube,     FVector(10, 0, 0),    FRotator::ZeroRotator, FVector(34, 6.5f, 9),     0 },
		{ EIAShape::Cube,     FVector(12, 0, 5.5f), FRotator::ZeroRotator, FVector(28, 3, 2.5f),     1 },
		{ EIAShape::Cylinder, FVector(38, 0, 0.5f), AlongX,                FVector(4.2f, 4.2f, 32),  0 },
		{ EIAShape::Cylinder, FVector(24, 0, 0),    AlongX,                FVector(6.8f, 6.8f, 14),  2 },
		{ EIAShape::Cylinder, FVector(32, 0, 0.5f), AlongX,                FVector(7.6f, 7.6f, 1.8f), 1 },
		{ EIAShape::Cylinder, FVector(38, 0, 0.5f), AlongX,                FVector(7.6f, 7.6f, 1.8f), 1 },
		{ EIAShape::Cylinder, FVector(44, 0, 0.5f), AlongX,                FVector(7.6f, 7.6f, 1.8f), 1 },
		{ EIAShape::Cube,     FVector(18, 5, -1),   FRotator::ZeroRotator, FVector(12, 1.5f, 6),     1 },
		{ EIAShape::Cube,     FVector(18, -5, -1),  FRotator::ZeroRotator, FVector(12, 1.5f, 6),     1 },
		{ EIAShape::Cube,     FVector(4, 0, -8),    FRotator(-15, 0, 0),   FVector(5, 4.5f, 12),     0 },
		{ EIAShape::Sphere,   FVector(55, 0, 0.5f), FRotator::ZeroRotator, FVector(3, 3, 3),         3 },
	};

	const FVector RifleMuzzle(56.f, 0.f, 0.5f);

	// How the rifle sits in the right hand of the third-person character (bone space of hand_r).
	const FVector TPRifleHandOffset(2.f, -3.5f, 6.3f);
	const FRotator TPRifleHandRotation(-2.f, 155.f, 20.f);
	constexpr float TPRifleScale = 0.85f;
}

void AIAPlayerCharacter::DestroyWeapon(bool bFirstPerson)
{
	TArray<TObjectPtr<UStaticMeshComponent>>& Parts = bFirstPerson ? FPWeaponParts : TPWeaponParts;
	TObjectPtr<USceneComponent>& Root = bFirstPerson ? FPWeaponRoot : TPWeaponRoot;

	for (UStaticMeshComponent* Part : Parts)
	{
		if (Part)
		{
			Part->DestroyComponent();
		}
	}
	Parts.Reset();
	if (Root)
	{
		Root->DestroyComponent();
		Root = nullptr;
	}
	if (bFirstPerson)
	{
		FPMuzzleFlash = nullptr;
		FPCoreMaterial = nullptr;
	}
}

void AIAPlayerCharacter::BuildWeapon(bool bFirstPerson, USkeletalMesh* MeshAsset)
{
	UMaterialInterface* BaseMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody"));
	if (!BaseMaterial)
	{
		return;
	}

	auto MakeMaterial = [&](const FLinearColor& Color, float Roughness, float Metallic, float Glow)
	{
		UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, this);
		Material->SetVectorParameterValue(TEXT("Color"), Color);
		Material->SetScalarParameterValue(TEXT("Roughness"), Roughness);
		Material->SetScalarParameterValue(TEXT("Metallic"), Metallic);
		Material->SetScalarParameterValue(TEXT("Glow"), Glow);
		return Material;
	};

	UMaterialInstanceDynamic* BodyMat = MakeMaterial(FLinearColor(0.045f, 0.05f, 0.06f), 0.35f, 0.5f, 0.f);
	UMaterialInstanceDynamic* AccentMat = MakeMaterial(CurrentAccent, 0.4f, 0.2f, 0.4f);
	UMaterialInstanceDynamic* CoreMat = MakeMaterial(CurrentAccent, 0.3f, 0.f, 4.f);
	UMaterialInstanceDynamic* FlashMat = MakeMaterial(CurrentAccent, 0.3f, 0.f, 12.f);

	USceneComponent* Root = NewObject<USceneComponent>(this);
	if (bFirstPerson)
	{
		// Bottom right of the screen, a bit smaller than life so that it does not fill the view.
		Root->SetupAttachment(FirstPersonCamera);
		Root->SetRelativeLocationAndRotation(FVector(26.f, 12.f, -12.f), FRotator::ZeroRotator);
		Root->SetRelativeScale3D(FVector(0.5f));
		Root->RegisterComponent();
		FPWeaponRoot = Root;
	}
	else
	{
		if (!MeshAsset)
		{
			Root->DestroyComponent();
			return;
		}
		if (MeshAsset->GetRefSkeleton().FindBoneIndex(TEXT("hand_r")) == INDEX_NONE)
		{
			Root->DestroyComponent();
			return;
		}

		// Held in the right hand. The offset (bone space of hand_r) fits the rifle poses of the animation.
		FVector HandOffset(TPRifleHandOffset);
		FRotator HandRotation(TPRifleHandRotation);
		float HandScale = TPRifleScale;
#if !UE_BUILD_SHIPPING
		// Developer tuning without a rebuild:  -IARifleOffset=x,y,z,pitch,yaw,roll,scale
		FString Tuning;
		TArray<FString> Numbers;
		if (FParse::Value(FCommandLine::Get(), TEXT("IARifleOffset="), Tuning, /*bShouldStopOnSeparator*/ false))
		{
			Tuning.ParseIntoArray(Numbers, TEXT(","));
			if (Numbers.Num() >= 6)
			{
				HandOffset = FVector(FCString::Atof(*Numbers[0]), FCString::Atof(*Numbers[1]), FCString::Atof(*Numbers[2]));
				HandRotation = FRotator(FCString::Atof(*Numbers[3]), FCString::Atof(*Numbers[4]), FCString::Atof(*Numbers[5]));
			}
			if (Numbers.Num() >= 7)
			{
				HandScale = FCString::Atof(*Numbers[6]);
			}
		}
#endif
		Root->SetRelativeLocationAndRotation(HandOffset, HandRotation);
		Root->SetRelativeScale3D(FVector(HandScale));
		Root->RegisterComponent();
		Root->AttachToComponent(GetMesh(), FAttachmentTransformRules::KeepRelativeTransform, TEXT("hand_r"));
		TPWeaponRoot = Root;
	}

	TArray<TObjectPtr<UStaticMeshComponent>>& Parts = bFirstPerson ? FPWeaponParts : TPWeaponParts;
	for (const FRiflePart& Part : RifleParts)
	{
		const TCHAR* ShapePath = TEXT("/Engine/BasicShapes/Cube.Cube");
		if (Part.Shape == EIAShape::Cylinder) { ShapePath = TEXT("/Engine/BasicShapes/Cylinder.Cylinder"); }
		else if (Part.Shape == EIAShape::Sphere) { ShapePath = TEXT("/Engine/BasicShapes/Sphere.Sphere"); }
		UStaticMesh* ShapeMesh = LoadObject<UStaticMesh>(nullptr, ShapePath);
		if (!ShapeMesh)
		{
			continue;
		}

		UMaterialInstanceDynamic* Material = BodyMat;
		if (Part.Kind == 1) { Material = AccentMat; }
		else if (Part.Kind == 2) { Material = CoreMat; }
		else if (Part.Kind == 3) { Material = FlashMat; }

		UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(this);
		Comp->SetStaticMesh(ShapeMesh);
		Comp->SetMaterial(0, Material);
		Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Comp->SetCastShadow(false);
		if (bFirstPerson)
		{
			Comp->SetOnlyOwnerSee(true);
		}
		else
		{
			Comp->SetOwnerNoSee(true);
		}
		Comp->SetRelativeLocationAndRotation(Part.Location, Part.Rotation);
		Comp->SetRelativeScale3D(Part.Size / 100.f);
		Comp->RegisterComponent();
		Comp->AttachToComponent(Root, FAttachmentTransformRules::KeepRelativeTransform);
		Parts.Add(Comp);

		if (bFirstPerson && Part.Kind == 2) { FPCoreMaterial = Material; }
		if (bFirstPerson && Part.Kind == 3) { FPMuzzleFlash = Comp; }
	}
}

FVector AIAPlayerCharacter::GetMuzzleLocation(const FVector& Fallback) const
{
	const USceneComponent* Root = (IsLocalHuman() && FPWeaponRoot) ? FPWeaponRoot.Get() : TPWeaponRoot.Get();
	return Root ? Root->GetComponentTransform().TransformPosition(RifleMuzzle) : Fallback;
}

void AIAPlayerCharacter::UpdateWeaponView(float DeltaSeconds)
{
	if (GetNetMode() == NM_DedicatedServer)
	{
		return;
	}

	// The player's field of view setting applies to their own camera.
	if (IsLocalHuman() && FirstPersonCamera)
	{
		FirstPersonCamera->SetFieldOfView(IASettings::GetFieldOfView());
	}

	// The on-screen rifle exists only for the human playing on this machine.
	if (!FPWeaponRoot && IsLocalHuman() && !bDead && AppliedLookKey != INT32_MIN)
	{
		BuildWeapon(true, GetMesh()->GetSkeletalMeshAsset());
	}
	if (!FPWeaponRoot)
	{
		return;
	}
	if (bDead || !IsLocalHuman())
	{
		FPWeaponRoot->SetVisibility(false, true);
		return;
	}
	FPWeaponRoot->SetVisibility(true, true);

	Recoil = FMath::Max(0.f, Recoil - DeltaSeconds * 6.f);

	// Idle sway and running bob.
	const float Speed = GetVelocity().Size2D();
	const float MoveAlpha = GetCharacterMovement()->IsMovingOnGround() ? FMath::Clamp(Speed / 600.f, 0.f, 1.f) : 0.f;
	BobTime += DeltaSeconds * (1.5f + MoveAlpha * 8.f);
	const float BobY = FMath::Sin(BobTime) * (0.15f + MoveAlpha * 0.6f);
	const float BobZ = FMath::Cos(BobTime * 2.f) * (0.1f + MoveAlpha * 0.5f);

	const FVector Base(26.f, 12.f, -12.f);
	const FVector Kick(-7.f * Recoil, 0.f, 1.8f * Recoil);
	FPWeaponRoot->SetRelativeLocationAndRotation(Base + Kick + FVector(0.f, BobY, BobZ), FRotator(7.f * Recoil, 0.f, 0.f));

	// The core and the muzzle light up with each shot.
	if (FPCoreMaterial)
	{
		FPCoreMaterial->SetScalarParameterValue(TEXT("Glow"), 4.f + 14.f * Recoil);
	}
	if (FPMuzzleFlash)
	{
		const float FlashSize = (2.f + 11.f * Recoil) / 100.f;
		FPMuzzleFlash->SetRelativeScale3D(FVector(FlashSize));
		FPMuzzleFlash->SetVisibility(Recoil > 0.15f);
	}
}
