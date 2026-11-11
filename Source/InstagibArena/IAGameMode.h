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
 *
 * A match goes through three phases (AIAGameState::Phase), all decided here on the server:
 *   Warmup  a short countdown: players can move but not fire, bots wait.
 *   Live    the fight: scores, medals, the clock.
 *   Ended   the results screen. After RestartDelay seconds (or when the host asks) a new match starts
 *           in place: no map reload, so listen servers and clients stay connected.
 * The engine's own match state stays "in progress" the whole time.
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

	/** Picks the spawn point where a new arrival is least likely to be shot at once. */
	virtual AActor* ChoosePlayerStart_Implementation(AController* Player) override;

	/** Called on the server when a player is killed. Killer may be null or equal to the victim. */
	void OnPlayerKilled(AController* Killer, AController* Victim);

	/** Ends the results screen at once and begins the next match (host or standalone player). */
	void StartNewMatch();

	/** Seconds before a dead player respawns. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Match")
	float RespawnDelay = 2.f;

	/** Seconds of the results screen before the next match starts by itself. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Match")
	float RestartDelay = 20.f;

	/** Seconds of the countdown before a match. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Match")
	float WarmupSeconds = 5.f;

	/** Kills closer together than this count as a multi kill. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Match")
	float MultiKillWindow = 4.f;

	int32 GetBotCount() const { return BotCount; }
	int32 GetBotSkill() const { return BotSkill; }

protected:
	void SpawnBots();
	void AssignTeam(AIAPlayerState* PlayerState);
	void BeginWarmup();
	void StartLive();
	void TickClock();
	void CheckScoreLimit();
	void FinishMatch(const FString& WinnerText, int32 WinnerPlayerId, uint8 WinnerTeam);
	void DetermineWinnerByScore();
	void ScheduleRespawn(AController* Victim, float Delay);

	// ---- announcements
	void AnnounceKillMedals(AIAPlayerState* Killer, int32 MultiKillCount);
	void UpdateLeadStates();
	void CheckFragsLeft();

	EIAGameType GameType = EIAGameType::FreeForAll;
	int32 ScoreLimit = 25;
	int32 TimeLimitMinutes = 0;
	int32 BotCount = 0;
	int32 BotSkill = 1;

	FTimerHandle ClockTimer;
	FTimerHandle WarmupTimer;
	FTimerHandle RestartTimer;
	bool bBotsSpawned = false;

	/** Raised for every new match, so that timers of the previous one can recognise that they are stale. */
	int32 MatchGeneration = 0;
	int32 NextSlotId = 1;
	bool bFirstBloodDone = false;
	int32 LastFragsLeft = 0;
	uint8 TeamLead[2] = { 0, 0 };

	/** When each spawn point was used last, so that two arrivals do not take the same one in a row. */
	TMap<TWeakObjectPtr<AActor>, float> StartLastUse;

#if !UE_BUILD_SHIPPING
	void SetupDevHooks();
	FTimerHandle DevTimer;
#endif
};
