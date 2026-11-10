// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SWidget.h"

class APlayerController;

/**
 * Look and building blocks shared by the main menu and the pause menu.
 * Every button here draws its own hover, focus and selected state, so the menus work
 * with the mouse and with the keyboard (arrow keys, Enter).
 */
namespace IAMenu
{
	extern const FLinearColor Accent;      // the orange of the game
	extern const FLinearColor TextDim;     // secondary text
	extern const FLinearColor PanelColor;  // dark panel behind the menu

	FSlateFontInfo Font(int32 Size, bool bBold = false);

	/** Plays the click sound for the local player. */
	void Click(const TWeakObjectPtr<APlayerController>& Owner);

	/** A large menu entry with an optional second line: "PLAY" over "Start a match against bots". */
	TSharedRef<SWidget> NavButton(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, const FText& Hint,
		TFunction<void()> OnClick, float Width = 380.f);

	/** A compact button that can show a selected state (orange). */
	TSharedRef<SWidget> Chip(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, TFunction<void()> OnClick,
		TFunction<bool()> IsSelected, float MinWidth = 0.f, int32 FontSize = 16);

	/** The main action of a screen: a wide, always-orange chip. */
	TSharedRef<SWidget> PrimaryButton(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, TFunction<void()> OnClick,
		float MinWidth = 280.f);

	/** "-  value  +". */
	TSharedRef<SWidget> Stepper(const TWeakObjectPtr<APlayerController>& Owner, TFunction<FText()> ValueText,
		TFunction<void()> OnMinus, TFunction<void()> OnPlus, float ValueWidth = 150.f);

	/** A label on the left and a control on the right. */
	TSharedRef<SWidget> Row(const FText& Label, TSharedRef<SWidget> Content, float LabelWidth = 170.f);

	/** The title of a screen, with a line under it. */
	TSharedRef<SWidget> Heading(const FText& Title);

	/** A small grey line of explanation. */
	TSharedRef<SWidget> Note(TFunction<FText()> Text, TFunction<FLinearColor()> Color = nullptr);
}
