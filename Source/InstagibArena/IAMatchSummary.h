// Instagib Arena
#pragma once

#include "CoreMinimal.h"
#include "IAMatchSummary.generated.h"

/** What the server tells a human player when a match ends: the numbers the rewards system needs (see IAProfileSubsystem::ApplyMatch). */
USTRUCT()
struct FIAMatchSummary
{
	GENERATED_BODY()

	UPROPERTY() uint8 GameType = 0;             // EIAGameType
	UPROPERTY() FString MapName;                // "Foundry" (without the DM- prefix)
	UPROPERTY() bool bWon = false;
	UPROPERTY() float DurationSec = 0.f;
	UPROPERTY() int32 Opponents = 0;            // players on the other side(s)
	UPROPERTY() bool bHumanOpponents = false;   // at least one opponent is a human
	UPROPERTY() int32 BotSkill = 3;             // 0 rookie .. 6 master
	UPROPERTY() int32 Kills = 0;
	UPROPERTY() int32 Deaths = 0;
	UPROPERTY() int32 ShotsFired = 0;
	UPROPERTY() int32 ShotsHit = 0;
	UPROPERTY() int32 Captures = 0;
	UPROPERTY() int32 Returns = 0;
	UPROPERTY() int32 FlagKills = 0;
	UPROPERTY() int32 BestStreak = 0;
	UPROPERTY() int32 Wave = 0;                 // survival: the wave reached
	UPROPERTY() int32 CampaignMatch = -1;       // 0..19 in the campaign, -1 otherwise
};
