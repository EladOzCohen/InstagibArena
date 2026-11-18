// Instagib Arena
#pragma once

#include "CoreMinimal.h"
#include "IACosmetics.h"

class UIAProfileSubsystem;

/**
 * Everything about the cosmetic loadout that is not the struct itself: the option names shown in the Gunsmith, which reward unlocks
 * which option (docs/REWARDS_DESIGN.md sections 5.1, 5.2, 5.3, 5.5), the text that tells the player what is still needed, the clean-up
 * of values that arrive over the network, the random looks of the bots and the development overrides.
 */
namespace IALoadout
{
	/** One group of choices in the loadout (one row of the Gunsmith). */
	enum class EField : uint8
	{
		BeamStyle,
		RifleFinish,
		Barrel,
		Stock,
		Fins,
		Charm,
		RifleLivery,
		KillEffect,
		CharacterVariant,
		Count
	};

	/** Number of values of a field (value 0 is always the standard look). */
	INSTAGIBARENA_API int32 OptionCount(EField Field);

	/** The name of one value, as the Gunsmith shows it ("Needle", "Rubber duck"). */
	INSTAGIBARENA_API FText OptionName(EField Field, int32 Value);

	/** The reward that unlocks a value (NAME_None = always available). */
	INSTAGIBARENA_API FName RequiredReward(EField Field, int32 Value);

	/** What the player has to do for a reward ("500 kills", "Skybound Silver medal"). */
	INSTAGIBARENA_API FText RequirementText(FName RewardId);

	/** Reads or writes one field of a loadout as a number. */
	INSTAGIBARENA_API int32 GetField(const FIACosmeticLoadout& Loadout, EField Field);
	INSTAGIBARENA_API void SetField(FIACosmeticLoadout& Loadout, EField Field, int32 Value);

	/** The six beam colours of reward G1 and the gold of G7 (sRGB). */
	INSTAGIBARENA_API const TArray<FColor>& BeamPresets();
	INSTAGIBARENA_API FColor GoldBeam();

	/** Rewards for the switches that are not one of the fields above. */
	inline const FName RewardBeamColor = TEXT("G1");
	inline const FName RewardCustomRifle = TEXT("G4");   // the Gunsmith proper: free colours and the two saved slots
	inline const FName RewardKillCounter = TEXT("G6");
	inline const FName RewardGold = TEXT("G7");

	/** Keeps every value inside its range (values come from other machines and from the save file). */
	INSTAGIBARENA_API void Clamp(FIACosmeticLoadout& Loadout);

	/** Resets everything the profile has not unlocked to the standard look. */
	INSTAGIBARENA_API void RemoveLocked(FIACosmeticLoadout& Loadout, const UIAProfileSubsystem* Profile);

	/** The lifetime kill count shown by the kill counter (profile stat "Kills"). */
	INSTAGIBARENA_API int32 LifetimeKills(const UIAProfileSubsystem* Profile);

	/** A random, cheap look for a bot: most bots get one or two things, a few get nothing. Same seed, same look. */
	INSTAGIBARENA_API FIACosmeticLoadout MakeBotLoadout(int32 Seed);

	/**
	 * Development only (empty in shipping builds): -IALoadout="ke=2,bs=3,..." replaces the local player's loadout and the loadout of the
	 * screenshot dummies; -IABotLoadout="..." the loadout of every bot. Same text as FIACosmeticLoadout::ToString, plus "kv=N" for the
	 * kill counter value. Returns false when the option is not given.
	 */
	INSTAGIBARENA_API bool GetDevOverride(const TCHAR* Param, FIACosmeticLoadout& OutLoadout);

	/** The loadout text plus the kill counter value, for the log ("LOADOUT name: ..."). */
	INSTAGIBARENA_API FString Describe(const FIACosmeticLoadout& Loadout);
}
