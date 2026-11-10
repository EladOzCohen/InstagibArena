// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "IAPlayerState.generated.h"

/** Team index: 0 = Red, 1 = Blue, 255 = no team (free for all). */
constexpr uint8 IA_NoTeam = 255;

UCLASS()
class INSTAGIBARENA_API AIAPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	AIAPlayerState();

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Score")
	int32 Kills = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Score")
	int32 Deaths = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Team")
	uint8 Team = IA_NoTeam;

	/** Set for AI players so the HUD can tag them. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Bot")
	bool bIsBotPlayer = false;

	/** Index into the character roster (0..14). */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Character")
	int32 CharacterIndex = 0;

	// ---- per-match statistics, kept by the server and shown on the scoreboard

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Stats")
	int32 ShotsFired = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Stats")
	int32 ShotsHit = 0;

	/** Kills since the last death. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Stats")
	int32 Streak = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Stats")
	int32 BestStreak = 0;

	/** Kills in a row with less than the multi-kill window between them (1 = a single kill). */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Stats")
	int32 MultiKill = 0;

	/** Server only: time of the last kill, for the multi-kill window. */
	float LastKillTime = -100.f;

	/** Server only: 0 = not leading, 1 = tied for the lead, 2 = leading alone. */
	uint8 LeadState = 0;

	/** Hits divided by shots, in percent. 0 when nothing was fired. */
	float GetAccuracy() const { return ShotsFired > 0 ? 100.f * ShotsHit / ShotsFired : 0.f; }

	/** Kills per death. With no death the kills count as they are. */
	float GetKillDeathRatio() const { return Deaths > 0 ? static_cast<float>(Kills) / Deaths : static_cast<float>(Kills); }

	/** Sets everything that belongs to one match back to zero (server). */
	void ResetMatchStats();

	/** Server: counts a kill for the multi-kill window and the streaks. Returns the new multi-kill count. */
	int32 RegisterKill(float Now, float MultiKillWindow);

	/** Server: counts a death (streak and multi-kill end). */
	void RegisterDeath();

	/**
	 * Called by the rifle on the server for every shot. Counts the shot and returns false when shooting is
	 * not allowed right now (countdown before the match, results screen), so the shot must be dropped.
	 */
	static bool RegisterShot(const APawn* Shooter);

	/** Called by the rifle on the server when a shot hit a player. */
	static void RegisterHit(const APawn* Shooter);

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
