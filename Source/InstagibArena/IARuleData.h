// Instagib Arena
//
// Pure data of the game options that rewards unlock (docs/REWARDS_DESIGN.md 5.5 M1, 5.6 R1..R6):
// the mutators of a custom game, the Heat levels of the campaign (Apex+) and the times of day of the maps.
// No engine objects here: the game mode, the HUD and the menus read these tables.

#pragma once

#include "CoreMinimal.h"
#include "Misc/Paths.h"

/** Rule mutators of a custom game, as bits (AIAGameState::Mutators). URL option Mut=lowgrav,slowfinish,hardcore,endless,bigheads. */
enum class EIAMutator : uint8
{
	None       = 0,
	LowGravity = 1 << 0,   // R1
	SlowFinish = 1 << 1,   // R2
	Hardcore   = 1 << 2,   // R3
	Endless    = 1 << 3,   // R4 (survival without a wave limit)
	BigHeads   = 1 << 4,   // R6
};

/** One rule of the custom game menu. */
struct FIARuleInfo
{
	const TCHAR* RewardId;      // the unlock that gates it (UIAProfileSubsystem::IsUnlocked)
	const TCHAR* UrlKey;        // its name in Mut=
	EIAMutator Flag;
	const TCHAR* Name;
	const TCHAR* Description;
	const TCHAR* Requirement;   // shown while it is locked
};

namespace IARules
{
	inline const FIARuleInfo Mutators[] = {
		{ TEXT("R1"), TEXT("lowgrav"),    EIAMutator::LowGravity, TEXT("Low Gravity"),
		  TEXT("Everybody jumps higher and falls slower."),                                  TEXT("25 kills in the air") },
		{ TEXT("R2"), TEXT("slowfinish"), EIAMutator::SlowFinish, TEXT("Slow Finish"),
		  TEXT("The winning kill plays in slow motion."),                                     TEXT("25 wins") },
		{ TEXT("R3"), TEXT("hardcore"),   EIAMutator::Hardcore,   TEXT("Hardcore"),
		  TEXT("No HUD: a tiny crosshair, the scoreboard on Tab, nothing else."),            TEXT("50 wins") },
		{ TEXT("R4"), TEXT("endless"),    EIAMutator::Endless,    TEXT("Endless Survival"),
		  TEXT("Survival without a wave limit: how far can you get? Replaces the game type."), TEXT("Reach wave 10 in Survival") },
		{ TEXT("R6"), TEXT("bigheads"),   EIAMutator::BigHeads,   TEXT("Big Heads"),
		  TEXT("Huge heads. Looks only: the hit boxes stay the same."),                       TEXT("50 matches played") },
	};
	inline constexpr int32 MutatorCount = UE_ARRAY_COUNT(Mutators);

	/** Values of the mutators. */
	inline constexpr float LowGravityScale = 0.55f;      // multiplies the gravity of every character
	inline constexpr float SlowFinishDilation = 0.25f;   // global time dilation during the winning kill
	inline constexpr float SlowFinishSeconds = 2.5f;     // real seconds of slow motion before the results
	inline constexpr float BigHeadScale = 2.0f;          // scale of the head bone (third person mesh only)

	inline bool Has(uint8 Bits, EIAMutator Flag) { return (Bits & static_cast<uint8>(Flag)) != 0; }

	/** "lowgrav,bigheads" -> bits. Unknown words are ignored. */
	inline uint8 ParseMutators(const FString& Text)
	{
		TArray<FString> Words;
		Text.ParseIntoArray(Words, TEXT(","));
		uint8 Bits = 0;
		for (const FString& Word : Words)
		{
			for (const FIARuleInfo& Rule : Mutators)
			{
				if (Word.TrimStartAndEnd().Equals(Rule.UrlKey, ESearchCase::IgnoreCase))
				{
					Bits |= static_cast<uint8>(Rule.Flag);
				}
			}
		}
		return Bits;
	}

	/** Bits -> "lowgrav,bigheads" (empty for none). */
	inline FString MutatorsToString(uint8 Bits)
	{
		FString Out;
		for (const FIARuleInfo& Rule : Mutators)
		{
			if (Has(Bits, Rule.Flag))
			{
				Out += (Out.IsEmpty() ? TEXT("") : TEXT(",")) + FString(Rule.UrlKey);
			}
		}
		return Out;
	}

	// ------------------------------------------------------------------ Apex+ Heat (R5), campaign only

