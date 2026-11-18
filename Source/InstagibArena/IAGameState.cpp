// Instagib Arena

#include "IAGameState.h"
#include "IAPlayerState.h"
#include "IAMapVariant.h"
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
	DOREPLIFETIME(AIAGameState, Wave);
	DOREPLIFETIME(AIAGameState, WaveEnemiesLeft);
	DOREPLIFETIME(AIAGameState, Mutators);
	DOREPLIFETIME(AIAGameState, MapVariant);
	DOREPLIFETIME(AIAGameState, HeatLevel);
}

void AIAGameState::BeginPlay()
{
	Super::BeginPlay();
	// The server set the variant before this; a client may get it here or later in OnRep_MapVariant.
	IAMapVariant::Apply(GetWorld(), MapVariant);
}

void AIAGameState::OnRep_MapVariant()
{
	IAMapVariant::Apply(GetWorld(), MapVariant);
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
		if (State->SlotId == KillerId)
		{
			Entry.KillerName = State->GetPlayerName();
			Entry.KillerTeam = State->Team;
		}
		if (State->SlotId == VictimId)
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

void AIAGameState::MulticastFlagEvent_Implementation(EIAFlagEvent Kind, int32 Subject, uint8 FlagTeam)
{
	if (GetNetMode() == NM_DedicatedServer)
	{
		return;
	}

	const AIAPlayerState* Who = nullptr;
	for (APlayerState* PS : PlayerArray)
	{
		const AIAPlayerState* State = Cast<AIAPlayerState>(PS);
		if (State && State->SlotId == Subject)
		{
			Who = State;
		}
	}

	// A row in the kill feed.
	FIAFeedEntry Entry;
	Entry.bFlagEvent = true;
	Entry.FlagTeam = FlagTeam;
	Entry.Time = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	Entry.VictimId = Subject;
	Entry.VictimName = Who ? Who->GetPlayerName() : FString();
	Entry.VictimTeam = Who ? Who->Team : IA_NoTeam;
	const TCHAR* FlagName = FlagTeam == 0 ? TEXT("red") : TEXT("blue");
	switch (Kind)
	{
	case EIAFlagEvent::Taken:    Entry.EventText = FString::Printf(TEXT("took the %s flag"), FlagName); break;
	case EIAFlagEvent::Dropped:  Entry.EventText = FString::Printf(TEXT("dropped the %s flag"), FlagName); break;
	case EIAFlagEvent::Returned: Entry.EventText = FString::Printf(TEXT("returned the %s flag"), FlagName); break;
	case EIAFlagEvent::Captured: Entry.EventText = FString::Printf(TEXT("captured the %s flag"), FlagName); break;
	}
	if (Entry.VictimName.IsEmpty())
	{
		// Nobody to name (the flag went home by itself).
		Entry.VictimName = FlagTeam == 0 ? TEXT("The red flag") : TEXT("The blue flag");
		Entry.VictimTeam = FlagTeam;
		Entry.EventText = TEXT("is back at its base");
	}
	KillFeed.Add(Entry);
	if (KillFeed.Num() > 8)
	{
		KillFeed.RemoveAt(0, KillFeed.Num() - 8);
	}

	OnFlagEvent.Broadcast(Kind, Subject, FlagTeam);
}

void AIAGameState::MulticastAnnounce_Implementation(EIAAnnounce Kind, int32 Subject, int32 Param)
{
	if (GetNetMode() != NM_DedicatedServer)
	{
		OnAnnounce.Broadcast(Kind, Subject, Param);
	}
}
