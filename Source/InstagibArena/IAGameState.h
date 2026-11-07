// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameState.h"
#include "IAGameState.generated.h"

UENUM(BlueprintType)
enum class EIAGameType : uint8
{
	FreeForAll,
	TeamDeathmatch
};

UCLASS()
class INSTAGIBARENA_API AIAGameState : public AGameState
{
	GENERATED_BODY()

public:
	AIAGameState();

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	EIAGameType GameType = EIAGameType::FreeForAll;

	/** 0 = no score limit. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	int32 ScoreLimit = 0;

	/** 0 = no time limit. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	int32 TimeLimitSeconds = 0;

	/** Seconds left when a time limit is set, otherwise seconds elapsed. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	int32 ClockSeconds = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	int32 RedScore = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	int32 BlueScore = 0;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	bool bMatchOver = false;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	FString WinnerText;

	bool IsTeamGame() const { return GameType == EIAGameType::TeamDeathmatch; }

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
