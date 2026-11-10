// Instagib Arena

#include "IAPlayerState.h"
#include "IAGameState.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Net/UnrealNetwork.h"

AIAPlayerState::AIAPlayerState()
{
	SetNetUpdateFrequency(10.f);
}

void AIAPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(AIAPlayerState, Kills);
	DOREPLIFETIME(AIAPlayerState, Deaths);
	DOREPLIFETIME(AIAPlayerState, Team);
	DOREPLIFETIME(AIAPlayerState, bIsBotPlayer);
	DOREPLIFETIME(AIAPlayerState, CharacterIndex);
	DOREPLIFETIME(AIAPlayerState, ShotsFired);
	DOREPLIFETIME(AIAPlayerState, ShotsHit);
	DOREPLIFETIME(AIAPlayerState, Streak);
	DOREPLIFETIME(AIAPlayerState, BestStreak);
	DOREPLIFETIME(AIAPlayerState, MultiKill);
}

void AIAPlayerState::ResetMatchStats()
{
	Kills = 0;
	Deaths = 0;
	ShotsFired = 0;
	ShotsHit = 0;
	Streak = 0;
	BestStreak = 0;
	MultiKill = 0;
	LastKillTime = -100.f;
	LeadState = 0;
}

int32 AIAPlayerState::RegisterKill(float Now, float MultiKillWindow)
{
	MultiKill = (Now - LastKillTime <= MultiKillWindow) ? MultiKill + 1 : 1;
	LastKillTime = Now;
	++Streak;
	BestStreak = FMath::Max(BestStreak, Streak);
	return MultiKill;
}

void AIAPlayerState::RegisterDeath()
{
	Streak = 0;
	MultiKill = 0;
	LastKillTime = -100.f;
}

bool AIAPlayerState::RegisterShot(const APawn* Shooter)
{
	const UWorld* World = Shooter ? Shooter->GetWorld() : nullptr;
	if (const AIAGameState* GS = World ? World->GetGameState<AIAGameState>() : nullptr)
	{
		if (!GS->IsFiringAllowed())
		{
			return false;
		}
	}
	if (AIAPlayerState* PS = Shooter ? Shooter->GetPlayerState<AIAPlayerState>() : nullptr)
	{
		++PS->ShotsFired;
	}
	return true;
}

void AIAPlayerState::RegisterHit(const APawn* Shooter)
{
	if (AIAPlayerState* PS = Shooter ? Shooter->GetPlayerState<AIAPlayerState>() : nullptr)
	{
		++PS->ShotsHit;
	}
}
