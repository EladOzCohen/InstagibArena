// Instagib Arena

#include "SIAMainMenu.h"
#include "IAAudioSubsystem.h"
#include "IACampaignSubsystem.h"
#include "IACharacterRoster.h"
#include "IAInputConfig.h"
#include "IAMapList.h"
#include "IAMapPreview.h"
#include "IAMenuStyle.h"
#include "InstagibArena.h"
#include "SIAControlsPanel.h"
#include "SIASettingsPanel.h"
#include "SIAWelcome.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformApplicationMisc.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SDPIScaler.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

// ---------------------------------------------------------------- construction

void SIAMainMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	OnCharacterChanged = InArgs._OnCharacterChanged;
	OnPageChanged = InArgs._OnPageChanged;

	Setup.Load();
	JoinAddress = IASettings::GetJoinAddress();
	Modal = MakeShared<FIAModal>(Owner);

	// Coming back after a failed or lost connection: show it where the player can retry.
	if (!InArgs._InitialError.IsEmpty())
	{
		JoinStatus = FText::FromString(InArgs._InitialError);
		JoinStatusColor = FLinearColor(1.f, 0.35f, 0.3f);
		MultiplayerTab = 1;
		Page = EPage::Multiplayer;
	}

	SAssignNew(PageHost, SBox);
	SAssignNew(WelcomeHost, SBox);

	// The column has one width per screen. Everything inside is scaled by the player's UI scale on top of the automatic one.
	ChildSlot
	[
		SNew(SDPIScaler)
		.DPIScale_Lambda([]() { return IASettings::GetUiScale(); })
		[
			SNew(SOverlay)
			// Darkens the top and bottom edge of the picture a little, so that the eye stays in the middle.
			+ SOverlay::Slot()
			[
				Gradient(Orient_Vertical, {
					TPair<float, FLinearColor>(0.00f, FLinearColor(0.f, 0.f, 0.f, 0.42f)),
					TPair<float, FLinearColor>(0.22f, FLinearColor(0.f, 0.f, 0.f, 0.f)),
					TPair<float, FLinearColor>(0.80f, FLinearColor(0.f, 0.f, 0.f, 0.f)),
					TPair<float, FLinearColor>(1.00f, FLinearColor(0.f, 0.f, 0.f, 0.38f)) })
			]
			// The panel fades out into the picture instead of ending in a hard edge.
			+ SOverlay::Slot().HAlign(HAlign_Left)
			[
				SNew(SBox)
				.Padding_Lambda([this]() { return FMargin(PageWidth() - 1.f, 0.f, 0.f, 0.f); })
				[
					SNew(SBox)
					.WidthOverride(240.f)
					[
						Gradient(Orient_Horizontal, {
							TPair<float, FLinearColor>(0.00f, PanelColor),
							TPair<float, FLinearColor>(0.35f, FLinearColor(PanelColor.R, PanelColor.G, PanelColor.B, PanelColor.A * 0.45f)),
							TPair<float, FLinearColor>(1.00f, FLinearColor(PanelColor.R, PanelColor.G, PanelColor.B, 0.f)) })
					]
				]
			]
			+ SOverlay::Slot().HAlign(HAlign_Left)
			[
				SNew(SBox)
				.WidthOverride_Lambda([this]() { return FOptionalSize(PageWidth()); })
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(PanelColor)
					.Padding(FMargin(56.f, 36.f, 40.f, 22.f))
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot().FillHeight(1.f)
						[
							PageHost.ToSharedRef()
						]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 10.f, 0.f, 0.f)
						[
							SNew(SBox).HeightOverride(1.f)
							[
								SNew(SBorder)
								.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
								.BorderBackgroundColor(FLinearColor(1.f, 1.f, 1.f, 0.07f))
							]
						]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f, 0.f, 0.f)
						[
							SNew(STextBlock)
							.Text(FText::FromString(FString::Printf(TEXT("v%s    github.com/EladOzCohen/InstagibArena"), IASettings::GameVersion)))
							.Font(Font(12))
							.ColorAndOpacity(FLinearColor(TextDim.R, TextDim.G, TextDim.B, 0.85f))
						]
					]
				]
			]
			+ SOverlay::Slot() [ WelcomeHost.ToSharedRef() ]
			+ SOverlay::Slot() [ Modal->GetWidget() ]
		]
	];

	// Back from a campaign match: open on the ladder, on the match that was just played (or the next one after a win).
	if (const APlayerController* PC = Owner.Get())
	{
		UGameInstance* Instance = PC->GetGameInstance();
		UIACampaignSubsystem* Camp = Instance ? Instance->GetSubsystem<UIACampaignSubsystem>() : nullptr;
		if (Camp && Camp->bOpenLadderOnMenu && Camp->HasCampaign())
		{
			Camp->bOpenLadderOnMenu = false;
			Page = EPage::Campaign;
			CampaignView = 2;
			const bool bWon = Camp->LastResult.bWon;
			CampaignSelected = (Camp->LastResult.Match >= 0 && !bWon) ? Camp->LastResult.Match : FMath::Min(Camp->GetNextMatch(), IACampaign::MatchCount - 1);
		}
	}

	PageHost->SetContent(BuildPage(Page));

	if (OnPageChanged)
	{
		OnPageChanged(static_cast<int32>(Page));
	}
	if (OnCharacterChanged)
	{
		OnCharacterChanged(Setup.CharacterIndex);
	}

	Script.Load(TEXT("IAMenuScript"));

	// First launch (or after "Reset tutorial"): the welcome overlay.
	bool bForceWelcome = false;
