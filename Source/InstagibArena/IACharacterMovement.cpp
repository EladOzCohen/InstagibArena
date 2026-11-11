// Instagib Arena

#include "IACharacterMovement.h"
#include "GameFramework/Character.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"

namespace
{
	/** Saved move that carries the dodge and walk requests to the server and keeps replays exact. */
	class FSavedMove_IA : public FSavedMove_Character
	{
	public:
		typedef FSavedMove_Character Super;

		// Requests.
		bool bSavedWantsToDodge = false;
		uint8 SavedDodgeDir = 0;
		bool bSavedWantsToWalk = false;

		// State at the start of the move. A replayed move must begin with the same values.
		float SavedCooldown = 0.f;
		float SavedTimeSinceJump = 10.f;
		bool bSavedWallDodged = false;
		bool bSavedDodgedThisAir = false;

		virtual void Clear() override
		{
			Super::Clear();
			bSavedWantsToDodge = false;
			SavedDodgeDir = 0;
			bSavedWantsToWalk = false;
			SavedCooldown = 0.f;
			SavedTimeSinceJump = 10.f;
			bSavedWallDodged = false;
			bSavedDodgedThisAir = false;
		}

		virtual void SetMoveFor(ACharacter* C, float InDeltaTime, FVector const& NewAccel, FNetworkPredictionData_Client_Character& ClientData) override
		{
			Super::SetMoveFor(C, InDeltaTime, NewAccel, ClientData);
			if (const UIACharacterMovement* Move = Cast<UIACharacterMovement>(C->GetCharacterMovement()))
			{
				bSavedWantsToDodge = Move->bWantsToDodge;
				SavedDodgeDir = Move->WantedDodgeDir;
				bSavedWantsToWalk = Move->bWantsToWalk;
				SavedCooldown = Move->CooldownRemaining;
				SavedTimeSinceJump = Move->TimeSinceJump;
				bSavedWallDodged = Move->bWallDodgedThisJump;
				bSavedDodgedThisAir = Move->bDodgedThisAir;
			}
		}

		virtual void PrepMoveFor(ACharacter* C) override
		{
			Super::PrepMoveFor(C);
			if (UIACharacterMovement* Move = Cast<UIACharacterMovement>(C->GetCharacterMovement()))
			{
				Move->bWantsToDodge = bSavedWantsToDodge;
				Move->WantedDodgeDir = SavedDodgeDir;
				Move->bWantsToWalk = bSavedWantsToWalk;
				Move->CooldownRemaining = SavedCooldown;
				Move->TimeSinceJump = SavedTimeSinceJump;
				Move->bWallDodgedThisJump = bSavedWallDodged;
				Move->bDodgedThisAir = bSavedDodgedThisAir;
			}
		}

		virtual uint8 GetCompressedFlags() const override
		{
			uint8 Result = Super::GetCompressedFlags();
			if (bSavedWantsToDodge)
			{
				Result |= FLAG_Custom_0;
				if (SavedDodgeDir & 1) { Result |= FLAG_Custom_1; }
				if (SavedDodgeDir & 2) { Result |= FLAG_Custom_2; }
			}
			if (bSavedWantsToWalk)
			{
				Result |= FLAG_Custom_3;
			}
			return Result;
		}

		virtual bool IsImportantMove(const FSavedMovePtr& LastAckedMove) const override
		{
			// A dodge goes out at once, a changed walk state too.
			if (bSavedWantsToDodge)
			{
				return true;
			}
			if (LastAckedMove.IsValid() && static_cast<const FSavedMove_IA*>(LastAckedMove.Get())->bSavedWantsToWalk != bSavedWantsToWalk)
			{
				return true;
			}
			return Super::IsImportantMove(LastAckedMove);
		}

		virtual bool CanCombineWith(const FSavedMovePtr& NewMove, ACharacter* InCharacter, float MaxDelta) const override
		{
			const FSavedMove_IA* Other = static_cast<const FSavedMove_IA*>(NewMove.Get());
			if (bSavedWantsToDodge || Other->bSavedWantsToDodge || bSavedWantsToWalk != Other->bSavedWantsToWalk)
			{
				return false;
			}
			return Super::CanCombineWith(NewMove, InCharacter, MaxDelta);
		}
	};

	class FNetworkPredictionData_Client_IA : public FNetworkPredictionData_Client_Character
	{
	public:
		FNetworkPredictionData_Client_IA(const UCharacterMovementComponent& ClientMovement)
			: FNetworkPredictionData_Client_Character(ClientMovement)
		{
		}

