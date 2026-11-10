// Instagib Arena

#include "SIAMainMenu.h"
#include "IAAudioSubsystem.h"
#include "IACharacterRoster.h"
#include "IAMapList.h"
#include "IAMenuStyle.h"
#include "InstagibArena.h"
#include "SIASettingsPanel.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

// ---------------------------------------------------------------- construction

void SIAMainMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	OnCharacterChanged = InArgs._OnCharacterChanged;

	Setup.Load();
	JoinAddress = IASettings::GetJoinAddress();

	// Coming back after a failed or lost connection: show it where the player can retry.
	if (!InArgs._InitialError.IsEmpty())
	{
		JoinStatus = FText::FromString(InArgs._InitialError);
		JoinStatusColor = FLinearColor(1.f, 0.35f, 0.3f);
		MultiplayerTab = 1;
		Page = EPage::Multiplayer;
	}

	// The column keeps one width on every screen, so that the menu does not jump around.
	ChildSlot
	.HAlign(HAlign_Left)
	[
		SNew(SBox)
		.WidthOverride(640.f)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(PanelColor)
			.Padding(FMargin(56.f, 36.f, 40.f, 22.f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().FillHeight(1.f).VAlign(VAlign_Center)
				[
					SNew(SWidgetSwitcher)
					.WidgetIndex_Lambda([this]() { return static_cast<int32>(Page); })
					+ SWidgetSwitcher::Slot() [ BuildMainPage() ]
					+ SWidgetSwitcher::Slot() [ BuildCustomPage() ]
					+ SWidgetSwitcher::Slot() [ BuildMultiplayerPage() ]
					+ SWidgetSwitcher::Slot() [ BuildCharacterPage() ]
					+ SWidgetSwitcher::Slot() [ BuildSettingsPage() ]
					+ SWidgetSwitcher::Slot() [ BuildCreditsPage() ]
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 10.f, 0.f, 0.f)
				[
					SNew(STextBlock)
					.Text(FText::FromString(FString::Printf(TEXT("v%s    github.com/EladOzCohen/InstagibArena"), IASettings::GameVersion)))
					.Font(Font(12))
					.ColorAndOpacity(TextDim)
				]
			]
		]
	];

	if (OnCharacterChanged)
	{
		OnCharacterChanged(Setup.CharacterIndex);
	}
}

void SIAMainMenu::GoTo(EPage NewPage)
{
	Setup.Save();
	Page = NewPage;

	// Keep the keyboard working on the new screen.
	FSlateApplication::Get().SetKeyboardFocus(SharedThis(this), EFocusCause::SetDirectly);
}

void SIAMainMenu::ShowPageForTest(int32 PageIndex, int32 Tab)
{
	Page = static_cast<EPage>(FMath::Clamp(PageIndex, 0, 5));
	MultiplayerTab = FMath::Clamp(Tab, 0, 1);
}