#if !UE_BUILD_SHIPPING
	bForceWelcome = FParse::Param(FCommandLine::Get(), TEXT("IAFirstRun"));
	if (FParse::Param(FCommandLine::Get(), TEXT("IASkipWelcome")))
	{
		IASettings::SetTutorialDone(true);
	}
#endif
	if (bForceWelcome || (!IASettings::IsTutorialDone() && InArgs._InitialError.IsEmpty()))
	{
		ShowWelcome(0);
	}
}

float SIAMainMenu::PageWidth() const
{
	switch (Page)
	{
	case EPage::Custom:
	case EPage::Multiplayer: return 720.f;
	case EPage::Settings:
	case EPage::HowToPlay:
	case EPage::Campaign:    return 840.f;
	default:                 return 640.f;
	}
}

TSharedRef<SWidget> SIAMainMenu::BuildPage(EPage Which)
{
	switch (Which)
	{
	case EPage::Custom:      return BuildCustomPage();
	case EPage::Multiplayer: return BuildMultiplayerPage();
	case EPage::Character:   return BuildCharacterPage();
	case EPage::Settings:    return BuildSettingsPage();
	case EPage::Campaign:    return BuildCampaignPage();
	case EPage::Credits:     return BuildCreditsPage();
	case EPage::HowToPlay:   return BuildHowToPlayPage();
	default:                 return BuildMainPage();
	}
}

void SIAMainMenu::GoTo(EPage NewPage)
{
	Setup.Save();
	Page = NewPage;
	PageTime = 0.f;
	PageHost->SetContent(BuildPage(NewPage));
	if (OnPageChanged)
	{
		OnPageChanged(static_cast<int32>(NewPage));
	}
	// The first Tick after this puts the keyboard focus on the first button of the new screen.
	FSlateApplication::Get().SetKeyboardFocus(SharedThis(this), EFocusCause::SetDirectly);
}

void SIAMainMenu::ShowPageForTest(int32 PageIndex, int32 Tab)
{
	Page = static_cast<EPage>(FMath::Clamp(PageIndex, 0, 7));
	MultiplayerTab = FMath::Clamp(Tab, 0, 1);
	SettingsTab = FMath::Clamp(Tab, 0, 3);
	CampaignView = FMath::Clamp(Tab, 0, 2);   // campaign page: 0 home, 1 new campaign, 2 the ladder
	PageTime = 1.f;
	PageHost->SetContent(BuildPage(Page));
	if (OnPageChanged)
	{
		OnPageChanged(static_cast<int32>(Page));
	}
}

void SIAMainMenu::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

	const FString Next = Script.Step(InDeltaTime);
	if (!Next.IsEmpty())
	{
		DevCommand(Next);
	}

	// Slide and fade in the screen that has just opened.
	if (PageTime < 1.f)
	{
		PageTime = FMath::Min(1.f, PageTime + InDeltaTime / 0.22f);
	}
	const float Eased = 1.f - FMath::Pow(1.f - PageTime, 3.f);
	PageHost->SetRenderOpacity(Eased);
	PageHost->SetRenderTransform(FSlateRenderTransform(FVector2D((1.f - Eased) * -34.f, 0.f)));

	// Keep the keyboard working: when nothing in the menu has focus, give it to the first button.
	if (!Modal->IsOpen())
	{
		const TSharedPtr<SWidget> Focused = FSlateApplication::Get().GetKeyboardFocusedWidget();
		if (!Focused.IsValid() || Focused.Get() == this)
		{
			if (Welcome.IsValid())
			{
				FocusFirst(WelcomeHost.ToSharedRef());
			}
			else
			{
				FocusFirst(PageHost.ToSharedRef());
			}
		}
	}
}

FReply SIAMainMenu::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	// A click on empty space: take the focus back so that Esc and the arrow keys keep working.
	return FReply::Handled().SetUserFocus(SharedThis(this), EFocusCause::Mouse);
}

