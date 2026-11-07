// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "IACharacterMovement.generated.h"

/** Direction of a dodge, relative to where the player is facing. */
UENUM()
enum class EIADodgeDir : uint8
{
	Forward = 0,
	Back = 1,
	Left = 2,
	Right = 3
};

/**
 * Character movement with UT2004-style dodge and wall dodge.
 * Double jump comes from ACharacter::JumpMaxCount = 2.
 * Dodge requests travel to the server inside the compressed move flags,
 * so they are client-predicted and replay correctly after corrections.
 */
UCLASS()
class INSTAGIBARENA_API UIACharacterMovement : public UCharacterMovementComponent
{
	GENERATED_BODY()

public:
	UIACharacterMovement();

	/** Horizontal speed given by a ground dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float DodgeSpeed = 950.f;

	/** Upward speed given by a ground dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float DodgeVerticalSpeed = 320.f;

	/** Minimum seconds between dodges. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float DodgeCooldown = 0.45f;

	/** Horizontal speed given by a wall dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float WallDodgeSpeed = 850.f;

	/** Upward speed given by a wall dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float WallDodgeVerticalSpeed = 420.f;

	/** How far from the capsule edge a wall may be for a wall dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float WallDetectDistance = 80.f;

	/** Called by the owning client (or the server for bots) to request a dodge. */
	void RequestDodge(EIADodgeDir Direction);

	virtual FNetworkPredictionData_Client* GetPredictionData_Client() const override;
	virtual void UpdateFromCompressedFlags(uint8 Flags) override;
	virtual void UpdateCharacterStateBeforeMovement(float DeltaSeconds) override;
	virtual void ProcessLanded(const FHitResult& Hit, float RemainingTime, int32 Iterations) override;

	bool bWantsToDodge = false;
	uint8 WantedDodgeDir = 0;

private:
	void PerformDodge();

	float CooldownRemaining = 0.f;
	bool bWallDodgedThisJump = false;
};