	inline constexpr int32 MaxHeat = 5;

	/** What each Heat level adds. The levels are cumulative: Heat 3 has the rules of 1, 2 and 3. */
	struct FHeatStep
	{
		const TCHAR* Name;
		const TCHAR* Rule;
	};
	inline const FHeatStep HeatSteps[MaxHeat] = {
		{ TEXT("Sharpened"),   TEXT("Enemy skill +1") },
		{ TEXT("Outnumbered"), TEXT("One more enemy (not in duels), your spawn protection 15% shorter") },
		{ TEXT("Coordinated"), TEXT("Enemies share what they see and hunt you together") },
		{ TEXT("Relentless"),  TEXT("Enemies respawn twice as fast (survival: waves come sooner)") },
		{ TEXT("Apex"),        TEXT("The clock: a quarter less time (8 minutes when there was no limit)") },
	};

	/** The rules of one Heat level, as the game mode applies them. */
	struct FHeatRules
	{
		int32 EnemySkillBonus = 0;
		int32 ExtraEnemies = 0;
		float PlayerProtectScale = 1.f;
		bool bCoordinated = false;
		float EnemyRespawnScale = 1.f;
		bool bTimePressure = false;
	};

	inline FHeatRules HeatRules(int32 Heat)
	{
		FHeatRules R;
		if (Heat >= 1) { R.EnemySkillBonus = 1; }
		if (Heat >= 2) { R.ExtraEnemies = 1; R.PlayerProtectScale = 0.85f; }
		if (Heat >= 3) { R.bCoordinated = true; }
		if (Heat >= 4) { R.EnemyRespawnScale = 0.5f; }
		if (Heat >= 5) { R.bTimePressure = true; }
		return R;
	}

	/** Heat 5: the time limit of a campaign match (minutes) from the normal one. */
	inline int32 HeatTimeLimit(int32 NormalMinutes)
	{
		return NormalMinutes <= 0 ? 8 : FMath::Max(3, FMath::RoundToInt(NormalMinutes * 0.75f));
	}

	/** URL option of the campaign Heat level. */
	inline const TCHAR* const HeatUrlOption = TEXT("Heat");

	// ------------------------------------------------------------------ times of day (M1)

	/** 0 day (the map as it was built), 1 dusk, 2 night. URL option Variant=dusk|night. */
	inline constexpr int32 VariantCount = 3;
	inline const TCHAR* const VariantKeys[VariantCount] = { TEXT("day"), TEXT("dusk"), TEXT("night") };
	inline const TCHAR* const VariantNames[VariantCount] = { TEXT("Day"), TEXT("Dusk"), TEXT("Night") };
	inline const TCHAR* const VariantRequirements[VariantCount] = { TEXT(""), TEXT("10 wins on this map"), TEXT("30 wins on this map") };

	inline int32 ParseVariant(const FString& Text)
	{
		for (int32 I = 0; I < VariantCount; ++I)
		{
			if (Text.Equals(VariantKeys[I], ESearchCase::IgnoreCase)) { return I; }
		}
		return 0;
	}

	/** "/Game/Maps/DM-Foundry" or "DM-Foundry" -> "Foundry". */
	inline FString MapShortName(const FString& MapPathOrName)
	{
		FString Name = FPaths::GetBaseFilename(MapPathOrName);
		Name.RemoveFromStart(TEXT("UEDPIE_0_"));
		Name.RemoveFromStart(TEXT("DM-"));
		return Name;
	}

	/** The space arenas and Quarry stay as they are (always day). */
	inline bool MapHasVariants(const FString& ShortName)
	{
		static const TCHAR* const Fixed[] = { TEXT("Orbital"), TEXT("Derelict"), TEXT("Nexus"), TEXT("Quarry") };
		for (const TCHAR* F : Fixed)
		{
			if (ShortName.Equals(F, ESearchCase::IgnoreCase)) { return false; }
		}
		return !ShortName.IsEmpty() && !ShortName.Equals(TEXT("MainMenu"), ESearchCase::IgnoreCase);
	}

	/** The reward that unlocks a time of day on a map: MV_Foundry_Dusk, MV_Foundry_Night. NAME_None for day. */
	inline FName VariantUnlockId(const FString& ShortName, int32 Variant)
	{
		if (Variant <= 0 || Variant >= VariantCount) { return NAME_None; }
		return FName(*FString::Printf(TEXT("MV_%s_%s"), *ShortName, VariantNames[Variant]));
	}
}
