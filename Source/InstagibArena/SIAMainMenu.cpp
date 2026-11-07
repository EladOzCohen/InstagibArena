// Instagib Arena

#include "SIAMainMenu.h"
#include "IAMapList.h"
#include "IACharacterRoster.h"
#include "IAAudioSubsystem.h"
#include "InstagibArena.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "IAMainMenu"

namespace
{
	const FLinearColor Accent(1.0f, 0.42f, 0.0f, 1.0f);
	const FLinearColor Idle(0.16f, 0.17f, 0.2f, 1.0f);
	const FLinearColor PanelColor(0.02f, 0.02f, 0.03f, 0.82f);

	FSlateFontInfo MenuFont(int32 Size, const TCHAR* Style = TEXT("Regular"))
	{
		return FCoreStyle::GetDefaultFontStyle(Style, Size);
	}
}

TSharedRef<SWidget> SIAMainMenu::MakeButton(const FText& Label, TFunction<void()> OnClick, TFunction<bool()> IsSelected, float MinWidth)
{
	return SNew(SBox)
		.MinDesiredWidth(MinWidth)
		[
			SNew(SButton)
			.HAlign(HAlign_Center)
			.ContentPadding(FMargin(16.f, 8.f))
			.ButtonColorAndOpacity_Lambda([IsSelected]() -> FSlateColor
			{
				// The button brush is dark grey, so the tint is boosted above 1 to read as orange.
				static const FLinearColor Selected(4.0f, 1.7f, 0.2f, 1.0f);
				static const FLinearColor Normal(0.9f, 0.9f, 1.0f, 1.0f);
				return (IsSelected && IsSelected()) ? Selected : Normal;
			})
			.OnClicked_Lambda([this, OnClick]()
			{
				if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(Owner.Get()))
				{
					Audio->Play2D(EIASound::UIClick);
				}
				if (OnClick)
				{
					OnClick();
				}
				return FReply::Handled();
			})
			[
				SNew(STextBlock)
				.Text(Label)
				.Font(MenuFont(16, TEXT("Bold")))
				.ColorAndOpacity(FLinearColor::White)
			]
		];
}

TSharedRef<SWidget> SIAMainMenu::MakeStepper(TFunction<FText()> ValueText, TFunction<void()> OnMinus, TFunction<void()> OnPlus)
{
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			MakeButton(LOCTEXT("Minus", "-"), OnMinus, nullptr, 40.f)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(12.f, 0.f)
		[
			SNew(SBox).MinDesiredWidth(120.f).HAlign(HAlign_Center)
			[
				SNew(STextBlock)
				.Text_Lambda([ValueText]() { return ValueText(); })
				.Font(MenuFont(18, TEXT("Bold")))
				.ColorAndOpacity(Accent)
			]
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			MakeButton(LOCTEXT("Plus", "+"), OnPlus, nullptr, 40.f)
		];
}

TSharedRef<SWidget> SIAMainMenu::MakeRow(const FString& Label, TSharedRef<SWidget> Content)
{
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			SNew(SBox).WidthOverride(190.f)
			[
				SNew(STextBlock)
				.Text(FText::FromString(Label))
				.Font(MenuFont(16))
				.ColorAndOpacity(FLinearColor(0.8f, 0.8f, 0.85f))
			]
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			Content
		];
}

