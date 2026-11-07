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

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
