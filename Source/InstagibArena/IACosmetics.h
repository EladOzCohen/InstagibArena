// Instagib Arena
#pragma once

#include "CoreMinimal.h"
#include "IACosmetics.generated.h"

/**
 * Everything a player can choose to change the LOOK of the rifle, the beam and the kill, plus the card shown next to the name.
 * Pure appearance: no field changes damage, fire rate, hit boxes or movement. Small enough to replicate in the player state.
 * Reward ids (see docs/REWARDS_DESIGN.md, section 5): the ids G1..G12, K1..K6, C1..C8 ... gate what a player may pick.
 */
USTRUCT(BlueprintType)
struct INSTAGIBARENA_API FIACosmeticLoadout
{
	GENERATED_BODY()

	/** Beam: when bCustomBeamColor is false the beam uses the character's accent colour (the default). */
	UPROPERTY(BlueprintReadWrite) bool bCustomBeamColor = false;
	UPROPERTY(BlueprintReadWrite) FColor BeamColor = FColor(255, 255, 255, 255);
	/** 0 default, 1 Needle (thin), 2 Lance (thick), 3 Pulse (dashed), 4 Confetti (rainbow, a joke reward). */
	UPROPERTY(BlueprintReadWrite) uint8 BeamStyle = 0;

	/** Rifle colours: when bCustomRifle is false the rifle follows the character (the default). */
	UPROPERTY(BlueprintReadWrite) bool bCustomRifle = false;
	UPROPERTY(BlueprintReadWrite) FColor RifleBody = FColor(40, 40, 46, 255);
	UPROPERTY(BlueprintReadWrite) FColor RifleAccent = FColor(255, 160, 30, 255);
	UPROPERTY(BlueprintReadWrite) FColor RifleCore = FColor(255, 160, 30, 255);
	/** 0 default, 1 matt, 2 polished steel, 3 brushed brass, 4 gold (Master Gunsmith). */
	UPROPERTY(BlueprintReadWrite) uint8 RifleFinish = 0;

	/** Parts (looks only): 0 = standard. Barrel 1 short, 2 long, 3 twin, 4 flag pennant. Stock 1..3. Fins 1 plain, 2 ion fins. */
	UPROPERTY(BlueprintReadWrite) uint8 Barrel = 0;
	UPROPERTY(BlueprintReadWrite) uint8 Stock = 0;
	UPROPERTY(BlueprintReadWrite) uint8 Fins = 0;
	/** 0 none, 1 tiny hat, 2 rubber duck, 3 tiny cow. */
	UPROPERTY(BlueprintReadWrite) uint8 Charm = 0;
	/** Faction rifle livery: 0 none, 1 Rustborn, 2 Legion, 3 Syndicate, 4 Void Corps, 5 Hollow Court, 6 Obsidian (Apex+). */
	UPROPERTY(BlueprintReadWrite) uint8 RifleLivery = 0;
	/** Show the lifetime kill counter ring on the rifle (needs reward G6). */
	UPROPERTY(BlueprintReadWrite) bool bKillCounter = false;
	UPROPERTY(BlueprintReadWrite) int32 KillCounterValue = 0;

	/** Kill effect: 0 default, 1 Ash, 2 Gold Shatter, 3 Frost, 4 Glitch, 5 Ember, 6 Poof (joke). */
	UPROPERTY(BlueprintReadWrite) uint8 KillEffect = 0;

	/** Character colour variant: 0 standard, 1 Veteran, 2 Elite, 3 Obsidian. */
	UPROPERTY(BlueprintReadWrite) uint8 CharacterVariant = 0;

	/** The card: rank 0..6 (Recruit..Apex) and the chosen title id (0 none, see IARewardData.h). */
	UPROPERTY(BlueprintReadWrite) uint8 Rank = 0;
	UPROPERTY(BlueprintReadWrite) int32 TitleId = 0;

	/** Text form for the save file and back (all fields; unknown or missing values keep their defaults). */
	FString ToString() const;
	void FromString(const FString& Text);
};
