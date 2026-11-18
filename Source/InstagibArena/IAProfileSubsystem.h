// Instagib Arena
#pragma once

#include "CoreMinimal.h"
#include "IACosmetics.h"
#include "IAMatchSummary.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "IARewardData.h"
#include "IAProfileSubsystem.generated.h"

/**
 * The player's long-term profile: lifetime stat counters, the rewards unlocked so far, and the chosen cosmetic loadout.
 * Saved in GameUserSettings.ini (section InstagibArena.Profile) like the campaign. See docs/REWARDS_DESIGN.md.
 * Reward ids are short names: "G1".."G12" gunsmith, "K1".."K6" kill effects, "C1".."C8" characters, "P1".. card, "M1".. maps, "R1".. rules, "A1".. audio.
 */
class UIACampaignSubsystem;

/** What the last finished match gave the player (shown on the results screen). */
struct FIAMatchGain
{
	bool bCounted = false;           // false: the match was too short and did not count
	int32 AP = 0;                    // apex points gained
	int32 RankBefore = 0;
	int32 RankAfter = 0;
	TArray<FName> NewRewards;
	TArray<FString> NewMedals;       // "Slayer: Bronze"
	FString Note;
	int32 CountedKills = 0;
};

UCLASS()
class INSTAGIBARENA_API UIAProfileSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	static UIAProfileSubsystem* Get(const UObject* WorldContext);

	// ---- stat counters (lifetime)
	int64 GetStat(FName Stat) const;
	void AddStat(FName Stat, int64 Amount = 1);
	void SetStatMax(FName Stat, int64 Value);

	// ---- unlocks
	/** True when the reward is unlocked. Always true with -IAUnlockAll (development). */
	bool IsUnlocked(FName RewardId) const;
	/** Unlocks a reward; returns true when it was new (it is then also queued for the "New!" list). */
	bool Unlock(FName RewardId);
	/** The rewards unlocked since the last call (for the results screen). */
	TArray<FName> ConsumeNewUnlocks();

	// ---- loadout
	const FIACosmeticLoadout& GetLoadout() const { return Loadout; }
	void SetLoadout(const FIACosmeticLoadout& NewLoadout);

	void Save() const;

	// ---- match accounting (rules: docs/REWARDS_DESIGN.md section 11)
	/** A match goes live: forget what was collected in a match that was not finished. */
	void BeginMatch();
	/** A kill by the local player. Value: the weight of the victim (human 1, bot by skill), bSkilled: human or a bot of skill 3+. */
	void RecordKill(float Value, bool bSkilled, float DistanceCm, bool bAirborne);
	/** The match ended normally: commit the collected numbers, evaluate rewards. */
	void ApplyMatch(const FIAMatchSummary& Summary);
	const FIAMatchGain& GetLastGain() const { return LastGain; }
	/** The campaign state changed (a match was recorded, an ending chosen): unlock chapter and ending rewards. */
	void OnCampaignChanged(const UIACampaignSubsystem& Camp);
	/** Unlocks every stat reward whose counter is high enough, and medal tiers. Called after every change. */
	void EvaluateRewards();
	/** Forgets everything (the settings button). */
	void ResetProfile();

	// ---- queries for the menus
	int64 GetAP() const { return GetStat("AP"); }
	int32 GetRank() const;
	/** 0 = none, 1..5 = Rust..Obsidian. */
	int32 GetMedalTier(int32 MedalIndex) const;
	/** 0..1 progress of a stat reward (1 for an unlocked one). */
	float GetProgress(const struct IAReward::FReward& Reward) const;
	/** Is the look available: the first 37 always, the others when unlocked. */
	bool IsLookUnlocked(int32 Look) const;

private:
	void Load();

	TMap<FName, int64> Stats;
	TSet<FName> Unlocked;
	TArray<FName> NewUnlocks;
	FIACosmeticLoadout Loadout;
	bool bUnlockAll = false;

	// Collected in the running match, committed by ApplyMatch.
	struct FPending
	{
		float CountedValue = 0.f;
		int32 Raw = 0;
		int32 Air = 0;
		int32 Long = 0;
		float AP = 0.f;
	};
	FPending Pending;
	FIAMatchGain LastGain;
};
