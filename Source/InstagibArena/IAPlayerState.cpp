// Instagib Arena

#include "IAPlayerState.h"
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
}
