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

/** Where a match is: a countdown before it, the fight itself, the results screen after it. */
UENUM(BlueprintType)
enum class EIAMatchPhase : uint8
{
	Warmup,
	Live,
	Ended
};

/** Announcements the server sends to every machine. The HUD turns them into banners and sounds. */
UENUM(BlueprintType)
enum class EIAAnnounce : uint8
{
	FirstBlood,
	DoubleKill,
	MultiKill,
	UltraKill,
	MonsterKill,
	KillingSpree,
	Rampage,
	Dominating,
	Unstoppable,
	GodLike,
	TookLead,
	LostLead,
	TiedLead,
	FragsLeft
};

/** One line of the kill feed, kept on each machine for a few seconds. */
struct FIAFeedEntry
{
	FString KillerName;
	FString VictimName;
	int32 KillerId = -1;
	int32 VictimId = -1;
	uint8 KillerTeam = 255;
	uint8 VictimTeam = 255;
	bool bSuicide = false;
	bool bFell = false;   // fell out of the world, nobody to blame
	float Time = 0.f;
};

DECLARE_MULTICAST_DELEGATE_ThreeParams(FIAAnnounceDelegate, EIAAnnounce /*Kind*/, int32 /*SubjectPlayerId or team*/, int32 /*Param*/);

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

	/** True once the match is decided (the same moment the phase becomes Ended). */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	bool bMatchOver = false;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	FString WinnerText;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	EIAMatchPhase Phase = EIAMatchPhase::Warmup;

	/** Server time at which the warmup ends (Warmup) or the next match begins (Ended). Compare with GetServerWorldTimeSeconds(). */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	float PhaseEndTime = 0.f;

	/** PlayerId of the winner in free for all, -1 when there is none (team game or draw). */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	int32 WinnerPlayerId = -1;

	/** Winning team in a team game, 255 when there is none. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Match")
	uint8 WinnerTeam = 255;

	bool IsTeamGame() const { return GameType == EIAGameType::TeamDeathmatch; }

	/** False during the countdown and the results screen. */
	bool IsFiringAllowed() const { return Phase == EIAMatchPhase::Live; }

	/** Seconds until PhaseEndTime, never negative. */
	float GetPhaseSecondsLeft() const;

	/** The server tells every machine about a kill. Players are named by PlayerId; -1 = nobody (fell out of the world). */
	UFUNCTION(NetMulticast, Reliable)
	void MulticastKillFeed(int32 KillerId, int32 VictimId);

	/** The server announces a medal, a lead change or a frag warning. */
	UFUNCTION(NetMulticast, Reliable)
	void MulticastAnnounce(EIAAnnounce Kind, int32 Subject, int32 Param);

	/** The newest entries last. Filled on every machine, used by the HUD. */
	const TArray<FIAFeedEntry>& GetKillFeed() const { return KillFeed; }
	void ClearKillFeed() { KillFeed.Reset(); }

	/** The HUD listens here. */
	FIAAnnounceDelegate OnAnnounce;

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
	TArray<FIAFeedEntry> KillFeed;
};
