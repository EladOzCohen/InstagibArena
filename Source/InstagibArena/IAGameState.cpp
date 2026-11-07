// Instagib Arena

#include "IAGameState.h"
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
}
