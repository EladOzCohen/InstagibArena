// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "IABotController.generated.h"

class AIAPlayerCharacter;

/** Skill levels offered to the player, from the gentlest to the hardest (seven steps, see IABots in IASettings.h). */
UENUM(BlueprintType)
enum class EIABotSkill : uint8
{
	Rookie = 0,
	Beginner = 1,
	Casual = 2,
	Intermediate = 3,
	Advanced = 4,
	Expert = 5,
	Master = 6
};

/** Tuning values that make up one skill level. */
struct FIABotSkillParams
{
	float ReactionTime;        // seconds between first seeing an enemy and the first shot
	float AimErrorDegrees;     // random aim offset, re-rolled a few times per second
	float TurnRate;            // degrees per second the view can turn
	float FireToleranceDeg;    // how far off target the bot is willing to shoot
	float DodgesPerSecond;     // chance per second to dodge while an enemy is in view
	float JumpsPerSecond;      // chance per second to jump while in combat
	float SightRange;          // how far the bot can see
	float MemorySeconds;       // how long it chases the last known position
	float FieldOfViewDeg;      // total horizontal field of view

	static FIABotSkillParams ForSkill(EIABotSkill Skill);
};

/**
 * AI player. Sees enemies with line traces, paths over the nav grid,
 * strafes and dodges in combat, and fires the same instagib rifle as players.
 */
UCLASS()
class INSTAGIBARENA_API AIABotController : public AAIController
{
	GENERATED_BODY()

public:
	AIABotController();

	void SetSkill(EIABotSkill NewSkill);

	virtual void Tick(float DeltaSeconds) override;
	virtual void UpdateControlRotation(float DeltaTime, bool bUpdatePawn = true) override {}

protected:
	virtual void OnUnPossess() override;

private:
	void Think();
	void FindTarget(AIAPlayerCharacter* Me);
	bool IsEnemy(const AIAPlayerCharacter* Me, const AIAPlayerCharacter* Other) const;
	bool CanSee(const AIAPlayerCharacter* Me, const AIAPlayerCharacter* Other) const;
	bool HasGroundAhead(const AIAPlayerCharacter* Me, const FVector& Direction, float Distance = 250.f) const;
	bool LineOfFireHitsTeammate(const AIAPlayerCharacter* Me) const;

	void UpdateAim(AIAPlayerCharacter* Me, float DeltaSeconds);
	void UpdateMovement(AIAPlayerCharacter* Me, float DeltaSeconds);
	void UpdateFire(AIAPlayerCharacter* Me);
	void FollowPath(AIAPlayerCharacter* Me, float DeltaSeconds);
	void RepathTo(const FVector& Goal, const FVector& From);

	EIABotSkill Skill = EIABotSkill::Intermediate;
	FIABotSkillParams Params;

	float ThinkAccumulator = 0.f;
	float LogAccumulator = 0.f;

	// Target tracking.
	TWeakObjectPtr<AIAPlayerCharacter> Target;
	bool bTargetVisible = false;
	float TargetAcquiredTime = 0.f;
	FVector LastSeenLocation = FVector::ZeroVector;
	float LastSeenTime = -100.f;

	// Aim.
	FRotator AimOffset = FRotator::ZeroRotator;
	float NextAimRollTime = 0.f;

	// Movement.
	TArray<FVector> Path;
	int32 PathIndex = 0;
	FVector PathGoal = FVector::ZeroVector;
	float NextRepathTime = 0.f;
	float StrafeDirection = 1.f;
	float NextStrafeFlipTime = 0.f;
	bool bReleaseJump = false;

	// Stuck detection.
	FVector StuckCheckLocation = FVector::ZeroVector;
	float StuckCheckTime = 0.f;
};
