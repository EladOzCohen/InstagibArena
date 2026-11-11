// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;
class AIAPlayerState;
class SVerticalBox;

/**
 * The scoreboard table: rank, name, kills, deaths, K/D, accuracy, best streak and ping.
 * In team games the players are grouped by team. The player on this machine is highlighted and bots are tagged.
 * Used for the Tab overlay during the match and on the results screen.
 * The rows are rebuilt only when the order of the players changes; the numbers update by themselves.
 */
class SIAScoreboard : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIAScoreboard) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;

private:
	void Rebuild(const TArray<const AIAPlayerState*>& Ordered, bool bTeamGame, int32 RedScore, int32 BlueScore);
	TSharedRef<SWidget> MakeHeaderRow() const;
	TSharedRef<SWidget> MakeTeamRow(int32 Team, TFunction<int32()> Score) const;
	TSharedRef<SWidget> MakePlayerRow(TWeakObjectPtr<const AIAPlayerState> State, int32 Rank, bool bLocal) const;

	TWeakObjectPtr<APlayerController> Owner;
	TSharedPtr<SVerticalBox> Body;
	TArray<int32> Signature;
};
