// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameMode.h"
#include "IAGameState.h"
#include "IAGameMode.generated.h"

class AIAPlayerState;
class AIAFlag;
class AIAFlagBase;
class AIAPlayerCharacter;
class APlayerStart;

/**
 * Free for all, team deathmatch and capture the flag with score limit, time limit or both.
 *
 * Options are read from the travel URL, for example:
 *   /Game/Maps/Foundry?Mode=TDM?ScoreLimit=30?TimeLimit=10?Bots=6?BotSkill=2
 *     Mode       FFA (default), TDM or CTF
 *     ScoreLimit kills needed to win (CTF: captures needed), 0 = none
 *     TimeLimit  minutes, 0 = none
 *     Bots       2..10, 0 = no bots, 4 if not given
 *     BotSkill   0 rookie, 1 beginner, 2 casual, 3 intermediate (default), 4 advanced, 5 expert, 6 master
 * If neither limit is given the score limit defaults to 25 (CTF: 5 captures and 15 minutes; with only ScoreLimit
 * given CTF also gets the 15 minutes, with only TimeLimit given it gets the 5 captures).
 *
 * Capture the flag: two teams, each flag stands on its AIAFlagBase. An enemy touching a flag that is at home or dropped
 * takes it. The carrier scores a capture by touching his own base while his own flag is at home. A team mate touching
 * his own dropped flag returns it; a dropped flag also goes home by itself after FlagReturnSeconds. A carrier who dies
 * (or falls out of the world) drops the flag where he died. At the time limit the team with more captures wins.
 * Maps without AIAFlagBase actors get two bases made by CreateFallbackBases.
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
	virtual void Logout(AController* Exiting) override;
	virtual void Tick(float DeltaSeconds) override;

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

	/** Seconds after a spawn (and at the start of the fight) during which shots pass through the new body. Shooting ends it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Match")
	float SpawnProtectSeconds = 1.5f;

	/** Ends the spawn protection of this pawn now (server). Safe to call for any pawn. */
	void EndSpawnProtection(APawn* Pawn);

	/** Capture the flag: seconds until a dropped flag goes home by itself. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CTF")
	float FlagReturnSeconds = 15.f;

	/** Capture the flag: how close (cm, on the ground plane) a player must come to a flag to take or return it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CTF")
	float FlagTouchRadius = 130.f;

	int32 GetBotCount() const { return BotCount; }
	int32 GetBotSkill() const { return BotSkill; }
	bool IsCTF() const { return GameType == EIAGameType::CaptureTheFlag; }

protected:
	virtual void FinishRestartPlayer(AController* NewPlayer, const FRotator& StartRotation) override;
	void BeginSpawnProtection(APawn* Pawn);

	struct FProtection
	{
		TEnumAsByte<ECollisionResponse> CapsuleResponse = ECR_Block;
		TEnumAsByte<ECollisionResponse> MeshResponse = ECR_Ignore;
	};
	TMap<TWeakObjectPtr<APawn>, FProtection> Protected;

	void SpawnBots();
	void AssignTeam(AIAPlayerState* PlayerState);
	void BeginWarmup();
	void StartLive();
	void TickClock();
	void CheckScoreLimit();
	void FinishMatch(const FString& WinnerText, int32 WinnerPlayerId, uint8 WinnerTeam);
	void DetermineWinnerByScore();
	void ScheduleRespawn(AController* Victim, float Delay);

	// ---- capture the flag
	void SetupCTF();
	void ResetFlags();
	void TickFlags();
	void CreateFallbackBases();
	bool FindFlatSpot(const FVector& Around, float FloorZ, FVector& OutSpot) const;
	void SpawnBaseActor(uint8 Team, const FVector& Location, bool bFallback);
	void HandleFlagCarrierDeath(AController* Killer, AController* Victim);
	void DropFlag(AIAFlag* Flag, const FVector& Where, AIAPlayerState* ExCarrier);
	void ReturnFlag(AIAFlag* Flag, AIAPlayerState* Returner);
	void PickUpFlag(AIAFlag* Flag, AIAPlayerCharacter* Taker);
	void CaptureFlag(AIAFlag* Flag, AIAPlayerCharacter* Carrier);
	uint8 GetStartTeam(const APlayerStart* Start) const;

	TWeakObjectPtr<AIAFlag> Flags[2];
	TWeakObjectPtr<AIAFlagBase> Bases[2];
	bool bCtfSetUp = false;
	bool bDevDemoCarrier = false;   // development only: -IACtfCarryDemo

	/** Maps without start tags: which team each start was given to by the fallback (nearest base). */
	TMap<TWeakObjectPtr<const APlayerStart>, uint8> FallbackStartTeam;

	// ---- announcements
	void AnnounceKillMedals(AIAPlayerState* Killer, int32 MultiKillCount);
	void UpdateLeadStates();
	void CheckFragsLeft();

	EIAGameType GameType = EIAGameType::FreeForAll;
	int32 ScoreLimit = 25;
	int32 TimeLimitMinutes = 0;
	int32 BotCount = 0;
	int32 BotSkill = 3;

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
