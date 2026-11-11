// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;
class SBox;

/**
 * The welcome overlay shown on the first launch (and after "Reset tutorial"):
 * step 1 asks for a name and fullscreen or windowed, step 2 is a short tour of the controls.
 * Esc skips it. OnFinished runs when the player is through or skipped.
 */
class SIAWelcome : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIAWelcome) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		SLATE_ARGUMENT(TFunction<void()>, OnFinished)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;

	/** Developer check: jumps to a step (0 or 1). */
	void ShowStep(int32 NewStep);

private:
	TSharedRef<SWidget> BuildStep(int32 StepIndex);
	void Finish();

	TWeakObjectPtr<APlayerController> Owner;
	TFunction<void()> OnFinished;
	TSharedPtr<SBox> StepHost;
	FString NameText;
	int32 Step = 0;
};
