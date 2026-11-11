// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;
class FIAModal;
class SIAControlsPanel;
class SWidgetSwitcher;

/**
 * The settings screen with four tabs: GAMEPLAY, VIDEO, AUDIO and CONTROLS.
 * Used by the main menu and by the pause menu. Nothing here needs a restart.
 * Changes are applied and saved at once, except the resolution and display mode:
 * those are applied on request and reverted after 10 seconds unless the player keeps them.
 */
class SIASettingsPanel : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIASettingsPanel) : _ShowPlayerName(false), _InMatch(false), _InitialTab(0) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		/** Shows the player name row. The pause menu leaves it out, because the name only counts when joining. */
		SLATE_ARGUMENT(bool, ShowPlayerName)
		/** True in the pause menu: key changes then apply from the next match. */
		SLATE_ARGUMENT(bool, InMatch)
		SLATE_ARGUMENT(TSharedPtr<FIAModal>, Modal)
		/** When set, the Gameplay tab offers "Reset tutorial". */
		SLATE_ARGUMENT(TFunction<void()>, OnResetTutorial)
		SLATE_ARGUMENT(int32, InitialTab)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	void SetTab(int32 Tab);
	int32 GetTab() const { return ActiveTab; }

	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;

	/** Developer check: "tab=N", "res=WxH", "mode=N", "apply", "keep", "revert", "rebind=Id:Key", "reset-keys", "listen=Id". */
	bool DevCommand(const FString& Command);

private:
	TSharedRef<SWidget> BuildGameplayTab(const FArguments& Args);
	TSharedRef<SWidget> BuildVideoTab();
	TSharedRef<SWidget> BuildAudioTab();

	void BuildResolutionList();
	void SyncPendingVideo();
	bool HasPendingVideo() const;
	void ApplyPendingVideo();
	void RevertVideo();
	void KeepVideo();
	FIntPoint EffectiveResolution(EWindowMode::Type Mode, const FIntPoint& Res) const;

	TWeakObjectPtr<APlayerController> Owner;
	TSharedPtr<FIAModal> Modal;
	TSharedPtr<SIAControlsPanel> ControlsPanel;
	TSharedPtr<SWidgetSwitcher> Tabs;

	int32 ActiveTab = 0;

	TArray<FIntPoint> Resolutions;
	FIntPoint PendingResolution = FIntPoint::ZeroValue;
	EWindowMode::Type PendingMode = EWindowMode::Windowed;
	FIntPoint PreviousResolution = FIntPoint::ZeroValue;
	EWindowMode::Type PreviousMode = EWindowMode::Windowed;
};
