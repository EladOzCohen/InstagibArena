// Instagib Arena

#include "IAMenuStyle.h"
#include "IAAudioSubsystem.h"
#include "Brushes/SlateNoResource.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateTypes.h"
#include "Types/NavigationMetaData.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Widgets/SToolTip.h"
#include "Widgets/SCompoundWidget.h"
#include "Misc/App.h"

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

	void HoverTick(const TWeakObjectPtr<APlayerController>& Owner)
	{
		if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(Owner.Get()))
		{
			Audio->Play2D(EIASound::UIHover);
		}
	}

	TSharedRef<SToolTip> MakeTip(const FText& Text)
	{
		return SNew(SToolTip)
			.BorderImage(WhiteBrush())
			.TextMargin(FMargin(0.f))
			[
				SNew(SBorder)
				.BorderImage(WhiteBrush())
				.BorderBackgroundColor(FLinearColor(0.03f, 0.035f, 0.05f, 0.97f))
				.Padding(FMargin(12.f, 8.f))
				[
					SNew(SBox).MaxDesiredWidth(340.f)
					[
						SNew(STextBlock)
						.Text(Text)
						.AutoWrapText(true)
						.Font(Font(14))
						.ColorAndOpacity(FLinearColor(0.88f, 0.9f, 0.95f))
					]
				]
			];
	}

	FText KeyText(const FKey& Key)
	{
		return Key.IsValid() ? Key.GetDisplayName() : INVTEXT("Unbound");
	}

	TSharedRef<SWidget> ScrollArea(TSharedRef<SWidget> Content)
	{
		return SNew(SScrollBox)
			.ScrollBarThickness(FVector2D(5.f, 5.f))
			.AllowOverscroll(EAllowOverscroll::No)
			+ SScrollBox::Slot()
			.Padding(FMargin(0.f, 0.f, 12.f, 0.f))
			[
				Content
			];
	}

	namespace
	{
		SWidget* FindFocusable(SWidget& Widget)
		{
			if (Widget.GetVisibility() != EVisibility::Visible && !Widget.GetVisibility().IsVisible())
			{
				return nullptr;
			}
			if (Widget.GetVisibility() == EVisibility::Visible && Widget.SupportsKeyboardFocus() && Widget.IsEnabled())
			{
				return &Widget;
			}
			if (FChildren* Children = Widget.GetChildren())
			{
				for (int32 Index = 0; Index < Children->Num(); ++Index)
				{
					TSharedRef<SWidget> Child = Children->GetChildAt(Index);
					if (SWidget* Found = FindFocusable(Child.Get()))
					{
						return Found;
					}
				}
			}
			return nullptr;
		}
	}

	bool FocusFirst(const TSharedRef<SWidget>& Root)
	{
		if (SWidget* Found = FindFocusable(Root.Get()))
		{
			FSlateApplication::Get().SetKeyboardFocus(Found->AsShared(), EFocusCause::SetDirectly);
			return true;
		}
		return false;
	}

	void KeepNavigationInside(SWidget& Container)
	{
		const TSharedRef<FNavigationMetaData> Nav = MakeShared<FNavigationMetaData>();
		for (const EUINavigation Direction : { EUINavigation::Left, EUINavigation::Right, EUINavigation::Up, EUINavigation::Down,
			EUINavigation::Next, EUINavigation::Previous })
		{
			Nav->SetNavigationRule(Direction, EUINavigationRule::Wrap);
		}
		Container.AddMetadata(Nav);
	}

	namespace
	{
		/** A slider drawn by hand: a thin bar, an orange fill and a small handle. Mouse drag and Left/Right keys. */
		class SIASlider : public SLeafWidget
		{
		public:
			SLATE_BEGIN_ARGS(SIASlider) : _Min(0.f), _Max(1.f), _Step(0.1f), _Width(230.f) {}
				SLATE_ARGUMENT(float, Min)
				SLATE_ARGUMENT(float, Max)
				SLATE_ARGUMENT(float, Step)
				SLATE_ARGUMENT(float, Width)
				SLATE_ARGUMENT(TFunction<float()>, Get)
				SLATE_ARGUMENT(TFunction<void(float)>, Set)
				SLATE_ARGUMENT(TFunction<void()>, OnHover)
			SLATE_END_ARGS()

			void Construct(const FArguments& InArgs)
			{
				Min = InArgs._Min;
				Max = InArgs._Max;
				Step = InArgs._Step;
				Width = InArgs._Width;
				Get = InArgs._Get;
				Set = InArgs._Set;
				OnHover = InArgs._OnHover;
			}

			virtual bool SupportsKeyboardFocus() const override { return true; }

			virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(Width, 30.f); }

			virtual void OnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
			{
				SLeafWidget::OnMouseEnter(MyGeometry, MouseEvent);
				if (OnHover) { OnHover(); }
			}

			virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
			{
				if (MouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
				{
					SetFromMouse(MyGeometry, MouseEvent);
					return FReply::Handled().CaptureMouse(SharedThis(this)).SetUserFocus(SharedThis(this), EFocusCause::Mouse);
				}
				return FReply::Unhandled();
			}

			virtual FReply OnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
			{
				if (HasMouseCapture() && MouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
				{
					return FReply::Handled().ReleaseMouseCapture();
				}
				return FReply::Unhandled();
			}

			virtual FReply OnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override
			{
				if (HasMouseCapture())
				{
					SetFromMouse(MyGeometry, MouseEvent);
					return FReply::Handled();
				}
				return FReply::Unhandled();
			}

			virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override
			{
				const FKey Key = InKeyEvent.GetKey();
				if (Key == EKeys::Left || Key == EKeys::Right)
				{
					Apply(Get() + (Key == EKeys::Right ? Step : -Step));
					return FReply::Handled();
				}
				if (Key == EKeys::Home) { Apply(Min); return FReply::Handled(); }
				if (Key == EKeys::End) { Apply(Max); return FReply::Handled(); }
				return FReply::Unhandled();
			}

			virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
				FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override
			{
				const FSlateBrush* Brush = WhiteBrush();
				const FLinearColor Tint = InWidgetStyle.GetColorAndOpacityTint();
				const FVector2f Size = AllottedGeometry.GetLocalSize();
				const bool bActive = IsHovered() || HasKeyboardFocus() || HasMouseCapture();

				const float X0 = 8.f;
				const float X1 = FMath::Max(X0 + 1.f, Size.X - 8.f);
				const float Fraction = FMath::Clamp((Get() - Min) / FMath::Max(Max - Min, KINDA_SMALL_NUMBER), 0.f, 1.f);
				const float HandleX = X0 + (X1 - X0) * Fraction;
				const float TrackH = 6.f;
				const float TrackY = (Size.Y - TrackH) * 0.5f;

				auto Box = [&](float X, float Y, float W, float H, const FLinearColor& Color, int32 Layer)
				{
					FSlateDrawElement::MakeBox(OutDrawElements, Layer,
						AllottedGeometry.ToPaintGeometry(FVector2f(W, H), FSlateLayoutTransform(FVector2f(X, Y))),
						Brush, ESlateDrawEffect::None, Color * Tint);
				};

				Box(X0 - 2.f, TrackY, X1 - X0 + 4.f, TrackH, FLinearColor(0.19f, 0.20f, 0.25f), LayerId);
				Box(X0 - 2.f, TrackY, HandleX - X0 + 2.f, TrackH, bActive ? FLinearColor(1.f, 0.55f, 0.12f) : Accent, LayerId + 1);
				Box(HandleX - 6.f, (Size.Y - 22.f) * 0.5f, 12.f, 22.f, bActive ? FLinearColor::White : FLinearColor(0.82f, 0.84f, 0.90f), LayerId + 2);
				return LayerId + 3;
			}

		private:
			void SetFromMouse(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
			{
				const float Local = MyGeometry.AbsoluteToLocal(MouseEvent.GetScreenSpacePosition()).X;
				const float Fraction = FMath::Clamp((Local - 8.f) / FMath::Max(MyGeometry.GetLocalSize().X - 16.f, 1.f), 0.f, 1.f);
				Apply(Min + (Max - Min) * Fraction);
			}

			void Apply(float Value)
			{
				const float Snapped = Step > 0.f ? FMath::RoundToFloat((Value - Min) / Step) * Step + Min : Value;
				const float Clamped = FMath::Clamp(Snapped, Min, Max);
				if (!FMath::IsNearlyEqual(Clamped, Get()))
				{
					Set(Clamped);
				}
			}

			float Min = 0.f, Max = 1.f, Step = 0.1f, Width = 230.f;
			TFunction<float()> Get;
			TFunction<void(float)> Set;
			TFunction<void()> OnHover;
		};
	}

	TSharedRef<SWidget> Slider(const TWeakObjectPtr<APlayerController>& Owner, float Min, float Max, float Step,
		TFunction<float()> Get, TFunction<void(float)> Set, TFunction<FText(float)> Format, float Width)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SIASlider)
				.Min(Min).Max(Max).Step(Step).Width(Width)
				.Get(Get).Set(Set)
				.OnHover([Owner]() { HoverTick(Owner); })
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(14.f, 0.f, 0.f, 0.f)
			[
				SNew(SBox).MinDesiredWidth(64.f)
				[
					SNew(STextBlock)
					.Text_Lambda([Get, Format]() { return Format(Get()); })
					.Font(Font(18, true))
					.ColorAndOpacity(Accent)
				]
			];
	}

	TSharedRef<SWidget> Toggle(const TWeakObjectPtr<APlayerController>& Owner, TFunction<bool()> Get, TFunction<void(bool)> Set)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
			[
				Chip(Owner, INVTEXT("ON"), [Set]() { Set(true); }, [Get]() { return Get(); }, 80.f)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Chip(Owner, INVTEXT("OFF"), [Set]() { Set(false); }, [Get]() { return !Get(); }, 80.f)
			];
	}

	TSharedRef<SWidget> Swatch(const TWeakObjectPtr<APlayerController>& Owner, const FLinearColor& Color, TFunction<void()> OnClick,
		TFunction<bool()> IsSelected)
	{
		const TSharedRef<TWeakPtr<SButton>> Holder = MakeShared<TWeakPtr<SButton>>();
		TSharedPtr<SButton> Button;

		SAssignNew(Button, SButton)
			.ButtonStyle(&InvisibleButtonStyle())
			.ContentPadding(FMargin(0.f))
			.OnHovered_Lambda([Owner]() { HoverTick(Owner); })
			.OnClicked_Lambda([Owner, OnClick]()
			{
				Click(Owner);
				if (OnClick) { OnClick(); }
				return FReply::Handled();
			})
			[
				SNew(SBorder)
				.BorderImage(WhiteBrush())
				.BorderBackgroundColor_Lambda([Holder, IsSelected]() -> FSlateColor
				{
					if (IsSelected && IsSelected()) { return FLinearColor::White; }
					return IsActive(Holder) ? FLinearColor(0.7f, 0.72f, 0.78f) : FLinearColor(0.f, 0.f, 0.f, 0.f);
				})
				.Padding(FMargin(3.f))
				[
					SNew(SBox).WidthOverride(34.f).HeightOverride(26.f)
					[
						SNew(SBorder)
						.BorderImage(WhiteBrush())
						.BorderBackgroundColor(Color)
					]
				]
			];

		*Holder = Button;
		return Button.ToSharedRef();
	}
}

