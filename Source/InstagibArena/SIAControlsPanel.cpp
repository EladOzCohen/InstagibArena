// Instagib Arena

#include "SIAControlsPanel.h"
#include "IAInputConfig.h"
#include "IAMenuStyle.h"
#include "InstagibArena.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

namespace
{
	FText LabelOf(FName Id)
	{
		for (const FIABindingInfo& Info : IAInput::GetBindings())
		{
			if (Id == Info.Id)
			{
				return FText::FromString(Info.Label);
			}
		}
		return FText::FromName(Id);
	}

	/** A key shown as a flat dark plate (used when the panel is read-only, and for the fixed keys). */
	TSharedRef<SWidget> Plate(TFunction<FText()> Text, float Width)
	{
		return SNew(SBox).WidthOverride(Width)
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(0.10f, 0.11f, 0.15f))
				.Padding(FMargin(16.f, 8.f))
				.HAlign(HAlign_Center)
				[
					SNew(STextBlock)
					.Text_Lambda([Text]() { return Text(); })
					.Font(Font(16, true))
					.ColorAndOpacity(FLinearColor(0.82f, 0.84f, 0.90f))
				]
			];
	}
}

void SIAControlsPanel::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	Modal = InArgs._Modal;
	bReadOnly = InArgs._ReadOnly;

	const float KeyWidth = 230.f;
	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);

	for (const FIABindingInfo& Info : IAInput::GetBindings())
	{
		const FName Id = Info.Id;
		TSharedRef<SWidget> KeyWidget = bReadOnly
			? Plate([Id]() { return KeyText(IAInput::GetKey(Id)); }, KeyWidth)
			: ChipDyn(Owner,
				[this, Id]() { return ListeningId == Id ? INVTEXT("Press a key...") : KeyText(IAInput::GetKey(Id)); },
				[this, Id]() { if (ListeningId == Id) { CancelListen(); } else { BeginListen(Id); } },
				[this, Id]() { return ListeningId == Id; }, KeyWidth, 16);

		Rows->AddSlot().AutoHeight().Padding(0.f, 4.f)
		[
			Row(FText::FromString(Info.Label), KeyWidget, 220.f)
		];
	}

	// Keys that cannot be changed.
	auto FixedRow = [&Rows](const TCHAR* Label, const TCHAR* Keys)
	{
		Rows->AddSlot().AutoHeight().Padding(0.f, 4.f)
		[
			Row(FText::FromString(Label), Plate([Keys]() { return FText::FromString(Keys); }, 230.f), 220.f)
		];
	};
	FixedRow(TEXT("Look around"), TEXT("Mouse"));
	FixedRow(TEXT("Dodge"), TEXT("Double-tap a move key"));
	FixedRow(TEXT("Pause menu"), TEXT("Esc"));

	if (!bReadOnly)
	{
		Rows->AddSlot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 14.f, 0.f)
			[
				Chip(Owner, INVTEXT("RESET TO DEFAULTS"), [this]() { ResetToDefaults(); }, nullptr, 0.f, 15)
			]
		];
		Rows->AddSlot().AutoHeight().Padding(0.f, 10.f, 0.f, 0.f)
		[
			Note([this, bMatch = InArgs._InMatch]()
			{
				if (!ListeningId.IsNone())
				{
					return INVTEXT("Press the new key or mouse button now. Esc cancels.");
				}
				return bMatch
					? INVTEXT("Key changes made during a match apply from the next match. Click an action, then press the new key.")
					: INVTEXT("Click an action, then press the new key. Changes apply when the next match starts.");
			}, [this]() { return ListeningId.IsNone() ? TextDim : FLinearColor(1.f, 0.75f, 0.35f); })
		];
	}

	ChildSlot
	[
		Rows
	];
}

void SIAControlsPanel::BeginListen(FName Id)
{
	ListeningId = Id;
}

void SIAControlsPanel::CancelListen()
{
	ListeningId = NAME_None;
}

void SIAControlsPanel::ResetToDefaults()
{
	CancelListen();
	IAInput::ResetAll();
	UE_LOG(LogInstagib, Log, TEXT("Controls: all keys reset to defaults"));
}

void SIAControlsPanel::DevReset()
{
	ResetToDefaults();
}

void SIAControlsPanel::DevRebind(FName Id, FKey Key)
{
	Bind(Id, Key);
}

void SIAControlsPanel::Bind(FName Id, FKey Key)
{
	CancelListen();
	if (!Key.IsValid() || Key == IAInput::GetKey(Id))
	{
		return;
	}

	const FName Other = IAInput::FindActionUsingKey(Key, Id);
	if (Other.IsNone())
	{
		IAInput::SetKey(Id, Key);
		UE_LOG(LogInstagib, Log, TEXT("Controls: %s bound to %s"), *Id.ToString(), *Key.ToString());
		return;
	}

	// The key belongs to another action: offer to swap.
	const FKey OldKey = IAInput::GetKey(Id);
	auto DoSwap = [Id, Other, Key, OldKey]()
	{
		IAInput::SetKey(Other, OldKey);
		IAInput::SetKey(Id, Key);
		UE_LOG(LogInstagib, Log, TEXT("Controls: %s bound to %s, %s now uses %s"), *Id.ToString(), *Key.ToString(), *Other.ToString(), *OldKey.ToString());
	};

	if (!Modal.IsValid())
	{
		DoSwap();
		return;
	}

	const FText Body = FText::Format(INVTEXT("{0} is already used for \"{1}\". Swap the keys? \"{1}\" will get {2}."),
		KeyText(Key), LabelOf(Other), KeyText(OldKey));
	Modal->Show(INVTEXT("KEY ALREADY IN USE"), [Body]() { return Body; },
		{ { INVTEXT("SWAP"), DoSwap, true }, { INVTEXT("CANCEL"), nullptr, false } });
}

FReply SIAControlsPanel::OnPreviewKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (ListeningId.IsNone())
	{
		return FReply::Unhandled();
	}

	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Escape)
	{
		CancelListen();
		return FReply::Handled();
	}
	// Only keyboard and mouse keys can be bound.
	if (!Key.IsValid() || Key.IsGamepadKey() || Key.IsTouch() || Key.IsAxis1D() || Key.IsAxis2D() || Key.IsAxis3D())
	{
		return FReply::Handled();
	}
	Bind(ListeningId, Key);
	return FReply::Handled();
}

FReply SIAControlsPanel::OnPreviewMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (ListeningId.IsNone())
	{
		return FReply::Unhandled();
	}
	Bind(ListeningId, MouseEvent.GetEffectingButton());
	return FReply::Handled();
}

FReply SIAControlsPanel::OnMouseWheel(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (ListeningId.IsNone() || FMath::IsNearlyZero(MouseEvent.GetWheelDelta()))
	{
		return FReply::Unhandled();
	}
	Bind(ListeningId, MouseEvent.GetWheelDelta() > 0.f ? EKeys::MouseScrollUp : EKeys::MouseScrollDown);
	return FReply::Handled();
}
