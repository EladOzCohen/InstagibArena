// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameMode.h"
#include "IAGameState.h"
#include "IAGameMode.generated.h"

class AIAPlayerState;

/**
 * Free for all and team deathmatch with score limit, time limit or both.
 *
 * Options are read from the travel URL, for example:
 *   /Game/Maps/Foundry?Mode=TDM?ScoreLimit=30?TimeLimit=10?Bots=6?BotSkill=2
 *     Mode       FFA (default) or TDM
 *     ScoreLimit kills needed to win, 0 = none
 *     TimeLimit  minutes, 0 = none
 *     Bots       2..10, 0 = no bots, 4 if not given
 *     BotSkill   0 = beginner, 1 = intermediate, 2 = expert
 * If neither limit is given the score limit defaults to 25.
 */
UCLASS()
class INSTAGIBARENA_API AIAGameMode : public AGameMode
{
	GENERATED_BODY()

public:
	AIAGameMode();

	virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
	virtual void InitGameState() override;
	virtual void HandleMatchHasStarted() override;
	virtual void PostLogin(APlayerController* NewPlayer) override;
	virtual FString InitNewPlayer(APlayerController* NewPlayerController, const FUniqueNetIdRepl& UniqueId, const FString& Options, const FString& Portal = TEXT("")) override;

	/** Called on the server when a player is killed. Killer may be null or equal to the victim. */
	void OnPlayerKilled(AController* Killer, AController* Victim);

	/** Seconds before a dead player respawns. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Match")
	float RespawnDelay = 2.f;

	/** Seconds between the end of a match and the automatic restart. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Match")
	float RestartDelay = 10.f;

	int32 GetBotCount() const { return BotCount; }
	int32 GetBotSkill() const { return BotSkill; }

protected:
	void SpawnBots();
	void AssignTeam(AIAPlayerState* PlayerState);
	void TickClock();
	void CheckScoreLimit();
	void FinishMatch(const FString& WinnerText);
	void DetermineWinnerByScore();

	EIAGameType GameType = EIAGameType::FreeForAll;
	int32 ScoreLimit = 25;
	int32 TimeLimitMinutes = 0;
	int32 BotCount = 0;
	int32 BotSkill = 1;

	FTimerHandle ClockTimer;
	FTimerHandle RestartTimer;
	bool bBotsSpawned = false;
};