// ---------------------------------------------------------------- the message box

namespace
{
	/** The layer of a FIAModal. It only exists to be told about every frame. */
	class SIAModalLayer : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SIAModalLayer) {}
			SLATE_ARGUMENT(TWeakPtr<FIAModal>, Modal)
			SLATE_DEFAULT_SLOT(FArguments, Content)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			Modal = InArgs._Modal;
			ChildSlot[ InArgs._Content ];
		}

		virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override
		{
			if (const TSharedPtr<FIAModal> Pinned = Modal.Pin())
			{
				Pinned->TickAutoCancel();
			}
		}

	private:
		TWeakPtr<FIAModal> Modal;
	};
}

TSharedRef<SWidget> FIAModal::GetWidget()
{
	if (!Layer.IsValid())
	{
		SAssignNew(DialogHost, SBox);
		Layer = SNew(SIAModalLayer)
			.Modal(AsShared())
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.66f))
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					DialogHost.ToSharedRef()
				]
			];
		Layer->SetVisibility(EVisibility::Collapsed);
	}
	return Layer.ToSharedRef();
}

void FIAModal::Show(const FText& Title, TFunction<FText()> Body, const TArray<FChoice>& Choices, TFunction<void()> OnCancel, float AutoCancelSeconds)
{
	GetWidget();
	CancelAction = OnCancel;
	AutoCancelAt = AutoCancelSeconds > 0.f ? FPlatformTime::Seconds() + AutoCancelSeconds : 0.0;

	const TWeakPtr<FIAModal> WeakThis = AsShared();
	const TWeakObjectPtr<APlayerController> OwnerCopy = Owner;

	TSharedRef<SHorizontalBox> Buttons = SNew(SHorizontalBox);
	TSharedPtr<SWidget> FirstButton;
	for (const FChoice& Choice : Choices)
	{
		const TFunction<void()> Action = Choice.Action;
		TSharedRef<SWidget> Button = IAMenu::Chip(OwnerCopy, Choice.Label,
			[WeakThis, Action]()
			{
				if (const TSharedPtr<FIAModal> Pinned = WeakThis.Pin())
				{
					Pinned->Hide();
				}
				if (Action)
				{
					Action();
				}
			},
			Choice.bPrimary ? TFunction<bool()>([]() { return true; }) : TFunction<bool()>(nullptr), 150.f, 18);
		Buttons->AddSlot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)[ Button ];
		if (!FirstButton.IsValid() || Choice.bPrimary)
		{
			FirstButton = Button;
		}
	}

	TSharedRef<SBorder> Panel = SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(0.02f, 0.024f, 0.035f, 0.98f))
		.Padding(FMargin(36.f, 28.f))
		[
			SNew(SBox).WidthOverride(560.f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(STextBlock).Text(Title).Font(IAMenu::Font(28, true)).ColorAndOpacity(IAMenu::Accent)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f, 0.f, 0.f)
				[
					SNew(SBox).HeightOverride(2.f)
					[
						SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(1.f, 0.42f, 0.f, 0.55f))
					]
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 16.f, 0.f, 22.f)
				[
					SNew(STextBlock)
					.Text_Lambda([Body]() { return Body ? Body() : FText::GetEmpty(); })
					.AutoWrapText(true)
					.Font(IAMenu::Font(17))
					.ColorAndOpacity(FLinearColor(0.88f, 0.9f, 0.95f))
				]
				+ SVerticalBox::Slot().AutoHeight()
				[
					Buttons
				]
			]
		];
	IAMenu::KeepNavigationInside(Panel.Get());
	DialogHost->SetContent(Panel);

	bOpen = true;
	Layer->SetVisibility(EVisibility::Visible);
	if (FirstButton.IsValid())
	{
		FSlateApplication::Get().SetKeyboardFocus(FirstButton, EFocusCause::SetDirectly);
	}
}

