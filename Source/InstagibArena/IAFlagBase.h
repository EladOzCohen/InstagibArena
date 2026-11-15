// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IAFlagBase.generated.h"

/**
 * CONTRACT for maps (Capture the Flag): the home of one team's flag. Maps place exactly one per team with
 * Tools/mapkit.py (unreal.IAFlagBase, property flag_team: 0 = red, 1 = blue) at the centre of the team's base, on the
 * ground. The Capture the Flag game mode spawns that team's flag here and a carrier scores by bringing the enemy flag
 * back to this base while their own flag is at home. Team spawn points are ordinary PlayerStarts with PlayerStartTag
 * "Red" or "Blue"; untagged starts are used by every mode.
 *
 * This is the placeholder of the contract (the CTF game mode agent replaces the body with the real base: pad,
 * pole, capture zone, flag spawn). The class name and the property below must not change.
 */
UCLASS()
class INSTAGIBARENA_API AIAFlagBase : public AActor
{
	GENERATED_BODY()

public:
	AIAFlagBase();

	/** 0 = red, 1 = blue (same numbers as AIAPlayerState::Team). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CTF", meta = (ClampMin = "0", ClampMax = "1"))
	uint8 FlagTeam = 0;

	/** Radius of the capture zone in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CTF")
	float CaptureRadius = 220.f;
};