FReply SIAMainMenu::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape && Page != EPage::Main)
	{
		Click(Owner);
		GoTo(EPage::Main);
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

// ---------------------------------------------------------------- main screen

TSharedRef<SWidget> SIAMainMenu::BuildMainPage()
{
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(STextBlock)
			.Text(INVTEXT("INSTAGIB ARENA"))
			.Font(Font(46, true))
			.ColorAndOpacity(Accent)
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(4.f, 0.f, 0.f, 22.f)
		[
			SNew(STextBlock)
			.Text(INVTEXT("One shot. One kill."))
			.Font(Font(18))
			.ColorAndOpacity(TextDim)
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			NavButton(Owner, INVTEXT("QUICK PLAY"), INVTEXT("Jump into a match with your last settings"), [this]() { StartGame(false); })
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
			NavButton(Owner, INVTEXT("SETTINGS"), INVTEXT("Name, sound, mouse and display"), [this]() { GoTo(EPage::Settings); })
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			NavButton(Owner, INVTEXT("CREDITS"), FText::GetEmpty(), [this]() { GoTo(EPage::Credits); })
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			NavButton(Owner, INVTEXT("QUIT"), FText::GetEmpty(), [this]() { QuitGame(); })
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
					Chip(Owner, INVTEXT("Free For All"), [this]() { Setup.bTeamGame = false; }, [this]() { return !Setup.bTeamGame; }, 150.f)
				]
				+ SHorizontalBox::Slot().AutoWidth()
				[
					Chip(Owner, INVTEXT("Team Deathmatch"), [this]() { Setup.bTeamGame = true; }, [this]() { return Setup.bTeamGame; }, 170.f)
				])
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f, 0.f, 0.f)
		[
			Row(INVTEXT("Map"),
				Stepper(Owner,
					[this]() { return FText::FromString(IAMaps::List[Setup.MapIndex].DisplayName); },
					[this]() { Setup.MapIndex = (Setup.MapIndex + IAMaps::Count - 1) % IAMaps::Count; },
					[this]() { Setup.MapIndex = (Setup.MapIndex + 1) % IAMaps::Count; },
					190.f))
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(170.f, 2.f, 0.f, 6.f)
		[
			Note([this]() { return FText::FromString(IAMaps::List[Setup.MapIndex].Description); })
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
					190.f))
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Bot skill"),
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
				[
					Chip(Owner, INVTEXT("Beginner"), [this]() { Setup.BotSkill = 0; }, [this]() { return Setup.BotSkill == 0; }, 100.f, 15)
				]
				+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
				[
					Chip(Owner, INVTEXT("Intermediate"), [this]() { Setup.BotSkill = 1; }, [this]() { return Setup.BotSkill == 1; }, 100.f, 15)
				]
				+ SHorizontalBox::Slot().AutoWidth()
				[
					Chip(Owner, INVTEXT("Expert"), [this]() { Setup.BotSkill = 2; }, [this]() { return Setup.BotSkill == 2; }, 100.f, 15)
				])
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Score limit"),
				Stepper(Owner,
					[this]() { return Setup.ScoreLimit == 0 ? INVTEXT("Off") : FText::AsNumber(Setup.ScoreLimit); },
					[this, ScoreStep]() { Setup.ScoreLimit = FMath::Max(0, Setup.ScoreLimit - ScoreStep); },
					[this, ScoreStep]() { Setup.ScoreLimit = FMath::Min(100, Setup.ScoreLimit + ScoreStep); },
					190.f))
		]

		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Time limit"),
				Stepper(Owner,
					[this]() { return Setup.TimeLimit == 0 ? INVTEXT("Off") : FText::Format(INVTEXT("{0} min"), FText::AsNumber(Setup.TimeLimit)); },
					[this]() { Setup.TimeLimit = FMath::Max(0, Setup.TimeLimit - 1); },
					[this]() { Setup.TimeLimit = FMath::Min(30, Setup.TimeLimit + 1); },
					190.f))
		];
}

TSharedRef<SWidget> SIAMainMenu::BuildCustomPage()
{
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("CUSTOM GAME")) ]
		+ SVerticalBox::Slot().AutoHeight() [ BuildSetupRows() ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 24.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)
			[
				PrimaryButton(Owner, INVTEXT("START MATCH"), [this]() { StartGame(false); }, 300.f)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				BuildBackButton()
			]
		];
}

// ---------------------------------------------------------------- multiplayer