void FIAModal::Hide()
{
	if (!bOpen)
	{
		return;
	}
	bOpen = false;
	AutoCancelAt = 0.0;
	if (Layer.IsValid())
	{
		Layer->SetVisibility(EVisibility::Collapsed);
	}
	if (DialogHost.IsValid())
	{
		DialogHost->SetContent(SNullWidget::NullWidget);
	}
	if (const TSharedPtr<SWidget> Restore = RestoreFocus.Pin())
	{
		FSlateApplication::Get().SetKeyboardFocus(Restore, EFocusCause::SetDirectly);
	}
}

void FIAModal::Cancel()
{
	if (!bOpen)
	{
		return;
	}
	const TFunction<void()> Action = CancelAction;
	IAMenu::Click(Owner);
	Hide();
	if (Action)
	{
		Action();
	}
}

float FIAModal::GetSecondsLeft() const
{
	return AutoCancelAt > 0.0 ? FMath::Max(0.f, static_cast<float>(AutoCancelAt - FPlatformTime::Seconds())) : 0.f;
}

void FIAModal::TickAutoCancel()
{
	if (bOpen && AutoCancelAt > 0.0 && FPlatformTime::Seconds() >= AutoCancelAt)
	{
		Cancel();
	}
}

namespace IAMenu
{

	TSharedRef<SWidget> NavButton(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, const FText& Hint,
		TFunction<void()> OnClick, float Width)
	{
		const TSharedRef<TWeakPtr<SButton>> Holder = MakeShared<TWeakPtr<SButton>>();
		TSharedPtr<SButton> Button;

		SAssignNew(Button, SButton)
			.ButtonStyle(&InvisibleButtonStyle())
			.ContentPadding(FMargin(0.f))
			.OnHovered_Lambda([Owner]() { HoverTick(Owner); })
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
			.OnHovered_Lambda([Owner]() { HoverTick(Owner); })
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

	TSharedRef<SWidget> Row(const FText& Label, TSharedRef<SWidget> Content, float LabelWidth, const FText& Tooltip)
	{
		return SNew(SHorizontalBox)
			.ToolTip(Tooltip.IsEmpty() ? TSharedPtr<IToolTip>() : TSharedPtr<IToolTip>(MakeTip(Tooltip)))
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
