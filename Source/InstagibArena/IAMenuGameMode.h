// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "IAMenuGameMode.generated.h"

/** Game mode of the main menu level: no pawn, only the menu controller. */
UCLASS()
class INSTAGIBARENA_API AIAMenuGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AIAMenuGameMode();
};