FReply SIAMainMenu::OnPreviewKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	// Arrow keys and Tab move the focus: inside the message box while one is open, inside the welcome overlay, or on the screen.
	// This runs before the focused button sees the key (a button would answer with Slate's own navigation, which does not
	// know about our layout).
	const TSharedPtr<SWidget> NavRoot = Modal->IsOpen() ? Modal->GetDialogWidget()
		: (Welcome.IsValid() ? TSharedPtr<SWidget>(WelcomeHost) : TSharedPtr<SWidget>(PageHost));
	if (NavRoot.IsValid() && HandleNavKey(NavRoot.ToSharedRef(), InKeyEvent))
	{
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

FReply SIAMainMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape)
	{
		if (Modal->IsOpen())
		{
			Modal->Cancel();
			return FReply::Handled();
		}
		if (Welcome.IsValid())
		{
			return FReply::Unhandled();
		}
		if (Page != EPage::Main)
		{
			Click(Owner);
			GoTo(EPage::Main);
		}
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

TSharedRef<SWidget> SIAMainMenu::BuildBackButton()
{
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth()
		[
			Chip(Owner, INVTEXT("BACK"), [this]() { GoTo(EPage::Main); }, nullptr, 130.f, 18)
		];
}

TSharedRef<SWidget> SIAMainMenu::Frame(const FText& Title, TSharedRef<SWidget> Body, TSharedRef<SWidget> Footer)
{
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(Title) ]
		+ SVerticalBox::Slot().FillHeight(1.f) [ ScrollArea(Body) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 16.f, 0.f, 0.f) [ Footer ];
}

// ---------------------------------------------------------------- welcome overlay

void SIAMainMenu::ShowWelcome(int32 Step)
{
	Welcome = SNew(SIAWelcome)
		.OwnerController(Owner)
		.OnFinished([this]()
		{
			Welcome.Reset();
			WelcomeHost->SetContent(SNullWidget::NullWidget);
			FSlateApplication::Get().SetKeyboardFocus(SharedThis(this), EFocusCause::SetDirectly);
		});
	WelcomeHost->SetContent(Welcome.ToSharedRef());
	Welcome->ShowStep(Step);
}

// ---------------------------------------------------------------- main screen

TSharedRef<SWidget> SIAMainMenu::BuildMainPage()
{
	// The entries shrink to fit when the window is small or the UI scale is large, instead of running off the screen.
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().FillHeight(1.f).VAlign(VAlign_Center)
		[
			SNew(SScaleBox)
			.Stretch(EStretch::ScaleToFit)
			.StretchDirection(EStretchDirection::DownOnly)
			.HAlign(HAlign_Left)
			.VAlign(VAlign_Center)
			[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight()
			[
				// The logo: white and orange, spaced out, with a soft shadow so that it reads over any picture.
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth()
				[
					SNew(STextBlock)
					.Text(INVTEXT("INSTAGIB"))
					.Font(SpacedFont(46, true, 60))
					.ShadowOffset(FVector2D(0.f, 3.f))
					.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.55f))
					.ColorAndOpacity(FLinearColor(0.96f, 0.97f, 1.f))
				]
				+ SHorizontalBox::Slot().AutoWidth().Padding(16.f, 0.f, 0.f, 0.f)
				[
					SNew(STextBlock)
					.Text(INVTEXT("ARENA"))
					.Font(SpacedFont(46, true, 60))
					.ShadowOffset(FVector2D(0.f, 3.f))
					.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.55f))
					.ColorAndOpacity(Accent)
				]
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(4.f, 8.f, 0.f, 0.f)
			[
				// A bright bar that thins out into a faint line.
				SNew(SBox).HeightOverride(4.f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth()
					[
						SNew(SBox).WidthOverride(72.f)
						[
							SNew(SBorder)
							.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
							.BorderBackgroundColor(Accent)
						]
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
					[
						SNew(SBox).WidthOverride(300.f).HeightOverride(2.f)
						[
							Gradient(Orient_Horizontal, {
								TPair<float, FLinearColor>(0.f, FLinearColor(1.f, 0.42f, 0.f, 0.7f)),
								TPair<float, FLinearColor>(1.f, FLinearColor(1.f, 0.42f, 0.f, 0.f)) })
						]
					]
				]
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(4.f, 10.f, 0.f, 22.f)
			[
				SNew(STextBlock)
				.Text(INVTEXT("One shot. One kill."))
				.Font(SpacedFont(18, false, 70))
				.ShadowOffset(FVector2D(0.f, 1.f))
				.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.6f))
				.ColorAndOpacity(FLinearColor(0.74f, 0.76f, 0.82f))
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("QUICK PLAY"), INVTEXT("Jump into a match with your last settings"), [this]() { StartGame(false); })
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("CAMPAIGN"), INVTEXT("The Apex League: 20 matches, 5 worlds"), [this]() { CampaignView = 0; bCampaignResetAsked = false; GoTo(EPage::Campaign); })
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("CUSTOM GAME"), INVTEXT("Choose the map, bots and rules"), [this]() { GoTo(EPage::Custom); })
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("MULTIPLAYER"), INVTEXT("Host a game or join your friends"), [this]() { GoTo(EPage::Multiplayer); })
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("CHARACTER"), INVTEXT("Pick who you play as"), [this]() { GoTo(EPage::Character); })
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("HOW TO PLAY"), INVTEXT("The goal and all controls"), [this]() { GoTo(EPage::HowToPlay); })
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("SETTINGS"), INVTEXT("Gameplay, video, audio and controls"), [this]() { SettingsTab = 0; GoTo(EPage::Settings); })
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("CREDITS"), FText::GetEmpty(), [this]() { GoTo(EPage::Credits); })
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				NavButton(Owner, INVTEXT("QUIT"), FText::GetEmpty(), [this]() { QuitGame(); })
			]
			]
		];
}

