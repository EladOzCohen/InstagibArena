// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;

/**
 * The results screen after a match: who won, the full scoreboard, and the choice
 * PLAY AGAIN (host only; it also starts by itself after a countdown) or MAIN MENU.
 */
class SIAMatchResults : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIAMatchResults) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		SLATE_ARGUMENT(TFunction<void()>, OnPlayAgain)
		SLATE_ARGUMENT(TFunction<void()>, OnMainMenu)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;
	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;

private:
	FText GetHeadline() const;
	FLinearColor GetHeadlineColor() const;
	FText GetSubline() const;
	FText GetCountdownText() const;

	TWeakObjectPtr<APlayerController> Owner;
	TFunction<void()> PlayAgain;
	float Age = 0.f;
	bool bHost = false;
};
