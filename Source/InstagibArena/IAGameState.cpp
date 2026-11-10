// Instagib Arena

#include "IAGameState.h"
#include "IAPlayerState.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"

AIAGameState::AIAGameState()
{
}

void AIAGameState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(AIAGameState, GameType);
	DOREPLIFETIME(AIAGameState, ScoreLimit);
	DOREPLIFETIME(AIAGameState, TimeLimitSeconds);
	DOREPLIFETIME(AIAGameState, ClockSeconds);
	DOREPLIFETIME(AIAGameState, RedScore);
	DOREPLIFETIME(AIAGameState, BlueScore);
	DOREPLIFETIME(AIAGameState, bMatchOver);
	DOREPLIFETIME(AIAGameState, WinnerText);
	DOREPLIFETIME(AIAGameState, Phase);
	DOREPLIFETIME(AIAGameState, PhaseEndTime);
	DOREPLIFETIME(AIAGameState, WinnerPlayerId);
	DOREPLIFETIME(AIAGameState, WinnerTeam);
}

float AIAGameState::GetPhaseSecondsLeft() const
{
	return FMath::Max(0.f, PhaseEndTime - GetServerWorldTimeSeconds());
}

void AIAGameState::MulticastKillFeed_Implementation(int32 KillerId, int32 VictimId)
{
	if (GetNetMode() == NM_DedicatedServer)
	{
		return;
	}

	FIAFeedEntry Entry;
	Entry.KillerId = KillerId;
	Entry.VictimId = VictimId;
	Entry.bFell = KillerId < 0;
	Entry.bSuicide = KillerId == VictimId;
	Entry.Time = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	for (APlayerState* PS : PlayerArray)
	{
		const AIAPlayerState* State = Cast<AIAPlayerState>(PS);
		if (!State)
		{
			continue;
		}
		if (State->GetPlayerId() == KillerId)
		{
			Entry.KillerName = State->GetPlayerName();
			Entry.KillerTeam = State->Team;
		}
		if (State->GetPlayerId() == VictimId)
		{
			Entry.VictimName = State->GetPlayerName();
			Entry.VictimTeam = State->Team;
		}
	}
	if (Entry.VictimName.IsEmpty())
	{
		return;
	}

	KillFeed.Add(Entry);
	if (KillFeed.Num() > 8)
	{
		KillFeed.RemoveAt(0, KillFeed.Num() - 8);
	}
}

void AIAGameState::MulticastAnnounce_Implementation(EIAAnnounce Kind, int32 Subject, int32 Param)
{
	if (GetNetMode() != NM_DedicatedServer)
	{
		OnAnnounce.Broadcast(Kind, Subject, Param);
	}
}