// ---------------------------------------------------------------- map card

void SIAMainMenu::ChangeMap(int32 Delta)
{
	Setup.MapIndex = (Setup.MapIndex + Delta + IAMaps::Count) % IAMaps::Count;
}

TSharedRef<SWidget> SIAMainMenu::BuildMapCard()
{
	auto Info = [this]() -> const FIAMapInfo& { return IAMaps::List[FMath::Clamp(Setup.MapIndex, 0, IAMaps::Count - 1)]; };

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				Chip(Owner, INVTEXT("<"), [this]() { ChangeMap(-1); }, nullptr, 46.f, 22)
			]
			+ SHorizontalBox::Slot().AutoWidth().Padding(10.f, 0.f)
			[
				IAMapPreview::MakeThumbnailWidget([this]() { return Setup.MapIndex; }, FVector2D(448.f, 252.f))
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				Chip(Owner, INVTEXT(">"), [this]() { ChangeMap(1); }, nullptr, 46.f, 22)
			]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 10.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().FillWidth(1.f)
			[
				SNew(STextBlock)
				.Text_Lambda([Info]() { return FText::FromString(Info().DisplayName); })
				.Font(Font(24, true))
				.ColorAndOpacity(FLinearColor::White)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text_Lambda([this]() { return FText::Format(INVTEXT("{0} / {1}"), FText::AsNumber(Setup.MapIndex + 1), FText::AsNumber(IAMaps::Count)); })
				.Font(Font(15))
				.ColorAndOpacity(TextDim)
			]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 2.f, 0.f, 0.f)
		[
			Note([Info]() { return FText::FromString(Info().Description); })
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 8.f)
		[
			SNew(STextBlock)
			.Text_Lambda([Info]() { return FText::Format(INVTEXT("Recommended: {0}"), IAMapPreview::RecommendedPlayers(Info())); })
			.Font(Font(15, true))
			.ColorAndOpacity(Accent)
		];
}

// ---------------------------------------------------------------- game rules (Custom Game and Host)

