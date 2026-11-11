// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;
class FIAModal;

/**
 * Lists every action of the key table (IAInputConfig.cpp) with its current key.
 * Click an action, press a key (or a mouse button) to bind it; Esc cancels.
 * When the key already belongs to another action, a box offers to swap the two.
 * The list is read from the table every time, so new actions appear without changes here.
 * In ReadOnly mode (How to Play, welcome tour) it only shows the keys.
 */
class SIAControlsPanel : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIAControlsPanel) : _ReadOnly(false), _InMatch(false) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		SLATE_ARGUMENT(TSharedPtr<FIAModal>, Modal)
		SLATE_ARGUMENT(bool, ReadOnly)
		/** Inside a match the note says that changes only count from the next match. */
		SLATE_ARGUMENT(bool, InMatch)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	bool IsListening() const { return !ListeningId.IsNone(); }

	/** Developer check: does what pressing the key while listening does (without the clash box being skipped). */
	void DevRebind(FName Id, FKey Key);
	void DevListen(FName Id) { BeginListen(Id); }
	void DevReset();

	virtual FReply OnPreviewKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply OnPreviewMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FReply OnMouseWheel(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;

private:
	void BeginListen(FName Id);
	void CancelListen();
	void Bind(FName Id, FKey Key);
	void ResetToDefaults();

	TWeakObjectPtr<APlayerController> Owner;
	TSharedPtr<FIAModal> Modal;
	FName ListeningId;
	bool bReadOnly = false;
};
