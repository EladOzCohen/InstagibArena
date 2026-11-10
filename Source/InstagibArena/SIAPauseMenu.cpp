// Instagib Arena

#include "SIAPauseMenu.h"
#include "IAMenuStyle.h"
#include "SIASettingsPanel.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

void SIAPauseMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	OnResume = InArgs._OnResume;
	const TFunction<void()> OnLeave = InArgs._OnLeave;
	const TFunction<void()> OnQuit = InArgs._OnQuit;

	TSharedRef<SWidget> MainPage = SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("PAUSED")) ]
		+ SVerticalBox::Slot().AutoHeight()
		[
			NavButton(Owner, INVTEXT("RESUME"), INVTEXT("Back to the match"), [this]() { if (OnResume) { OnResume(); } }, 400.f)
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			NavButton(Owner, INVTEXT("SETTINGS"), INVTEXT("Sound, mouse and display"), [this]() { bShowSettings = true; }, 400.f)
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			NavButton(Owner, INVTEXT("LEAVE MATCH"), INVTEXT("Go back to the main menu"), [OnLeave]() { if (OnLeave) { OnLeave(); } }, 400.f)
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			NavButton(Owner, INVTEXT("QUIT GAME"), FText::GetEmpty(), [OnQuit]() { if (OnQuit) { OnQuit(); } }, 400.f)
		];

	TSharedRef<SWidget> SettingsPage = SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("SETTINGS")) ]
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(SIASettingsPanel).OwnerController(Owner).ShowPlayerName(false)
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 22.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Chip(Owner, INVTEXT("BACK"), [this]() { bShowSettings = false; }, nullptr, 130.f, 18)
			]
		];

	// A dimmed screen with the menu in a column in the middle.
	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.58f))
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(PanelColor)
			.Padding(FMargin(48.f, 32.f))
			[
				SNew(SWidgetSwitcher)
				.WidgetIndex_Lambda([this]() { return bShowSettings ? 1 : 0; })
				+ SWidgetSwitcher::Slot() [ MainPage ]
				+ SWidgetSwitcher::Slot() [ SettingsPage ]
			]
		]
	];
}

FReply SIAPauseMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape)
	{
		Click(Owner);
		if (bShowSettings)
		{
			bShowSettings = false;
		}
		else if (OnResume)
		{
			OnResume();
		}
		return FReply::Handled();
	}
	return FReply::Unhandled();
}