TSharedRef<SWidget> SIAMainMenu::BuildSetupRows()
{
	const int32 ScoreStep = 5;

	return SNew(SVerticalBox)

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Game type"),
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
				[
					Chip(Owner, INVTEXT("Free For All"), [this]() { Setup.GameType = 0; }, [this]() { return Setup.GameType == 0; }, 124.f, 17)
				]
				+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
				[
					Chip(Owner, INVTEXT("Team Deathmatch"), [this]() { Setup.GameType = 1; }, [this]() { return Setup.GameType == 1; }, 154.f, 17)
				]
				+ SHorizontalBox::Slot().AutoWidth()
				[
					Chip(Owner, INVTEXT("Capture the Flag"), [this]() { Setup.GameType = 2; }, [this]() { return Setup.GameType == 2; }, 156.f, 17)
				],
				170.f, INVTEXT("Free For All: everyone for themselves. Team Deathmatch: two teams, red and blue. Capture the Flag: steal the enemy flag and bring it home."))
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Character"),
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 14.f, 0.f)
				[
					SNew(STextBlock)
					.Text_Lambda([this]() { return FText::FromString(IACharacters::GetLook(Setup.CharacterIndex).Name); })
					.Font(Font(18, true))
					.ColorAndOpacity(Accent)
				]
				+ SHorizontalBox::Slot().AutoWidth()
				[
					Chip(Owner, INVTEXT("CHANGE"), [this]() { GoTo(EPage::Character); }, nullptr, 90.f, 14)
				])
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Bots"),
				Stepper(Owner,
					[this]() { return Setup.BotCount == 0 ? INVTEXT("None") : FText::AsNumber(Setup.BotCount); },
					[this]() { Setup.BotCount = (Setup.BotCount <= 2) ? 0 : Setup.BotCount - 1; },
					[this]() { Setup.BotCount = (Setup.BotCount == 0) ? 2 : FMath::Min(10, Setup.BotCount + 1); },
					190.f),
				170.f, INVTEXT("Computer players. With none, you wait alone for other humans."))
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Bot skill"),
				Stepper(Owner,
					[this]() { return IABots::SkillName(Setup.BotSkill); },
					[this]() { Setup.BotSkill = FMath::Max(0, Setup.BotSkill - 1); },
					[this]() { Setup.BotSkill = FMath::Min(IABots::SkillCount - 1, Setup.BotSkill + 1); },
					190.f),
				170.f, INVTEXT("Seven levels, from Rookie (very forgiving) to Master (for professionals)."))
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			// Frags in free for all and team deathmatch, captures in capture the flag. Each mode keeps its own number.
			Row(TAttribute<FText>::CreateLambda([this]() { return Setup.IsCTF() ? INVTEXT("Capture limit") : INVTEXT("Score limit"); }),
				Stepper(Owner,
					[this]() { return Setup.IsCTF() ? FText::AsNumber(Setup.CaptureLimit) : (Setup.ScoreLimit == 0 ? INVTEXT("Off") : FText::AsNumber(Setup.ScoreLimit)); },
					[this, ScoreStep]()
					{
						if (Setup.IsCTF()) { Setup.CaptureLimit = FMath::Max(1, Setup.CaptureLimit - 1); }
						else { Setup.ScoreLimit = FMath::Max(0, Setup.ScoreLimit - ScoreStep); }
					},
					[this, ScoreStep]()
					{
						if (Setup.IsCTF()) { Setup.CaptureLimit = FMath::Min(10, Setup.CaptureLimit + 1); }
						else { Setup.ScoreLimit = FMath::Min(100, Setup.ScoreLimit + ScoreStep); }
					},
					190.f),
				170.f, INVTEXT("The match ends when someone (or a team) reaches this many frags, or in Capture the Flag when a team has captured the enemy flag this many times (1 to 10)."))
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Time limit"),
				Stepper(Owner,
					[this]() { return Setup.TimeLimit == 0 ? INVTEXT("Off") : FText::Format(INVTEXT("{0} min"), FText::AsNumber(Setup.TimeLimit)); },
					[this]() { Setup.TimeLimit = FMath::Max(0, Setup.TimeLimit - 1); },
					[this]() { Setup.TimeLimit = FMath::Min(30, Setup.TimeLimit + 1); },
					190.f),
				170.f, INVTEXT("The match ends when this time is up."))
		];
}

TSharedRef<SWidget> SIAMainMenu::BuildCustomPage()
{
	return Frame(INVTEXT("CUSTOM GAME"),
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ BuildMapCard() ]
		+ SVerticalBox::Slot().AutoHeight() [ BuildSetupRows() ],
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)
		[
			PrimaryButton(Owner, INVTEXT("START MATCH"), [this]() { StartGame(false); }, 300.f)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			BuildBackButton()
		]);
}

// ---------------------------------------------------------------- multiplayer

