// Instagib Arena

#include "IACharacterMovement.h"
#include "GameFramework/Character.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"

namespace
{
	/** Saved move that carries the dodge request to the server. */
	class FSavedMove_IA : public FSavedMove_Character
	{
	public:
		typedef FSavedMove_Character Super;

		bool bSavedWantsToDodge = false;
		uint8 SavedDodgeDir = 0;

		virtual void Clear() override
		{
			Super::Clear();
			bSavedWantsToDodge = false;
			SavedDodgeDir = 0;
		}

		virtual void SetMoveFor(ACharacter* C, float InDeltaTime, FVector const& NewAccel, FNetworkPredictionData_Client_Character& ClientData) override
		{
			Super::SetMoveFor(C, InDeltaTime, NewAccel, ClientData);
			if (const UIACharacterMovement* Move = Cast<UIACharacterMovement>(C->GetCharacterMovement()))
			{
				bSavedWantsToDodge = Move->bWantsToDodge;
				SavedDodgeDir = Move->WantedDodgeDir;
			}
		}

		virtual void PrepMoveFor(ACharacter* C) override
		{
			Super::PrepMoveFor(C);
			if (UIACharacterMovement* Move = Cast<UIACharacterMovement>(C->GetCharacterMovement()))
			{
				Move->bWantsToDodge = bSavedWantsToDodge;
				Move->WantedDodgeDir = SavedDodgeDir;
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
			return Result;
		}

		virtual bool CanCombineWith(const FSavedMovePtr& NewMove, ACharacter* InCharacter, float MaxDelta) const override
		{
			const FSavedMove_IA* Other = static_cast<const FSavedMove_IA*>(NewMove.Get());
			if (bSavedWantsToDodge || Other->bSavedWantsToDodge)
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
	// UT-like feel: fast acceleration, strong air control, high jumps.
	MaxWalkSpeed = 600.f;
	MaxAcceleration = 2600.f;
	GroundFriction = 8.f;
	BrakingDecelerationWalking = 2400.f;
	JumpZVelocity = 620.f;
	AirControl = 0.35f;
	BrakingDecelerationFalling = 200.f;
	GravityScale = 1.15f;
	MaxStepHeight = 45.f;
	SetWalkableFloorAngle(50.f);
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
}

void UIACharacterMovement::RequestDodge(EIADodgeDir Direction)
{
	bWantsToDodge = true;
	WantedDodgeDir = static_cast<uint8>(Direction);
}

void UIACharacterMovement::UpdateCharacterStateBeforeMovement(float DeltaSeconds)
{
	Super::UpdateCharacterStateBeforeMovement(DeltaSeconds);

	CooldownRemaining = FMath::Max(0.f, CooldownRemaining - DeltaSeconds);

	if (bWantsToDodge)
	{
		bWantsToDodge = false;
		if (CooldownRemaining <= 0.f)
		{
			PerformDodge();
		}
	}
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
		// Ground dodge.
		Velocity = Direction * DodgeSpeed;
		Velocity.Z = DodgeVerticalSpeed;
		SetMovementMode(MOVE_Falling);
		CooldownRemaining = DodgeCooldown;
	}
	else if (IsFalling() && !bWallDodgedThisJump)
	{
		// Wall dodge: a wall in the dodge direction pushes the player off it.
		const UCapsuleComponent* Capsule = CharacterOwner->GetCapsuleComponent();
		const float Reach = (Capsule ? Capsule->GetScaledCapsuleRadius() : 34.f) + WallDetectDistance;
		const FVector Start = UpdatedComponent->GetComponentLocation();
		const FVector End = Start + Direction * Reach;

		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(IAWallDodge), false, CharacterOwner);
		if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_WorldStatic, Params)
			&& Hit.ImpactNormal.Z < 0.3f)
		{
			const FVector Away = Hit.ImpactNormal.GetSafeNormal2D();
			Velocity = Away * WallDodgeSpeed;
			Velocity.Z = WallDodgeVerticalSpeed;
			bWallDodgedThisJump = true;
			CooldownRemaining = DodgeCooldown;
		}
	}
}

void UIACharacterMovement::ProcessLanded(const FHitResult& Hit, float RemainingTime, int32 Iterations)
{
	Super::ProcessLanded(Hit, RemainingTime, Iterations);
	bWallDodgedThisJump = false;
}