void SIAMainMenu::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	OnCharacterChanged = InArgs._OnCharacterChanged;

	const int32 ScoreStep = 5;

	ChildSlot
	[
		SNew(SBox)
		.HAlign(HAlign_Left)
		.VAlign(VAlign_Center)
		.Padding(FMargin(80.f, 0.f))
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(PanelColor)
			.Padding(FMargin(40.f, 30.f))
			[
				SNew(SVerticalBox)

				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(STextBlock)
					.Text(LOCTEXT("Title", "INSTAGIB ARENA"))
					.Font(MenuFont(44, TEXT("Bold")))
					.ColorAndOpacity(Accent)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 24.f)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("Subtitle", "One shot. One kill."))
					.Font(MenuFont(16))
					.ColorAndOpacity(FLinearColor(0.7f, 0.7f, 0.75f))
				]

				// Game type.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Game type"),
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
						[
							MakeButton(LOCTEXT("FFA", "Free For All"), [this]() { bTeamGame = false; }, [this]() { return !bTeamGame; }, 170.f)
						]
						+ SHorizontalBox::Slot().AutoWidth()
						[
							MakeButton(LOCTEXT("TDM", "Team Deathmatch"), [this]() { bTeamGame = true; }, [this]() { return bTeamGame; }, 170.f)
						])
				]

				// Map.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Map"),
						MakeStepper(
							[this]() { return FText::FromString(IAMaps::List[MapIndex].DisplayName); },
							[this]() { MapIndex = (MapIndex + IAMaps::Count - 1) % IAMaps::Count; },
							[this]() { MapIndex = (MapIndex + 1) % IAMaps::Count; }))
				]

				// Character.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Character"),
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth()
						[
							MakeStepper(
								[this]() { return FText::FromString(IACharacters::GetLook(CharacterIndex).Name); },
								[this]()
								{
									CharacterIndex = (CharacterIndex + IACharacters::LookCount - 1) % IACharacters::LookCount;
									if (OnCharacterChanged) { OnCharacterChanged(CharacterIndex); }
								},
								[this]()
								{
									CharacterIndex = (CharacterIndex + 1) % IACharacters::LookCount;
									if (OnCharacterChanged) { OnCharacterChanged(CharacterIndex); }
								})
						]
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(10.f, 0.f)
						[
							SNew(STextBlock)
							.Text_Lambda([this]() { return FText::FromString(IACharacters::GetLook(CharacterIndex).Title); })
							.Font(MenuFont(14))
							.ColorAndOpacity(FLinearColor(0.65f, 0.65f, 0.7f))
						])
				]

				// Bots.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Bots"),
						MakeStepper(
							[this]() { return BotCount == 0 ? LOCTEXT("NoBots", "None") : FText::AsNumber(BotCount); },
							[this]() { BotCount = (BotCount <= 2) ? 0 : BotCount - 1; },
							[this]() { BotCount = (BotCount == 0) ? 2 : FMath::Min(10, BotCount + 1); }))
				]

				// Bot skill.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Bot skill"),
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
						[
							MakeButton(LOCTEXT("Beginner", "Beginner"), [this]() { BotSkill = 0; }, [this]() { return BotSkill == 0; }, 110.f)
						]
						+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
						[
							MakeButton(LOCTEXT("Intermediate", "Intermediate"), [this]() { BotSkill = 1; }, [this]() { return BotSkill == 1; }, 110.f)
						]
						+ SHorizontalBox::Slot().AutoWidth()
						[
							MakeButton(LOCTEXT("Expert", "Expert"), [this]() { BotSkill = 2; }, [this]() { return BotSkill == 2; }, 110.f)
						])
				]

				// Score limit.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Score limit"),
						MakeStepper(
							[this]() { return ScoreLimit == 0 ? LOCTEXT("Off", "Off") : FText::AsNumber(ScoreLimit); },
							[this, ScoreStep]() { ScoreLimit = FMath::Max(0, ScoreLimit - ScoreStep); },
							[this, ScoreStep]() { ScoreLimit = FMath::Min(100, ScoreLimit + ScoreStep); }))
				]

				// Time limit.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Time limit"),
						MakeStepper(
							[this]() { return TimeLimit == 0 ? LOCTEXT("Off2", "Off") : FText::Format(LOCTEXT("Minutes", "{0} min"), FText::AsNumber(TimeLimit)); },
							[this]() { TimeLimit = FMath::Max(0, TimeLimit - 1); },
							[this]() { TimeLimit = FMath::Min(30, TimeLimit + 1); }))
				]

				// Volumes, in steps of ten percent.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Music volume"),
						MakeStepper(
							[this]() { const UIAAudioSubsystem* A = UIAAudioSubsystem::Get(Owner.Get()); return FText::Format(LOCTEXT("Percent", "{0}%"), FText::AsNumber(A ? FMath::RoundToInt(A->GetMusicVolume() * 100.f) : 0)); },
							[this]() { if (UIAAudioSubsystem* A = UIAAudioSubsystem::Get(Owner.Get())) { A->SetMusicVolume(FMath::RoundToFloat(A->GetMusicVolume() * 10.f - 1.f) / 10.f); } },
							[this]() { if (UIAAudioSubsystem* A = UIAAudioSubsystem::Get(Owner.Get())) { A->SetMusicVolume(FMath::RoundToFloat(A->GetMusicVolume() * 10.f + 1.f) / 10.f); } }))
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					MakeRow(TEXT("Effects volume"),
						MakeStepper(
							[this]() { const UIAAudioSubsystem* A = UIAAudioSubsystem::Get(Owner.Get()); return FText::Format(LOCTEXT("Percent2", "{0}%"), FText::AsNumber(A ? FMath::RoundToInt(A->GetSfxVolume() * 100.f) : 0)); },
							[this]() { if (UIAAudioSubsystem* A = UIAAudioSubsystem::Get(Owner.Get())) { A->SetSfxVolume(FMath::RoundToFloat(A->GetSfxVolume() * 10.f - 1.f) / 10.f); } },
							[this]() { if (UIAAudioSubsystem* A = UIAAudioSubsystem::Get(Owner.Get())) { A->SetSfxVolume(FMath::RoundToFloat(A->GetSfxVolume() * 10.f + 1.f) / 10.f); } }))
				]

				// Start.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 22.f, 0.f, 6.f)
				[
					MakeButton(LOCTEXT("Start", "START GAME"), [this]() { StartGame(false); }, []() { return true; }, 360.f)
				]

				// Multiplayer.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
					[
						MakeButton(LOCTEXT("Host", "Host LAN game"), [this]() { StartGame(true); }, nullptr, 170.f)
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 8.f, 0.f)
					[
						SNew(SBox).WidthOverride(150.f)
						[
							SNew(SEditableTextBox)
							.Text_Lambda([this]() { return FText::FromString(JoinAddress); })
							.OnTextChanged_Lambda([this](const FText& NewText) { JoinAddress = NewText.ToString(); })
							.Font(MenuFont(15))
						]
					]
					+ SHorizontalBox::Slot().AutoWidth()
					[
						MakeButton(LOCTEXT("Join", "Join"), [this]() { JoinGame(); }, nullptr, 80.f)
					]
				]

				// Quit.
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
				[
					MakeButton(LOCTEXT("Quit", "Quit"), [this]()
					{
						if (APlayerController* PC = Owner.Get())
						{
							UKismetSystemLibrary::QuitGame(PC, PC, EQuitPreference::Quit, false);
						}
					}, nullptr, 120.f)
				]
			]
		]
	];
}

