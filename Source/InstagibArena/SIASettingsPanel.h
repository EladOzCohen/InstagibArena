// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;

/**
 * The settings screen: player name, volumes, mouse sensitivity, field of view and display mode.
 * Used by the main menu and by the pause menu. Every change is applied and saved at once.
 */
class SIASettingsPanel : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIASettingsPanel) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		/** Shows the player name row. The pause menu leaves it out, because the name only counts when joining. */
		SLATE_ARGUMENT(bool, ShowPlayerName)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
};