TSharedRef<SWidget> SIAMainMenu::BuildMultiplayerPage()
{
	const FString LocalAddress = IASettings::GetLocalAddressText();

	TSharedRef<SWidget> HostTab = SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ BuildMapCard() ]
		+ SVerticalBox::Slot().AutoHeight() [ BuildSetupRows() ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
			[
				Note([LocalAddress]()
				{
					return LocalAddress.IsEmpty()
						? INVTEXT("Friends join with your address. Open Command Prompt, type ipconfig and look for IPv4 Address.")
						: FText::Format(INVTEXT("Friends on your network join with this address:  {0}"), FText::FromString(LocalAddress));
				}, []() { return FLinearColor(0.95f, 0.85f, 0.5f); })
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(12.f, 0.f, 0.f, 0.f)
			[
				ChipDyn(Owner,
					[this]() { return FPlatformTime::Seconds() < CopiedUntil ? INVTEXT("COPIED!") : INVTEXT("COPY ADDRESS"); },
					[this, LocalAddress]()
					{
						if (!LocalAddress.IsEmpty())
						{
							FPlatformApplicationMisc::ClipboardCopy(*LocalAddress);
							CopiedUntil = FPlatformTime::Seconds() + 2.0;
							UE_LOG(LogInstagib, Log, TEXT("Menu: address %s copied to the clipboard"), *LocalAddress);
						}
					},
					[this]() { return FPlatformTime::Seconds() < CopiedUntil; }, 170.f, 14)
			]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
		[
			Note([]() { return INVTEXT("Over the internet: use a free virtual network such as Tailscale or ZeroTier, or forward UDP port 7777."); })
		];

	// The addresses joined before, as small buttons.
	TSharedRef<SWidget> RecentWidget = SNullWidget::NullWidget;
	{
		TSharedRef<SWrapBox> Recents = SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(6.f, 6.f));
		const TArray<FString> List = IASettings::GetRecentAddresses();
		for (const FString& Address : List)
		{
			Recents->AddSlot()
			[
				Chip(Owner, FText::FromString(Address), [this, Address]() { JoinAddress = Address; JoinStatus = FText::GetEmpty(); }, nullptr, 0.f, 14)
			];
		}
		if (List.Num() > 0)
		{
			RecentWidget = SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 6.f)
				[
					SNew(STextBlock).Text(INVTEXT("RECENT")).Font(Font(13, true)).ColorAndOpacity(TextDim)
				]
				+ SVerticalBox::Slot().AutoHeight() [ Recents ];
		}
	}

	TSharedRef<SWidget> JoinTab = SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Host address"),
				SNew(SBox).WidthOverride(320.f)
				[
					SNew(SEditableTextBox)
					.Text_Lambda([this]() { return FText::FromString(JoinAddress); })
					.HintText(INVTEXT("for example 192.168.1.20"))
					.Font(Font(18))
					.OnTextChanged_Lambda([this](const FText& NewText)
					{
						if (NewText.ToString() != JoinAddress) { JoinAddress = NewText.ToString(); JoinStatus = FText::GetEmpty(); }
					})
					.OnTextCommitted_Lambda([this](const FText&, ETextCommit::Type CommitType)
					{
						if (CommitType == ETextCommit::OnEnter) { JoinGame(); }
					})
				],
				170.f, INVTEXT("The IP address or name of the host, optionally with a port: 192.168.1.20:7777"))
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(170.f, 6.f, 0.f, 0.f)
		[
			Note([]() { return INVTEXT("Ask the host for the address shown on their Host screen."); })
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			Note([this]() { return JoinStatus; }, [this]() { return JoinStatusColor; })
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			RecentWidget
		];

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("MULTIPLAYER")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 14.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
			[
				Chip(Owner, INVTEXT("HOST A GAME"), [this]() { MultiplayerTab = 0; }, [this]() { return MultiplayerTab == 0; }, 180.f)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Chip(Owner, INVTEXT("JOIN A GAME"), [this]() { MultiplayerTab = 1; }, [this]() { return MultiplayerTab == 1; }, 180.f)
			]
		]
		+ SVerticalBox::Slot().FillHeight(1.f)
		[
			ScrollArea(
				SNew(SWidgetSwitcher)
				.WidgetIndex_Lambda([this]() { return MultiplayerTab; })
				+ SWidgetSwitcher::Slot() [ HostTab ]
				+ SWidgetSwitcher::Slot() [ JoinTab ])
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 16.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)
			[
				SNew(SWidgetSwitcher)
				.WidgetIndex_Lambda([this]() { return MultiplayerTab; })
				+ SWidgetSwitcher::Slot() [ PrimaryButton(Owner, INVTEXT("HOST GAME"), [this]() { StartGame(true); }, 300.f) ]
				+ SWidgetSwitcher::Slot() [ PrimaryButton(Owner, INVTEXT("JOIN GAME"), [this]() { JoinGame(); }, 300.f) ]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				BuildBackButton()
			]
		];
}

// ---------------------------------------------------------------- character, settings, how to play, credits

TSharedRef<SWidget> SIAMainMenu::BuildCharacterPage()
{
	TSharedRef<SUniformGridPanel> Grid = SNew(SUniformGridPanel).SlotPadding(FMargin(3.f));
	for (int32 Index = 0; Index < IACharacters::LookCount; ++Index)
	{
		// Four per row: with five the longer names (Razorclaw, Gearhead, Brimstone) were cut off.
		Grid->AddSlot(Index % 4, Index / 4)
		[
			Chip(Owner, FText::FromString(IACharacters::GetLook(Index).Name), [this, Index]() { SelectCharacter(Index); },
				[this, Index]() { return Setup.CharacterIndex == Index; }, 0.f, 14)
		];
	}

	return Frame(INVTEXT("CHARACTER"),
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(STextBlock)
			.Text_Lambda([this]() { return FText::FromString(IACharacters::GetLook(Setup.CharacterIndex).Name); })
			.Font(Font(40, true))
			.ColorAndOpacity(FLinearColor::White)
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(2.f, 0.f, 0.f, 18.f)
		[
			SNew(STextBlock)
			.Text_Lambda([this]() { return FText::FromString(IACharacters::GetLook(Setup.CharacterIndex).Title); })
			.Font(Font(18))
			.ColorAndOpacity(Accent)
		]
		+ SVerticalBox::Slot().AutoHeight() [ Grid ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			Note([]() { return INVTEXT("Your choice is remembered, and other players see you as this character."); })
		],
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth()
		[
			Chip(Owner, INVTEXT("DONE"), [this]() { GoTo(EPage::Main); }, nullptr, 130.f, 18)
		]);
}

TSharedRef<SWidget> SIAMainMenu::BuildSettingsPage()
{
	TSharedRef<SIASettingsPanel> Panel = SNew(SIASettingsPanel)
		.OwnerController(Owner)
		.ShowPlayerName(true)
		.Modal(Modal)
		.InitialTab(SettingsTab)
		.OnResetTutorial([this]()
		{
			IASettings::SetTutorialDone(false);
			GoTo(EPage::Main);
			ShowWelcome(0);
		});
	SettingsPanel = Panel;

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("SETTINGS")) ]
		+ SVerticalBox::Slot().FillHeight(1.f) [ Panel ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 16.f, 0.f, 0.f) [ BuildBackButton() ];
}