		virtual FSavedMovePtr AllocateNewMove() override
		{
			return FSavedMovePtr(new FSavedMove_IA());
		}
	};
}

UIACharacterMovement::UIACharacterMovement()
{
	// Ground: fast acceleration and short stopping, like a classic arena shooter.
	MaxWalkSpeed = 600.f;
	MaxAcceleration = 2600.f;
	GroundFriction = 8.f;
	BrakingDecelerationWalking = 2400.f;

	// Air: high jumps, strong air control, momentum is kept.
	JumpZVelocity = 620.f;
	GravityScale = 1.15f;
	AirControl = 0.45f;
	AirControlBoostMultiplier = 2.f;
	AirControlBoostVelocityThreshold = 25.f;
	BrakingDecelerationFalling = 120.f;

	// Terrain: no sticking on ledge edges, small steps are climbed.
	MaxStepHeight = 45.f;
	PerchRadiusThreshold = 10.f;
	SetWalkableFloorAngle(50.f);

	// Crouch (hold). The capsule keeps its base, so the head comes down.
	NavAgentProps.bCanCrouch = true;
	SetCrouchedHalfHeight(60.f);
	MaxWalkSpeedCrouched = 300.f;
	bCrouchMaintainsBaseLocation = true;
}

FNetworkPredictionData_Client* UIACharacterMovement::GetPredictionData_Client() const
{
	if (ClientPredictionData == nullptr)
	{
		UIACharacterMovement* MutableThis = const_cast<UIACharacterMovement*>(this);
		MutableThis->ClientPredictionData = new FNetworkPredictionData_Client_IA(*this);
	}
	return ClientPredictionData;
}

void UIACharacterMovement::UpdateFromCompressedFlags(uint8 Flags)
{
	Super::UpdateFromCompressedFlags(Flags);

	bWantsToDodge = (Flags & FSavedMove_Character::FLAG_Custom_0) != 0;
	WantedDodgeDir = 0;
	if (Flags & FSavedMove_Character::FLAG_Custom_1) { WantedDodgeDir |= 1; }
	if (Flags & FSavedMove_Character::FLAG_Custom_2) { WantedDodgeDir |= 2; }
	bWantsToWalk = (Flags & FSavedMove_Character::FLAG_Custom_3) != 0;
}

void UIACharacterMovement::RequestDodge(EIADodgeDir Direction)
{
	bWantsToDodge = true;
	WantedDodgeDir = static_cast<uint8>(Direction);
}

float UIACharacterMovement::GetMaxSpeed() const
{
	float Speed = Super::GetMaxSpeed();
	if (bWantsToWalk && IsMovingOnGround())
	{
		Speed = FMath::Min(Speed, SlowWalkSpeed);
	}
	return Speed;
}

void UIACharacterMovement::UpdateCharacterStateBeforeMovement(float DeltaSeconds)
{
	Super::UpdateCharacterStateBeforeMovement(DeltaSeconds);

	CooldownRemaining = FMath::Max(0.f, CooldownRemaining - DeltaSeconds);
	TimeSinceJump += DeltaSeconds;

	if (bWantsToDodge)
	{
		bWantsToDodge = false;
		PerformDodge();
	}
}

bool UIACharacterMovement::DoJump(bool bReplayingMoves, float DeltaTime)
{
	const bool bInAir = IsFalling();

	// Two taps in quick succession would merge into one big jump, so the air jump has to wait a moment.
	if (bInAir && TimeSinceJump < DoubleJumpDelay)
	{
		return false;
	}

	const bool bJumped = Super::DoJump(bReplayingMoves, DeltaTime);
	if (bJumped)
	{
		if (bInAir)
		{
			// The air jump is a little lower than the first one, but also helps when falling fast.
			Velocity.Z = JumpZVelocity * DoubleJumpScale;
		}
		TimeSinceJump = 0.f;
	}
	return bJumped;
}

