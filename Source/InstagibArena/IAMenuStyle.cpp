// Instagib Arena

#include "IAMenuStyle.h"
#include "IAAudioSubsystem.h"
#include "Brushes/SlateNoResource.h"
#include "GameFramework/PlayerController.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateTypes.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace IAMenu
{
	const FLinearColor Accent(1.0f, 0.42f, 0.0f, 1.0f);
	const FLinearColor TextDim(0.62f, 0.64f, 0.70f, 1.0f);
	const FLinearColor PanelColor(0.012f, 0.014f, 0.022f, 0.86f);

	namespace
	{
		/** A button with no drawing of its own: the content draws every state. */
		const FButtonStyle& InvisibleButtonStyle()
		{
			static const FSlateNoResource NoResource;
			static const FButtonStyle Style = FButtonStyle()
				.SetNormal(NoResource)
				.SetHovered(NoResource)
				.SetPressed(NoResource)
				.SetDisabled(NoResource)
				.SetNormalPadding(FMargin(0.f))
				.SetPressedPadding(FMargin(0.f));
			return Style;
		}

		const FSlateBrush* WhiteBrush()
		{
			return FCoreStyle::Get().GetBrush("WhiteBrush");
		}

		/** Hover or keyboard focus. The button pointer is filled in right after the button is made. */
		bool IsActive(const TSharedRef<TWeakPtr<SButton>>& Holder)
		{
			const TSharedPtr<SButton> Button = Holder->Pin();
			return Button.IsValid() && (Button->IsHovered() || Button->HasKeyboardFocus());
		}
	}

	FSlateFontInfo Font(int32 Size, bool bBold)
	{
		return FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), Size);
	}

	void Click(const TWeakObjectPtr<APlayerController>& Owner)
	{
		if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(Owner.Get()))
		{
			Audio->Play2D(EIASound::UIClick);
		}
	}

	TSharedRef<SWidget> NavButton(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, const FText& Hint,
		TFunction<void()> OnClick, float Width)
	{
		const TSharedRef<TWeakPtr<SButton>> Holder = MakeShared<TWeakPtr<SButton>>();
		TSharedPtr<SButton> Button;

		SAssignNew(Button, SButton)
			.ButtonStyle(&InvisibleButtonStyle())
			.ContentPadding(FMargin(0.f))
			.OnClicked_Lambda([Owner, OnClick]()
			{
				Click(Owner);
				if (OnClick)
				{
					OnClick();
				}
				return FReply::Handled();
			})
			[
				SNew(SBox)
				.WidthOverride(Width)
				[
					SNew(SBorder)
					.BorderImage(WhiteBrush())
					.BorderBackgroundColor_Lambda([Holder]() -> FSlateColor
					{
						return IsActive(Holder) ? FLinearColor(1.f, 0.42f, 0.f, 0.30f) : FLinearColor(0.f, 0.f, 0.f, 0.f);
					})
					.Padding(FMargin(0.f))
					[
						SNew(SHorizontalBox)
						// The orange bar on the left lights up with the entry.
						+ SHorizontalBox::Slot().AutoWidth()
						[
							SNew(SBox).WidthOverride(5.f)
							[
								SNew(SBorder)
								.BorderImage(WhiteBrush())
								.BorderBackgroundColor_Lambda([Holder]() -> FSlateColor
								{
									return IsActive(Holder) ? Accent : FLinearColor(0.f, 0.f, 0.f, 0.f);
								})
							]
						]
						+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center).Padding(FMargin(18.f, 8.f))
						[
							SNew(SVerticalBox)
							+ SVerticalBox::Slot().AutoHeight()
							[
								SNew(STextBlock)
								.Text(Label)
								.Font(Font(26, true))
								.ColorAndOpacity_Lambda([Holder]() -> FSlateColor
								{
									return IsActive(Holder) ? FLinearColor::White : FLinearColor(0.82f, 0.84f, 0.90f);
								})
							]
							+ SVerticalBox::Slot().AutoHeight()
							[
								SNew(STextBlock)
								.Text(Hint)
								.Visibility(Hint.IsEmpty() ? EVisibility::Collapsed : EVisibility::HitTestInvisible)
								.Font(Font(13))
								.ColorAndOpacity(TextDim)
							]
						]
					]
				]
			];

		*Holder = Button;
		return Button.ToSharedRef();
	}

	TSharedRef<SWidget> Chip(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, TFunction<void()> OnClick,
		TFunction<bool()> IsSelected, float MinWidth, int32 FontSize)
	{
		const TSharedRef<TWeakPtr<SButton>> Holder = MakeShared<TWeakPtr<SButton>>();
		TSharedPtr<SButton> Button;

		SAssignNew(Button, SButton)
			.ButtonStyle(&InvisibleButtonStyle())
			.ContentPadding(FMargin(0.f))
			.OnClicked_Lambda([Owner, OnClick]()
			{
				Click(Owner);
				if (OnClick)
				{
					OnClick();
				}
				return FReply::Handled();
			})
			[
				SNew(SBox)
				.MinDesiredWidth(MinWidth)
				[
					SNew(SBorder)
					.BorderImage(WhiteBrush())
					.BorderBackgroundColor_Lambda([Holder, IsSelected]() -> FSlateColor
					{
						if (IsSelected && IsSelected())
						{
							return IsActive(Holder) ? FLinearColor(1.f, 0.55f, 0.12f) : Accent;
						}
						return IsActive(Holder) ? FLinearColor(0.36f, 0.37f, 0.43f) : FLinearColor(0.19f, 0.20f, 0.25f);
					})
					.Padding(FMargin(16.f, 8.f))
					.HAlign(HAlign_Center)
					[
						SNew(STextBlock)
						.Text(Label)
						.Font(Font(FontSize, true))
						.ColorAndOpacity(FLinearColor::White)
					]
				]
			];

		*Holder = Button;
		return Button.ToSharedRef();
	}

	TSharedRef<SWidget> PrimaryButton(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, TFunction<void()> OnClick,
		float MinWidth)
	{
		return Chip(Owner, Label, OnClick, []() { return true; }, MinWidth, 22);
	}

	TSharedRef<SWidget> Stepper(const TWeakObjectPtr<APlayerController>& Owner, TFunction<FText()> ValueText,
		TFunction<void()> OnMinus, TFunction<void()> OnPlus, float ValueWidth)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				Chip(Owner, INVTEXT("-"), OnMinus, nullptr, 44.f, 18)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8.f, 0.f)
			[
				SNew(SBox).MinDesiredWidth(ValueWidth).HAlign(HAlign_Center)
				[
					SNew(STextBlock)
					.Text_Lambda([ValueText]() { return ValueText(); })
					.Font(Font(18, true))
					.ColorAndOpacity(Accent)
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				Chip(Owner, INVTEXT("+"), OnPlus, nullptr, 44.f, 18)
			];
	}

	TSharedRef<SWidget> Row(const FText& Label, TSharedRef<SWidget> Content, float LabelWidth)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SBox).WidthOverride(LabelWidth)
				[
					SNew(STextBlock)
					.Text(Label)
					.Font(Font(16))
					.ColorAndOpacity(FLinearColor(0.82f, 0.84f, 0.90f))
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				Content
			];
	}

	TSharedRef<SWidget> Heading(const FText& Title)
	{
		return SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight()
			[
				SNew(STextBlock)
				.Text(Title)
				.Font(Font(34, true))
				.ColorAndOpacity(Accent)
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f, 0.f, 18.f)
			[
				SNew(SBox).HeightOverride(2.f)
				[
					SNew(SBorder)
					.BorderImage(WhiteBrush())
					.BorderBackgroundColor(FLinearColor(1.f, 0.42f, 0.f, 0.55f))
				]
			];
	}

	TSharedRef<SWidget> Note(TFunction<FText()> Text, TFunction<FLinearColor()> Color)
	{
		return SNew(STextBlock)
			.Text_Lambda([Text]() { return Text(); })
			.AutoWrapText(true)
			.Font(Font(14))
			.ColorAndOpacity_Lambda([Color]() -> FSlateColor { return Color ? Color() : TextDim; });
	}
}
