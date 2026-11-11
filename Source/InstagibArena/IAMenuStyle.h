// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SWidget.h"

class APlayerController;
class SToolTip;

/**
 * Look and building blocks shared by the main menu and the pause menu.
 * Every button here draws its own hover, focus and selected state, so the menus work
 * with the mouse and with the keyboard (arrow keys, Tab, Enter, Esc).
 */
namespace IAMenu
{
	extern const FLinearColor Accent;      // the orange of the game
	extern const FLinearColor TextDim;     // secondary text
	extern const FLinearColor PanelColor;  // dark panel behind the menu

	FSlateFontInfo Font(int32 Size, bool bBold = false);

	/** Plays the click sound for the local player. */
	void Click(const TWeakObjectPtr<APlayerController>& Owner);

	/** Plays the quiet tick heard when the pointer moves onto a button. */
	void HoverTick(const TWeakObjectPtr<APlayerController>& Owner);

	/** A dark tooltip in the style of the menus. */
	TSharedRef<SToolTip> MakeTip(const FText& Text);

	/** A large menu entry with an optional second line: "PLAY" over "Start a match against bots". */
	TSharedRef<SWidget> NavButton(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, const FText& Hint,
		TFunction<void()> OnClick, float Width = 380.f);

	/** A compact button that can show a selected state (orange). */
	TSharedRef<SWidget> Chip(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, TFunction<void()> OnClick,
		TFunction<bool()> IsSelected, float MinWidth = 0.f, int32 FontSize = 16);

	/** A chip whose text can change (a key name, "Press a key..."). */
	TSharedRef<SWidget> ChipDyn(const TWeakObjectPtr<APlayerController>& Owner, TFunction<FText()> Label, TFunction<void()> OnClick,
		TFunction<bool()> IsSelected, float MinWidth = 0.f, int32 FontSize = 16);

	/** Developer check: sends a key press through Slate exactly like the keyboard does (focus, navigation, shortcuts). */
	void SimulateKey(const FKey& Key);

	/** The main action of a screen: a wide, always-orange chip. */
	TSharedRef<SWidget> PrimaryButton(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, TFunction<void()> OnClick,
		float MinWidth = 280.f);

	/** "-  value  +". */
	TSharedRef<SWidget> Stepper(const TWeakObjectPtr<APlayerController>& Owner, TFunction<FText()> ValueText,
		TFunction<void()> OnMinus, TFunction<void()> OnPlus, float ValueWidth = 150.f);

	/** A slider with the value written to its right. The arrow keys move it when it has focus. */
	TSharedRef<SWidget> Slider(const TWeakObjectPtr<APlayerController>& Owner, float Min, float Max, float Step,
		TFunction<float()> Get, TFunction<void(float)> Set, TFunction<FText(float)> Format, float Width = 230.f);

	/** "ON" and "OFF" side by side. */
	TSharedRef<SWidget> Toggle(const TWeakObjectPtr<APlayerController>& Owner, TFunction<bool()> Get, TFunction<void(bool)> Set);

	/** A small square of colour that can show a selected state. */
	TSharedRef<SWidget> Swatch(const TWeakObjectPtr<APlayerController>& Owner, const FLinearColor& Color, TFunction<void()> OnClick,
		TFunction<bool()> IsSelected);

	/** A label on the left and a control on the right. The tooltip (when not empty) shows over the whole row. */
	TSharedRef<SWidget> Row(const FText& Label, TSharedRef<SWidget> Content, float LabelWidth = 170.f,
		const FText& Tooltip = FText::GetEmpty());

	/** The title of a screen, with a line under it. */
	TSharedRef<SWidget> Heading(const FText& Title);

	/** A small grey line of explanation. */
	TSharedRef<SWidget> Note(TFunction<FText()> Text, TFunction<FLinearColor()> Color = nullptr);

	/** A scroll box with a thin bar, for content that may not fit at large UI scales. */
	TSharedRef<SWidget> ScrollArea(TSharedRef<SWidget> Content);

	/** Gives keyboard focus to the first button (or other focusable widget) found under Root. Returns whether one was found. */
	bool FocusFirst(const TSharedRef<SWidget>& Root);

	/** Keeps arrow keys and Tab inside the widget instead of leaving it for widgets behind. */
	void KeepNavigationInside(SWidget& Container);

	/** Formats a key for the player: "Space Bar", "Left Mouse Button". */
	FText KeyText(const FKey& Key);

	/**
	 * Developer check (not in shipping builds): runs the commands of  -IAMenuScript="a;b;c"  (or another parameter name)
	 * one after another, 0.7 s apart. "wait=3" pauses for 3 seconds. Call Step every frame.
	 */
	struct FDevScript
	{
		TArray<FString> Commands;
		int32 Next = 0;
		float Timer = -1.5f;

		void Load(const TCHAR* ParamName);
		/** Returns a command when one is due, otherwise an empty string. */
		FString Step(float DeltaTime);
	};
}

/**
 * A message box over the whole screen: a title, a text and a few buttons, optionally closing itself
 * after some seconds (as a cancel). Esc cancels. Used for "Quit?", "Keep these display settings?",
 * "Key already used" and similar questions.
 */
class FIAModal : public TSharedFromThis<FIAModal>
{
public:
	struct FChoice
	{
		FText Label;
		TFunction<void()> Action;
		bool bPrimary = false;
	};

	explicit FIAModal(const TWeakObjectPtr<APlayerController>& InOwner) : Owner(InOwner) {}

	/** Add this widget on top of everything else on the screen. It is invisible until Show is called. */
	TSharedRef<SWidget> GetWidget();

	/** Where keyboard focus goes back to when the box closes. */
	void SetRestoreFocus(const TSharedPtr<SWidget>& Widget) { RestoreFocus = Widget; }

	void Show(const FText& Title, TFunction<FText()> Body, const TArray<FChoice>& Choices, TFunction<void()> OnCancel = nullptr,
		float AutoCancelSeconds = 0.f);
	void Hide();
	void Cancel();
	bool IsOpen() const { return bOpen; }
	float GetSecondsLeft() const;

	/** Called by the layer every frame while open. */
	void TickAutoCancel();

private:
	TWeakObjectPtr<APlayerController> Owner;
	TSharedPtr<SWidget> Layer;
	TSharedPtr<class SBox> DialogHost;
	TWeakPtr<SWidget> RestoreFocus;
	TFunction<void()> CancelAction;
	bool bOpen = false;
	double AutoCancelAt = 0.0;
};
