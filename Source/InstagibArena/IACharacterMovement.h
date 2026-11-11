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
 * Character movement with UT2004-style dodge, wall dodge, double jump, crouch and slow walk.
 *
 * Everything that changes the player's movement is client-predicted: the requests (dodge, walk, crouch)
 * travel to the server inside the compressed move flags, and the little state they depend on (dodge
 * cooldown, wall dodge used) is stored in the saved move, so that corrected moves replay the same way.
 */
UCLASS()
class INSTAGIBARENA_API UIACharacterMovement : public UCharacterMovementComponent
{
	GENERATED_BODY()

public:
	UIACharacterMovement();

	// ---- dodge

	/** Horizontal speed given by a ground dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float DodgeSpeed = 800.f;

	/** Upward speed given by a ground dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float DodgeVerticalSpeed = 280.f;

	/** Minimum seconds between dodges. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float DodgeCooldown = 0.4f;

	/** After landing from a dodge the next dodge needs at least this long. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float DodgeLandingLockout = 0.18f;

	/** Horizontal speed given by a wall dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float WallDodgeSpeed = 780.f;

	/** Upward speed given by a wall dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float WallDodgeVerticalSpeed = 400.f;

	/** How far from the capsule edge a wall may be for a wall dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float WallDetectDistance = 70.f;

	// ---- jumping

	/** The second (air) jump reaches this fraction of the first jump's upward speed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Jump")
	float DoubleJumpScale = 0.86f;

	/** Seconds after the first jump before the air jump is accepted (a double tap would otherwise merge into one jump). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Jump")
	float DoubleJumpDelay = 0.1f;

	/** Falling faster than this when landing slows the player down (units per second). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Jump")
	float HardLandingSpeed = 1000.f;

	// ---- walk

	/** Top speed while the walk key is held (quiet and precise). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Walk")
	float SlowWalkSpeed = 320.f;

	/** Called by the owning client (or the server for bots) to request a dodge. */
	void RequestDodge(EIADodgeDir Direction);

	/** Slow walk (hold). Predicted like crouching. */
	void SetWantsToWalk(bool bWalk) { bWantsToWalk = bWalk; }
	bool WantsToWalk() const { return bWantsToWalk; }

	virtual FNetworkPredictionData_Client* GetPredictionData_Client() const override;
	virtual void UpdateFromCompressedFlags(uint8 Flags) override;
	virtual void UpdateCharacterStateBeforeMovement(float DeltaSeconds) override;
	virtual void ProcessLanded(const FHitResult& Hit, float RemainingTime, int32 Iterations) override;
	virtual bool DoJump(bool bReplayingMoves, float DeltaTime) override;
	virtual float GetMaxSpeed() const override;

	bool bWantsToDodge = false;
	uint8 WantedDodgeDir = 0;
	bool bWantsToWalk = false;

	// ---- read by the camera and the animation (cosmetic only)

	/** Downward speed at the last landing and the world time it happened. */
	float LastLandingSpeed = 0.f;
	float LastLandingTime = -10.f;

	/** Seconds left until the next dodge is allowed, and whether a wall dodge was already used in this jump. */
	float CooldownRemaining = 0.f;
	bool bWallDodgedThisJump = false;

	/** Seconds since the last jump, and whether this stretch in the air began with (or contained) a dodge. */
	float TimeSinceJump = 10.f;
	bool bDodgedThisAir = false;

	/** Counts every dodge that was performed on this machine. The camera and the animation watch it. */
	int32 DodgeCounter = 0;
	EIADodgeDir LastDodgeDir = EIADodgeDir::Forward;

private:
	void PerformDodge();
	bool FindWall(const FVector& Direction, FHitResult& OutHit) const;
};
