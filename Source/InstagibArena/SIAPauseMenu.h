// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;

/**
 * The menu that opens with Esc during a match: Resume, Settings, Leave Match, Quit Game.
 * The match keeps running behind it (in a game with other players it cannot be paused).
 */
class SIAPauseMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIAPauseMenu) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		SLATE_ARGUMENT(TFunction<void()>, OnResume)
		SLATE_ARGUMENT(TFunction<void()>, OnLeave)
		SLATE_ARGUMENT(TFunction<void()>, OnQuit)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;

private:
	TWeakObjectPtr<APlayerController> Owner;
	TFunction<void()> OnResume;
	bool bShowSettings = false;
};