bool UIACharacterMovement::FindWall(const FVector& Direction, FHitResult& OutHit) const
{
	const UCapsuleComponent* Capsule = CharacterOwner ? CharacterOwner->GetCapsuleComponent() : nullptr;
	if (!Capsule || !GetWorld())
	{
		return false;
	}

	const float Radius = Capsule->GetScaledCapsuleRadius();
	const float HalfHeight = Capsule->GetScaledCapsuleHalfHeight();
	const float Reach = Radius + WallDetectDistance;
	const FVector Center = UpdatedComponent->GetComponentLocation();

	FCollisionQueryParams Params(SCENE_QUERY_STAT(IAWallDodge), false, CharacterOwner);

	// Three heights and three angles: a ledge, a corner or a slightly angled wall still counts.
	const float Heights[3] = { 0.f, HalfHeight * 0.55f, -HalfHeight * 0.55f };
	const float Angles[3] = { 0.f, -30.f, 30.f };

	bool bFound = false;
	float BestDistance = TNumericLimits<float>::Max();
	for (const float Height : Heights)
	{
		for (const float Angle : Angles)
		{
			const FVector Dir = Direction.RotateAngleAxis(Angle, FVector::UpVector);
			const FVector Start = Center + FVector(0.f, 0.f, Height);
			FHitResult Hit;
			if (!GetWorld()->LineTraceSingleByChannel(Hit, Start, Start + Dir * Reach, ECC_WorldStatic, Params))
			{
				continue;
			}
			// A wall: nearly vertical, and facing us.
			if (FMath::Abs(Hit.ImpactNormal.Z) > 0.3f || FVector::DotProduct(Hit.ImpactNormal, Dir) > -0.15f)
			{
				continue;
			}
			if (Hit.Distance < BestDistance)
			{
				BestDistance = Hit.Distance;
				OutHit = Hit;
				bFound = true;
			}
		}
	}
	return bFound;
}

void UIACharacterMovement::PerformDodge()
{
	if (!CharacterOwner || !UpdatedComponent)
	{
		return;
	}

	const FRotator YawRotation(0.f, UpdatedComponent->GetComponentRotation().Yaw, 0.f);
	const FVector Forward = YawRotation.Vector();
	const FVector Right = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);

	FVector Direction = Forward;
	switch (static_cast<EIADodgeDir>(WantedDodgeDir))
	{
	case EIADodgeDir::Forward: Direction = Forward; break;
	case EIADodgeDir::Back:    Direction = -Forward; break;
	case EIADodgeDir::Left:    Direction = -Right; break;
	case EIADodgeDir::Right:   Direction = Right; break;
	}

	if (IsMovingOnGround())
	{
		if (CooldownRemaining > 0.f)
		{
			return;
		}

		// Dodging gets you up from a crouch.
		if (IsCrouching())
		{
			bWantsToCrouch = false;
			UnCrouch(false);
		}

		Velocity = Direction * DodgeSpeed;
		Velocity.Z = DodgeVerticalSpeed;
		SetMovementMode(MOVE_Falling);
		CooldownRemaining = DodgeCooldown;
		bDodgedThisAir = true;
		LastDodgeDir = static_cast<EIADodgeDir>(WantedDodgeDir);
		++DodgeCounter;
	}
	else if (IsFalling() && !bWallDodgedThisJump && CooldownRemaining <= DodgeCooldown * 0.5f)
	{
		// Wall dodge: a wall in the dodge direction pushes the player off it.
		FHitResult Hit;
		if (FindWall(Direction, Hit))
		{
			const FVector Away = Hit.ImpactNormal.GetSafeNormal2D();
			const FVector Tangent = FVector::VectorPlaneProject(Velocity, FVector(Away.X, Away.Y, 0.f));
			Velocity = Away * WallDodgeSpeed + FVector(Tangent.X, Tangent.Y, 0.f) * 0.6f;
			Velocity.Z = WallDodgeVerticalSpeed;
			bWallDodgedThisJump = true;
			CooldownRemaining = DodgeCooldown;
			bDodgedThisAir = true;
			LastDodgeDir = static_cast<EIADodgeDir>(WantedDodgeDir);
			++DodgeCounter;
		}
	}
}

void UIACharacterMovement::ProcessLanded(const FHitResult& Hit, float RemainingTime, int32 Iterations)
{
	// Before the base class runs, the vertical speed is still the speed of the fall.
	LastLandingSpeed = FMath::Max(0.f, -Velocity.Z);
	LastLandingTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;

	Super::ProcessLanded(Hit, RemainingTime, Iterations);

	bWallDodgedThisJump = false;
	TimeSinceJump = 10.f;

	if (LastLandingSpeed > HardLandingSpeed)
	{
		// A hard landing costs a part of the speed.
		Velocity.X *= 0.8f;
		Velocity.Y *= 0.8f;
	}
	if (bDodgedThisAir)
	{
		bDodgedThisAir = false;
		CooldownRemaining = FMath::Max(CooldownRemaining, DodgeLandingLockout);
	}
}
