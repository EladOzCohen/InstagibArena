// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "IASettings.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;

/**
 * The main menu, written in Slate so it needs no UMG assets.
 *
 * A column on the left holds the screens, one at a time:
 *   Main         Quick Play, Custom Game, Multiplayer, Character, Settings, Credits, Quit
 *   Custom Game  game type, map, bots and limits, then Start
 *   Multiplayer  Host a game (same setup as Custom Game) or Join a game by address
 *   Character    a grid of the 15 characters, with a live 3D preview on the right of the screen
 *   Settings     name, volumes, mouse sensitivity, field of view, display mode
 *   Credits
 * Esc goes back one screen. The arrow keys and Enter work as well as the mouse.
 */
class SIAMainMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIAMainMenu) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		/** Called whenever the selected character changes, so that the 3D preview can follow. */
		SLATE_ARGUMENT(TFunction<void(int32)>, OnCharacterChanged)
		/** A message to show on the Join screen when the menu opens (for example "connection lost"). */
		SLATE_ARGUMENT(FString, InitialError)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	int32 GetCharacterIndex() const { return Setup.CharacterIndex; }

	/** Developer check: opens a screen by number (0 main ... 5 credits). Used by -IAMenuPage=N for screenshots. */
	void ShowPageForTest(int32 PageIndex, int32 Tab);

	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;

private:
	enum class EPage : int32
	{
		Main = 0,
		Custom,
		Multiplayer,
		Character,
		Settings,
		Credits
	};

	void GoTo(EPage NewPage);

	TSharedRef<SWidget> BuildMainPage();
	TSharedRef<SWidget> BuildCustomPage();
	TSharedRef<SWidget> BuildMultiplayerPage();
	TSharedRef<SWidget> BuildCharacterPage();
	TSharedRef<SWidget> BuildSettingsPage();
	TSharedRef<SWidget> BuildCreditsPage();

	/** The game rules rows, used by both Custom Game and Host a game. */
	TSharedRef<SWidget> BuildSetupRows();
	TSharedRef<SWidget> BuildBackButton();

	void SelectCharacter(int32 Index);
	void StartGame(bool bHost);
	void JoinGame();
	void QuitGame();

	FString BuildOptions(bool bHost) const;

	TWeakObjectPtr<APlayerController> Owner;
	TFunction<void(int32)> OnCharacterChanged;

	EPage Page = EPage::Main;
	FIAMatchSetup Setup;

	int32 MultiplayerTab = 0;      // 0 = host a game, 1 = join a game
	FString JoinAddress;
	FText JoinStatus;
	FLinearColor JoinStatusColor = FLinearColor::White;
};