TSharedRef<SWidget> SIAMainMenu::BuildMultiplayerPage()
{
	const FString LocalAddress = IASettings::GetLocalAddressText();

	TSharedRef<SWidget> HostTab = SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ BuildSetupRows() ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			Note([LocalAddress]()
			{
				return LocalAddress.IsEmpty()
					? INVTEXT("Friends join with your address. Open Command Prompt, type ipconfig and look for IPv4 Address.")
					: FText::Format(INVTEXT("Friends on your network join with this address:  {0}"), FText::FromString(LocalAddress));
			}, []() { return FLinearColor(0.95f, 0.85f, 0.5f); })
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
		[
			Note([]() { return INVTEXT("Over the internet: use a free virtual network such as Tailscale or ZeroTier, or forward UDP port 7777."); })
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 18.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				PrimaryButton(Owner, INVTEXT("HOST GAME"), [this]() { StartGame(true); }, 300.f)
			]
		];

	TSharedRef<SWidget> JoinTab = SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Host address"),
				SNew(SBox).WidthOverride(300.f)
				[
					SNew(SEditableTextBox)
					.Text_Lambda([this]() { return FText::FromString(JoinAddress); })
					.HintText(INVTEXT("for example 192.168.1.20"))
					.Font(Font(18))
					.OnTextChanged_Lambda([this](const FText& NewText) { JoinAddress = NewText.ToString(); })
					.OnTextCommitted_Lambda([this](const FText&, ETextCommit::Type CommitType)
					{
						if (CommitType == ETextCommit::OnEnter) { JoinGame(); }
					})
				])
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(170.f, 6.f, 0.f, 0.f)
		[
			Note([]() { return INVTEXT("Ask the host for the address shown on their Host screen."); })
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 16.f, 0.f, 0.f)
		[
			Note([this]() { return JoinStatus; }, [this]() { return JoinStatusColor; })
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 18.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				PrimaryButton(Owner, INVTEXT("JOIN GAME"), [this]() { JoinGame(); }, 300.f)
			]
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
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(SWidgetSwitcher)
			.WidgetIndex_Lambda([this]() { return MultiplayerTab; })
			+ SWidgetSwitcher::Slot() [ HostTab ]
			+ SWidgetSwitcher::Slot() [ JoinTab ]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 22.f, 0.f, 0.f)
		[
			BuildBackButton()
		];
}

// ---------------------------------------------------------------- character, settings, credits

TSharedRef<SWidget> SIAMainMenu::BuildCharacterPage()
{
	TSharedRef<SUniformGridPanel> Grid = SNew(SUniformGridPanel).SlotPadding(FMargin(3.f));
	for (int32 Index = 0; Index < IACharacters::LookCount; ++Index)
	{
		Grid->AddSlot(Index % 5, Index / 5)
		[
			Chip(Owner, FText::FromString(IACharacters::GetLook(Index).Name), [this, Index]() { SelectCharacter(Index); },
				[this, Index]() { return Setup.CharacterIndex == Index; }, 0.f, 14)
		];
	}

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("CHARACTER")) ]
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
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 18.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Chip(Owner, INVTEXT("DONE"), [this]() { GoTo(EPage::Main); }, nullptr, 130.f, 18)
			]
		];
}

TSharedRef<SWidget> SIAMainMenu::BuildSettingsPage()
{
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("SETTINGS")) ]
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(SIASettingsPanel).OwnerController(Owner).ShowPlayerName(true)
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 22.f, 0.f, 0.f)
		[
			BuildBackButton()
		];
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

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight() [ Heading(INVTEXT("CREDITS")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(INVTEXT("Instagib Arena"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f) [ Line(INVTEXT("A fan-made tribute to Unreal Tournament 2004.")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(INVTEXT("Made with Unreal Engine 5.8"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f) [ Line(INVTEXT("Unreal Engine is by Epic Games. The Mannequin characters and animations are Epic's content.")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(INVTEXT("Sound and music"), true) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f) [ Line(INVTEXT("Every sound effect and music track was generated for this game.")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Line(INVTEXT("Open source"), true) ]
		+ SVerticalBox::Slot().AutoHeight() [ Line(INVTEXT("Code under the MIT license: github.com/EladOzCohen/InstagibArena")) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 22.f, 0.f, 0.f)
		[
			BuildBackButton()
		];
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
		Setup.bTeamGame ? TEXT("TDM") : TEXT("FFA"), Setup.ScoreLimit, Setup.TimeLimit, Setup.BotCount, Setup.BotSkill, Setup.CharacterIndex);

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

	const FString Address = JoinAddress.TrimStartAndEnd();
	if (Address.IsEmpty())
	{
		JoinStatus = INVTEXT("Type the host's address first.");
		JoinStatusColor = FLinearColor(1.f, 0.35f, 0.3f);
		return;
	}

	Setup.Save();
	IASettings::SetJoinAddress(Address);

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
	if (APlayerController* PC = Owner.Get())
	{
		Setup.Save();
		UKismetSystemLibrary::QuitGame(PC, PC, EQuitPreference::Quit, false);
	}
}
