// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;

/**
 * Main menu, written in Slate so it needs no UMG assets.
 * Lets the player pick game type, map, bots, bot skill and limits,
 * then start a local game, host a LAN game or join one by IP address.
 */
class SIAMainMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIAMainMenu) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		/** Called whenever the selected character changes, so that the preview can follow. */
		SLATE_ARGUMENT(TFunction<void(int32)>, OnCharacterChanged)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	TSharedRef<SWidget> MakeButton(const FText& Label, TFunction<void()> OnClick, TFunction<bool()> IsSelected, float MinWidth = 0.f);
	TSharedRef<SWidget> MakeStepper(TFunction<FText()> ValueText, TFunction<void()> OnMinus, TFunction<void()> OnPlus);
	TSharedRef<SWidget> MakeRow(const FString& Label, TSharedRef<SWidget> Content);

	void StartGame(bool bHost);
	void JoinGame();

	TWeakObjectPtr<APlayerController> Owner;
	TFunction<void(int32)> OnCharacterChanged;

	bool bTeamGame = false;
	int32 MapIndex = 0;
	int32 CharacterIndex = 0;
	int32 BotCount = 4;
	int32 BotSkill = 1;
	int32 ScoreLimit = 25;
	int32 TimeLimit = 10;
	FString JoinAddress = TEXT("127.0.0.1");
};
