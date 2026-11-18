// Instagib Arena

#include "IAPlayerState.h"
#include "IAGameMode.h"
#include "IAGameState.h"
#include "IALoadoutRules.h"
#include "InstagibArena.h"
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
	DOREPLIFETIME(AIAPlayerState, SlotId);
	DOREPLIFETIME(AIAPlayerState, SpawnProtectEndTime);
	DOREPLIFETIME(AIAPlayerState, ShotsFired);
	DOREPLIFETIME(AIAPlayerState, ShotsHit);
	DOREPLIFETIME(AIAPlayerState, Streak);
	DOREPLIFETIME(AIAPlayerState, BestStreak);
	DOREPLIFETIME(AIAPlayerState, MultiKill);
	DOREPLIFETIME(AIAPlayerState, Captures);
	DOREPLIFETIME(AIAPlayerState, Returns);
	DOREPLIFETIME(AIAPlayerState, FlagKills);
	DOREPLIFETIME(AIAPlayerState, Loadout);
}

void AIAPlayerState::SetLoadout(const FIACosmeticLoadout& NewLoadout)
{
	Loadout = NewLoadout;
	IALoadout::Clamp(Loadout);
	bHasLoadout = true;
	++LoadoutSerial;
	ForceNetUpdate();
	UE_LOG(LogInstagib, Log, TEXT("LOADOUT %s (%s, %s): %s"), *GetPlayerName(), bIsBotPlayer ? TEXT("bot") : TEXT("human"),
		GetNetMode() == NM_Client ? TEXT("client") : TEXT("server"), *IALoadout::Describe(Loadout));
}

void AIAPlayerState::OnRep_Loadout()
{
	++LoadoutSerial;
	bHasLoadout = true;
	UE_LOG(LogInstagib, Log, TEXT("LOADOUT %s (%s, %s): %s"), *GetPlayerName(), bIsBotPlayer ? TEXT("bot") : TEXT("human"),
		GetNetMode() == NM_Client ? TEXT("client") : TEXT("server"), *IALoadout::Describe(Loadout));
}

void AIAPlayerState::ResetMatchStats()
{
	Kills = 0;
	Deaths = 0;
	Captures = 0;
	Returns = 0;
	FlagKills = 0;
	ShotsFired = 0;
	ShotsHit = 0;
	Streak = 0;
	BestStreak = 0;
	MultiKill = 0;
	LastKillTime = -100.f;
	LeadState = 0;
	SpawnProtectEndTime = 0.f;
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
		// Shooting ends the spawn protection.
		if (PS->SpawnProtectEndTime > 0.f)
		{
			if (AIAGameMode* GM = World ? World->GetAuthGameMode<AIAGameMode>() : nullptr)
			{
				GM->EndSpawnProtection(const_cast<APawn*>(Shooter));
			}
		}
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
