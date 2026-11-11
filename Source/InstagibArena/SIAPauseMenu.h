// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "IAMenuStyle.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;
class FIAModal;
class SIASettingsPanel;

/**
 * The menu that opens with Esc during a match: Resume, Settings, Leave Match, Quit Game.
 * The settings are the same panel as in the main menu (Gameplay, Video, Audio, Controls); nothing in it needs a restart.
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
	virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;

	/** Developer check: a command of -IAPauseScript (same commands as the settings panel, plus "key=Name"). */
	void DevCommand(const FString& Command);

private:
	void ShowSettings(bool bShow);
	TSharedRef<SWidget> BuildMainPage();

	TWeakObjectPtr<APlayerController> Owner;
	TFunction<void()> OnResume;
	TFunction<void()> OnLeave;
	TFunction<void()> OnQuit;
	bool bShowSettings = false;
	int32 InitialSettingsTab = 0;

	TSharedPtr<FIAModal> Modal;
	TSharedPtr<SWidget> ContentRoot;
	IAMenu::FDevScript Script;     // -IAPauseScript="settings=1;key=Down;..." (development only)
	TWeakPtr<SIASettingsPanel> SettingsPanel;
};
