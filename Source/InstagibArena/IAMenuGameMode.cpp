// Instagib Arena

#include "IAMenuGameMode.h"
#include "IAMenuPlayerController.h"

AIAMenuGameMode::AIAMenuGameMode()
{
	DefaultPawnClass = nullptr;
	PlayerControllerClass = AIAMenuPlayerController::StaticClass();
}