TSharedRef<SWidget> SIAMainMenu::BuildHowToPlayPage()
{
	auto Line = [](const TCHAR* Text, bool bBold = false)
	{
		return SNew(STextBlock)
			.Text(FText::FromString(Text))
			.AutoWrapText(true)
			.Font(Font(bBold ? 20 : 16, bBold))
			.ColorAndOpacity(bBold ? FLinearColor::White : FLinearColor(0.82f, 0.84f, 0.90f));
	};

	return Frame(INVTEXT("HOW TO PLAY"),
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(TEXT("The goal"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f)
		[
			Line(TEXT("Everyone carries the same rifle and every hit is a kill. Frag the other players before they frag you. The first to the score limit, or the best when the time runs out, wins."))
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(TEXT("Capture the Flag"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f)
		[
			Line(TEXT("Two teams, red and blue. Each team has a flag on its base. Touch the enemy flag to take it, then run back and touch your own base to score a capture. "
				"You can only capture while your own flag is at home. If your flag is taken, kill the carrier. If a carrier dies the flag drops: your team returns it by touching it, "
				"and an enemy can pick it up. A dropped flag goes home by itself after 15 seconds. The first team to the capture limit wins, or the team with more captures when the time is up."))
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 8.f) [ Line(TEXT("Controls"), true) ]
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(SIAControlsPanel).OwnerController(Owner).ReadOnly(true)
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 18.f, 0.f, 4.f) [ Line(TEXT("Tips"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(TEXT("Keep moving and dodge: a target that stands still is easy to hit.")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(TEXT("Listen for footsteps and landings to find enemies.")) ]
		+ SVerticalBox::Slot().AutoHeight() [ Line(TEXT("Esc opens the pause menu. In multiplayer the match keeps running.")) ],
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)
		[
			Chip(Owner, INVTEXT("CHANGE CONTROLS"), [this]() { SettingsTab = 3; GoTo(EPage::Settings); }, nullptr, 0.f, 16)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			BuildBackButton()
		]);
}

TSharedRef<SWidget> SIAMainMenu::BuildCreditsPage()
{
	auto Line = [](const FText& Text, bool bBold = false)
	{
		return SNew(STextBlock)
			.Text(Text)
			.AutoWrapText(true)
			.Font(Font(bBold ? 20 : 16, bBold))
			.ColorAndOpacity(bBold ? FLinearColor::White : FLinearColor(0.82f, 0.84f, 0.90f));
	};

	return Frame(INVTEXT("CREDITS"),
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(INVTEXT("Instagib Arena"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f) [ Line(INVTEXT("A fan-made tribute to Unreal Tournament 2004.")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(INVTEXT("Made with Unreal Engine 5.8"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f) [ Line(INVTEXT("Unreal Engine is by Epic Games. The Mannequin characters and animations are Epic's content.")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(INVTEXT("Sound and music"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f) [ Line(INVTEXT("Every sound effect and music track was generated for this game.")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(INVTEXT("Open source"), true) ]
		+ SVerticalBox::Slot().AutoHeight() [ Line(INVTEXT("Code under the MIT license: github.com/EladOzCohen/InstagibArena")) ],
		BuildBackButton());
}

// ---------------------------------------------------------------- actions

void SIAMainMenu::SelectCharacter(int32 Index)
{
	Setup.CharacterIndex = FMath::Clamp(Index, 0, IACharacters::LookCount - 1);
	Setup.Save();
	if (OnCharacterChanged)
	{
		OnCharacterChanged(Setup.CharacterIndex);
	}
}

FString SIAMainMenu::BuildOptions(bool bHost) const
{
	FString Options = FString::Printf(TEXT("Mode=%s?ScoreLimit=%d?TimeLimit=%d?Bots=%d?BotSkill=%d?Char=%d"),
		Setup.GameType == 2 ? TEXT("CTF") : (Setup.GameType == 1 ? TEXT("TDM") : TEXT("FFA")),
		Setup.GameType == 2 ? Setup.CaptureLimit : Setup.ScoreLimit, Setup.TimeLimit, Setup.BotCount, Setup.BotSkill, Setup.CharacterIndex);

	const FString Name = IASettings::GetUrlSafePlayerName();
	if (!Name.IsEmpty())
	{
		Options += TEXT("?Name=") + Name;
	}
	if (bHost)
	{
		Options += TEXT("?listen");
	}
	return Options;
}

void SIAMainMenu::StartGame(bool bHost)
{
	APlayerController* PC = Owner.Get();
	if (!PC)
	{
		return;
	}

	Setup.Save();
	const FString Options = BuildOptions(bHost);

	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(PC))
	{
		Audio->Play2D(EIASound::UIStart);
	}

	UE_LOG(LogInstagib, Log, TEXT("Menu: opening %s with options %s"), IAMaps::List[Setup.MapIndex].AssetPath, *Options);
	UGameplayStatics::OpenLevel(PC, FName(IAMaps::List[Setup.MapIndex].AssetPath), true, Options);
}

void SIAMainMenu::JoinGame()
{
	APlayerController* PC = Owner.Get();
	if (!PC)
	{
		return;
	}

	FText Problem;
	if (!IASettings::ValidateJoinAddress(JoinAddress, Problem))
	{
		JoinStatus = Problem;
		JoinStatusColor = FLinearColor(1.f, 0.35f, 0.3f);
		UE_LOG(LogInstagib, Log, TEXT("Menu: join refused for '%s'"), *JoinAddress);
		return;
	}

	const FString Address = JoinAddress.TrimStartAndEnd();
	Setup.Save();
	IASettings::SetJoinAddress(Address);
	IASettings::AddRecentAddress(Address);

	FString Url = FString::Printf(TEXT("%s?Char=%d"), *Address, Setup.CharacterIndex);
	const FString Name = IASettings::GetUrlSafePlayerName();
	if (!Name.IsEmpty())
	{
		Url += TEXT("?Name=") + Name;
	}

	JoinStatus = FText::Format(INVTEXT("Connecting to {0} ..."), FText::FromString(Address));
	JoinStatusColor = FLinearColor(0.95f, 0.85f, 0.5f);

	UE_LOG(LogInstagib, Log, TEXT("Menu: joining %s"), *Url);
	PC->ClientTravel(Url, TRAVEL_Absolute);
}

void SIAMainMenu::QuitGame()
{
	if (Modal->IsOpen())
	{
		return;
	}
	Modal->Show(INVTEXT("QUIT GAME?"), []() { return INVTEXT("Do you really want to leave Instagib Arena?"); },
		{
			{ INVTEXT("QUIT"), [this]()
				{
					if (APlayerController* PC = Owner.Get())
					{
						Setup.Save();
						UKismetSystemLibrary::QuitGame(PC, PC, EQuitPreference::Quit, false);
					}
				}, false },
			{ INVTEXT("STAY"), nullptr, true }
		});
}

// ---------------------------------------------------------------- developer check

void SIAMainMenu::DevCommand(const FString& Command)
{
	FString Name = Command;
	FString Value;
	Command.Split(TEXT("="), &Name, &Value);
	UE_LOG(LogInstagib, Log, TEXT("MenuScript: %s"), *Command);

	if (Name == TEXT("page")) { ShowPageForTest(FCString::Atoi(*Value), 0); }
	else if (Name == TEXT("mp")) { MultiplayerTab = FCString::Atoi(*Value); }
	else if (Name == TEXT("settings")) { SettingsTab = FCString::Atoi(*Value); Page = EPage::Settings; PageTime = 1.f; PageHost->SetContent(BuildPage(Page)); }
	else if (Name == TEXT("key")) { SimulateKey(FKey(*Value)); }
	else if (Name == TEXT("welcome")) { if (Value == TEXT("off")) { if (Welcome.IsValid()) { Welcome.Reset(); WelcomeHost->SetContent(SNullWidget::NullWidget); } } else { ShowWelcome(FCString::Atoi(*Value)); } }
	else if (Name == TEXT("quit")) { QuitGame(); }
	else if (Name == TEXT("modal-cancel")) { Modal->Cancel(); }
	else if (Name == TEXT("quickplay")) { StartGame(false); }
	else if (Name == TEXT("host")) { StartGame(true); }
	else if (Name == TEXT("gametype")) { Setup.GameType = FMath::Clamp(FCString::Atoi(*Value), 0, 2); }
	else if (Name == TEXT("map")) { Setup.MapIndex = FMath::Clamp(FCString::Atoi(*Value), 0, IAMaps::Count - 1); }
	else if (Name == TEXT("join")) { JoinAddress = Value; JoinGame(); }
	else if (Name == TEXT("copy")) { CopiedUntil = FPlatformTime::Seconds() + 2.0; }
	else if (Name == TEXT("uiscale")) { IASettings::SetUiScale(FCString::Atof(*Value)); }
	else if (Name == TEXT("tutorial-done")) { IASettings::SetTutorialDone(true); }
	else if (const TSharedPtr<SIASettingsPanel> Panel = SettingsPanel.Pin())
	{
		if (!Panel->DevCommand(Command))
		{
			UE_LOG(LogInstagib, Warning, TEXT("MenuScript: unknown command %s"), *Command);
		}
	}
	else
	{
		UE_LOG(LogInstagib, Warning, TEXT("MenuScript: unknown command %s"), *Command);
	}
}
