// Instagib Arena

#include "SIAPauseMenu.h"
#include "IAMenuStyle.h"
#include "IASettings.h"
#include "InstagibArena.h"
#include "SIASettingsPanel.h"
#include "Framework/Application/SlateApplication.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SDPIScaler.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

void SIAPauseMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	OnResume = InArgs._OnResume;
	OnLeave = InArgs._OnLeave;
	OnQuit = InArgs._OnQuit;
	Modal = MakeShared<FIAModal>(Owner);


#if !UE_BUILD_SHIPPING
	// Developer check for screenshots: -IAPauseTab=N opens the settings on tab N.
	int32 TestTab = -1;
	if (FParse::Value(FCommandLine::Get(), TEXT("IAPauseTab="), TestTab))
	{
		InitialSettingsTab = FMath::Clamp(TestTab, 0, 3);
		bShowSettings = true;
	}
#endif
	Script.Load(TEXT("IAPauseScript"));
	ShowSettings(bShowSettings);
}

TSharedRef<SWidget> SIAPauseMenu::BuildMainPage()
{
	const TFunction<void()> Leave = OnLeave;
	const TFunction<void()> Quit = OnQuit;
	return SNew(SBox).WidthOverride(400.f)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("PAUSED")) ]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("RESUME"), INVTEXT("Back to the match"), [this]() { if (OnResume) { OnResume(); } }, 400.f)
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("SETTINGS"), INVTEXT("Gameplay, video, audio and controls"), [this]() { ShowSettings(true); }, 400.f)
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("LEAVE MATCH"), INVTEXT("Go back to the main menu"), [Leave]() { if (Leave) { Leave(); } }, 400.f)
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("QUIT GAME"), FText::GetEmpty(),
					[this, Quit]()
					{
						Modal->Show(INVTEXT("QUIT GAME?"), []() { return INVTEXT("Do you really want to leave Instagib Arena?"); },
							{ { INVTEXT("QUIT"), [Quit]() { if (Quit) { Quit(); } }, false }, { INVTEXT("STAY"), nullptr, true } });
					}, 400.f)
			]
		];
}

void SIAPauseMenu::ShowSettings(bool bShow)
{
	bShowSettings = bShow;

	// A dimmed screen. The main page is a small card in the middle; the settings fill the height of the screen.
	auto Install = [this](TSharedRef<SWidget> Content, bool bTall)
	{
		ContentRoot = Content;
		ChildSlot
		[
			SNew(SDPIScaler)
			.DPIScale_Lambda([]() { return IASettings::GetUiScale(); })
			[
				SNew(SOverlay)
				+ SOverlay::Slot()
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.58f))
					.HAlign(HAlign_Center)
					.VAlign(bTall ? VAlign_Fill : VAlign_Center)
					.Padding(bTall ? FMargin(0.f, 28.f) : FMargin(0.f))
					[
						SNew(SBorder)
						.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
						.BorderBackgroundColor(PanelColor)
						.Padding(FMargin(48.f, 32.f))
						[
							Content
						]
					]
				]
				+ SOverlay::Slot() [ Modal->GetWidget() ]
			]
		];
	};

	if (!bShow)
	{
		Install(BuildMainPage(), false);
		return;
	}

	TSharedRef<SIASettingsPanel> SettingsWidget = SNew(SIASettingsPanel)
		.OwnerController(Owner)
		.ShowPlayerName(false)
		.InMatch(true)
		.Modal(Modal)
		.InitialTab(InitialSettingsTab);
	SettingsPanel = SettingsWidget;

	Install(
		SNew(SBox).WidthOverride(840.f)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("SETTINGS")) ]
			+ SVerticalBox::Slot().FillHeight(1.f) [ SettingsWidget ]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 16.f, 0.f, 0.f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth()
				[
					Chip(Owner, INVTEXT("BACK"), [this]() { ShowSettings(false); }, nullptr, 130.f, 18)
				]
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(18.f, 0.f, 0.f, 0.f)
				[
					Note([]() { return INVTEXT("New keys apply from the next match."); })
				]
			]
		], true);
}

void SIAPauseMenu::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

	const FString Next = Script.Step(InDeltaTime);
	if (!Next.IsEmpty())
	{
		DevCommand(Next);
	}

	// Keep the keyboard working: when nothing in the menu has focus, give it to the first button.
	if (!Modal->IsOpen())
	{
		const TSharedPtr<SWidget> Focused = FSlateApplication::Get().GetKeyboardFocusedWidget();
		if (!Focused.IsValid() || Focused.Get() == this)
		{
			if (ContentRoot.IsValid())
			{
				FocusFirst(ContentRoot.ToSharedRef());
			}
		}
	}
}

FReply SIAPauseMenu::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	return FReply::Handled().SetUserFocus(SharedThis(this), EFocusCause::Mouse);
}

FReply SIAPauseMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape)
	{
		if (Modal->IsOpen())
		{
			Modal->Cancel();
			return FReply::Handled();
		}
		Click(Owner);
		if (bShowSettings)
		{
			ShowSettings(false);
		}
		else if (OnResume)
		{
			OnResume();
		}
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

void SIAPauseMenu::DevCommand(const FString& Command)
{
	FString Name = Command;
	FString Value;
	Command.Split(TEXT("="), &Name, &Value);
	UE_LOG(LogInstagib, Log, TEXT("PauseScript: %s"), *Command);

	if (Name == TEXT("key")) { SimulateKey(FKey(*Value)); }
	else if (Name == TEXT("settings")) { InitialSettingsTab = FCString::Atoi(*Value); ShowSettings(true); }
	else if (Name == TEXT("modal-cancel")) { Modal->Cancel(); }
	else if (const TSharedPtr<SIASettingsPanel> Pinned = SettingsPanel.Pin())
	{
		Pinned->DevCommand(Command);
	}
}
