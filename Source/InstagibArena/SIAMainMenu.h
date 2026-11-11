// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "IAMenuStyle.h"
#include "IASettings.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;
class FIAModal;
class SBox;
class SIASettingsPanel;
class SIAWelcome;

/**
 * The main menu, written in Slate so it needs no UMG assets.
 *
 * A column on the left holds the screens, one at a time (they slide in):
 *   Main         Quick Play, Custom Game, Multiplayer, Character, How to Play, Settings, Credits, Quit
 *   Custom Game  game type, map with preview picture, bots and limits, then Start
 *   Multiplayer  Host a game (same setup as Custom Game) or Join a game by address
 *   Character    a grid of the 15 characters, with a live 3D preview on the right of the screen
 *   Settings     Gameplay, Video, Audio and Controls tabs
 *   Credits
 *   How to Play  the goal and every control with the player's current keys
 * Esc goes back one screen. The arrow keys, Tab and Enter work as well as the mouse.
 * On the first launch a welcome overlay asks for a name and shows the controls.
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

	/** Developer check: opens a screen by number (0 main ... 6 how to play). Used by -IAMenuPage=N for screenshots. */
	void ShowPageForTest(int32 PageIndex, int32 Tab);

	/** Developer check: one command of -IAMenuScript (see IAMenuPlayerController.cpp). */
	void DevCommand(const FString& Command);

	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;

private:
	enum class EPage : int32
	{
		Main = 0,
		Custom,
		Multiplayer,
		Character,
		Settings,
		Credits,
		HowToPlay
	};

	void GoTo(EPage NewPage);
	float PageWidth() const;
	TSharedRef<SWidget> BuildPage(EPage Which);

	TSharedRef<SWidget> BuildMainPage();
	TSharedRef<SWidget> BuildCustomPage();
	TSharedRef<SWidget> BuildMultiplayerPage();
	TSharedRef<SWidget> BuildCharacterPage();
	TSharedRef<SWidget> BuildSettingsPage();
	TSharedRef<SWidget> BuildCreditsPage();
	TSharedRef<SWidget> BuildHowToPlayPage();

	/** Heading, a body that scrolls when the window is small, and a row of buttons that always stays visible. */
	TSharedRef<SWidget> Frame(const FText& Title, TSharedRef<SWidget> Body, TSharedRef<SWidget> Footer);

	/** The game rules rows, used by both Custom Game and Host a game. */
	TSharedRef<SWidget> BuildSetupRows();
	/** The map picture with name, description, recommended players and previous/next. */
	TSharedRef<SWidget> BuildMapCard();
	TSharedRef<SWidget> BuildBackButton();

	void ShowWelcome(int32 Step = 0);
	void SelectCharacter(int32 Index);
	void StartGame(bool bHost);
	void JoinGame();
	void QuitGame();
	void ChangeMap(int32 Delta);

	FString BuildOptions(bool bHost) const;

	TWeakObjectPtr<APlayerController> Owner;
	TFunction<void(int32)> OnCharacterChanged;

	EPage Page = EPage::Main;
	FIAMatchSetup Setup;

	int32 MultiplayerTab = 0;      // 0 = host a game, 1 = join a game
	int32 SettingsTab = 0;
	FString JoinAddress;
	FText JoinStatus;
	FLinearColor JoinStatusColor = FLinearColor::White;
	double CopiedUntil = 0.0;

	TSharedPtr<FIAModal> Modal;
	TSharedPtr<SBox> PageHost;
	TSharedPtr<SBox> WelcomeHost;
	TSharedPtr<SIAWelcome> Welcome;
	TWeakPtr<SIASettingsPanel> SettingsPanel;

	IAMenu::FDevScript Script;     // -IAMenuScript="page=4;settings=1;..." (development only)
	float PageTime = 1.f;         // 0 when a screen has just been opened, 1 when its slide-in is done
};
