// Instagib Arena
#pragma once

#include "CoreMinimal.h"
#include "IACosmetics.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "IAProfileSubsystem.generated.h"

/**
 * The player's long-term profile: lifetime stat counters, the rewards unlocked so far, and the chosen cosmetic loadout.
 * Saved in GameUserSettings.ini (section InstagibArena.Profile) like the campaign. See docs/REWARDS_DESIGN.md.
 * Reward ids are short names: "G1".."G12" gunsmith, "K1".."K6" kill effects, "C1".."C8" characters, "P1".. card, "M1".. maps, "R1".. rules, "A1".. audio.
 */
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

private:
	void Load();

	TMap<FName, int64> Stats;
	TSet<FName> Unlocked;
	TArray<FName> NewUnlocks;
	FIACosmeticLoadout Loadout;
	bool bUnlockAll = false;
};