void SIAMainMenu::StartGame(bool bHost)
{
	APlayerController* PC = Owner.Get();
	if (!PC)
	{
		return;
	}

	FString Options = FString::Printf(TEXT("Mode=%s?ScoreLimit=%d?TimeLimit=%d?Bots=%d?BotSkill=%d?Char=%d"),
		bTeamGame ? TEXT("TDM") : TEXT("FFA"), ScoreLimit, TimeLimit, BotCount, BotSkill, CharacterIndex);
	if (bHost)
	{
		Options += TEXT("?listen");
	}

	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(PC))
	{
		Audio->Play2D(EIASound::UIStart);
	}

	UE_LOG(LogInstagib, Log, TEXT("Menu: opening %s with options %s"), IAMaps::List[MapIndex].AssetPath, *Options);
	UGameplayStatics::OpenLevel(PC, FName(IAMaps::List[MapIndex].AssetPath), true, Options);
}

void SIAMainMenu::JoinGame()
{
	APlayerController* PC = Owner.Get();
	if (!PC || JoinAddress.IsEmpty())
	{
		return;
	}

	const FString Url = FString::Printf(TEXT("%s?Char=%d"), *JoinAddress, CharacterIndex);
	UE_LOG(LogInstagib, Log, TEXT("Menu: joining %s"), *Url);
	PC->ClientTravel(Url, TRAVEL_Absolute);
}

#undef LOCTEXT_NAMESPACE
