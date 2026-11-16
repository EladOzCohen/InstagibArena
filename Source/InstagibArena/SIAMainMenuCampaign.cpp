// Instagib Arena
//
// The campaign screens of the main menu: home (continue / new), new campaign (name, character, difficulty) and the ladder.

#include "SIAMainMenu.h"
#include "IAAudioSubsystem.h"
#include "IACampaignSubsystem.h"
#include "IACharacterRoster.h"
#include "IAMenuStyle.h"
#include "InstagibArena.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

namespace
{
	UIACampaignSubsystem* GetCamp(const TWeakObjectPtr<APlayerController>& Owner)
	{
		const APlayerController* PC = Owner.Get();
		UGameInstance* Instance = PC ? PC->GetGameInstance() : nullptr;
		return Instance ? Instance->GetSubsystem<UIACampaignSubsystem>() : nullptr;
	}

	FText ModeName(EIACampaignMode Mode)
	{
		switch (Mode)
		{
		case EIACampaignMode::Duel:           return INVTEXT("DUEL");
		case EIACampaignMode::FreeForAll:     return INVTEXT("FREE FOR ALL");
		case EIACampaignMode::TeamDeathmatch: return INVTEXT("TEAM DEATHMATCH");
		case EIACampaignMode::CaptureTheFlag: return INVTEXT("CAPTURE THE FLAG");
		case EIACampaignMode::Survival:       return INVTEXT("SURVIVAL");
		}
		return FText::GetEmpty();
	}

	/** What a player must do to win, in a sentence. */
	FText GoalText(const FIACampaignMatch& M)
	{
		switch (M.Mode)
		{
		case EIACampaignMode::CaptureTheFlag: return FText::Format(INVTEXT("Win: {0} flag captures, or lead when {1} minutes are up."), M.Limit, M.TimeLimitMinutes);
		case EIACampaignMode::Survival:       return FText::Format(INVTEXT("Win: survive {0} waves."), M.Limit);
		default:                              return FText::Format(INVTEXT("Win: {0} frags, or lead when {1} minutes are up."), M.Limit, M.TimeLimitMinutes);
		}
	}

	TSharedRef<SWidget> StarRow(int32 Count)
	{
		TSharedRef<SHorizontalBox> Row = SNew(SHorizontalBox);
		for (int32 I = 0; I < 3; ++I)
		{
			Row->AddSlot().AutoWidth().Padding(2.f, 0.f)
			[
				SNew(SBox).WidthOverride(14.f).HeightOverride(14.f)
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(I < Count ? FLinearColor(1.f, 0.78f, 0.1f) : FLinearColor(1.f, 1.f, 1.f, 0.16f))
				]
			];
		}
		return Row;
	}

	TSharedRef<SWidget> Paragraph(const FText& Text, int32 Size = 16, FLinearColor Color = FLinearColor(0.82f, 0.84f, 0.9f))
	{
		return SNew(STextBlock).Text(Text).Font(Font(Size)).ColorAndOpacity(Color).AutoWrapText(true);
	}
}

void SIAMainMenu::SetCampaignView(int32 View)
{
	CampaignView = View;
	PageTime = 1.f;
	PageHost->SetContent(BuildCampaignPage());
	FSlateApplication::Get().SetKeyboardFocus(SharedThis(this), EFocusCause::SetDirectly);
}

TSharedRef<SWidget> SIAMainMenu::BuildCampaignPage()
{
	UIACampaignSubsystem* Camp = GetCamp(Owner);
	if (!Camp)
	{
		return Frame(INVTEXT("CAMPAIGN"), Paragraph(INVTEXT("The campaign is not available.")), BuildBackButton());
	}
	if (CampaignView == 2 && !Camp->HasCampaign()) { CampaignView = 0; }
	switch (CampaignView)
	{
	case 1:  return BuildCampaignNew();
	case 2:  return BuildCampaignLadder();
	default: return BuildCampaignHome();
	}
}

// ---------------------------------------------------------------- home

TSharedRef<SWidget> SIAMainMenu::BuildCampaignHome()
{
	UIACampaignSubsystem* Camp = GetCamp(Owner);
	const bool bHas = Camp && Camp->HasCampaign();

	TSharedRef<SVerticalBox> Body = SNew(SVerticalBox);
	Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 12.f)
	[
		SNew(STextBlock).Text(INVTEXT("THE APEX LEAGUE")).Font(SpacedFont(30, true, 50)).ColorAndOpacity(Accent)
	];
	Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 14.f)
	[
		Paragraph(INVTEXT("The Apex League sends its fighters across five worlds, broadcast to a hundred more. You start with nothing: no team, no sponsor, one entry slot. "
			"Win your matches, recruit a squad, and climb to the throne of the champion nobody has beaten in eleven seasons."), 18)
	];
	Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 18.f)
	[
		Paragraph(INVTEXT("20 matches in 5 chapters: duels, free for all, team deathmatch, capture the flag and survival. Earn up to 3 stars in each."), 16, TextDim)
	];

	if (bHas)
	{
		FString SquadNames;
		for (int32 Look : Camp->GetSquad())
		{
			SquadNames += (SquadNames.IsEmpty() ? TEXT("") : TEXT(", ")) + FString(IACharacters::GetLook(Look).Name);
		}
		Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 6.f)
		[
			Paragraph(FText::Format(INVTEXT("Hero: {0}    Next match: {1} of {2}    Stars: {3} of {4}"),
				FText::FromString(Camp->GetHeroName()), FMath::Min(Camp->GetNextMatch() + 1, IACampaign::MatchCount),
				IACampaign::MatchCount, Camp->GetTotalStars(), IACampaign::MatchCount * 3), 17, FLinearColor::White)
		];
		Body->AddSlot().AutoHeight()
		[
			Paragraph(FText::Format(INVTEXT("Squad: {0}"), SquadNames.IsEmpty() ? INVTEXT("none yet") : FText::FromString(SquadNames)), 16, TextDim)
		];
	}

	TSharedRef<SHorizontalBox> Footer = SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 10.f, 0.f) [ BuildBackButton() ];
	if (bHas)
	{
		Footer->AddSlot().AutoWidth().Padding(0.f, 0.f, 10.f, 0.f)
		[
			PrimaryButton(Owner, INVTEXT("CONTINUE"), [this]()
			{
				if (UIACampaignSubsystem* C = GetCamp(Owner)) { CampaignSelected = FMath::Min(C->GetNextMatch(), IACampaign::MatchCount - 1); }
				SetCampaignView(2);
			}, 240.f)
		];
		Footer->AddSlot().AutoWidth()
		[
			ChipDyn(Owner, [this]() { return bCampaignResetAsked ? INVTEXT("CLICK AGAIN: PROGRESS WILL BE LOST") : INVTEXT("NEW CAMPAIGN"); },
				[this]()
				{
					if (!bCampaignResetAsked) { bCampaignResetAsked = true; return; }
					bCampaignResetAsked = false;
					SetCampaignView(1);
				}, [this]() { return bCampaignResetAsked; }, 0.f, 16)
		];
	}
	else
	{
		Footer->AddSlot().AutoWidth()
		[
			PrimaryButton(Owner, INVTEXT("NEW CAMPAIGN"), [this]() { SetCampaignView(1); }, 240.f)
		];
	}
	return Frame(INVTEXT("CAMPAIGN"), Body, Footer);
}

// ---------------------------------------------------------------- new campaign

TSharedRef<SWidget> SIAMainMenu::BuildCampaignNew()
{
	if (CampaignName.IsEmpty())
	{
		CampaignName = IASettings::GetPlayerName();
	}
	CampaignLook = FMath::Clamp(Setup.CharacterIndex, 0, IACharacters::LookCount - 1);

	TSharedRef<SUniformGridPanel> Grid = SNew(SUniformGridPanel).SlotPadding(FMargin(3.f));
	for (int32 Index = 0; Index < IACharacters::LookCount; ++Index)
	{
		Grid->AddSlot(Index % 4, Index / 4)
		[
			Chip(Owner, FText::FromString(IACharacters::GetLook(Index).Name), [this, Index]() { CampaignLook = Index; SelectCharacter(Index); },
				[this, Index]() { return CampaignLook == Index; }, 0.f, 14)
		];
	}

	TSharedRef<SWidget> Body = SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f)
		[
			Row(INVTEXT("Your name"),
				SNew(SBox).WidthOverride(320.f)
				[
					SNew(SEditableTextBox)
					.Text_Lambda([this]() { return FText::FromString(CampaignName); })
					.HintText(INVTEXT("Wildcard"))
					.Font(Font(18))
					.OnTextChanged_Lambda([this](const FText& NewText) { CampaignName = NewText.ToString().Left(16); })
				],
				170.f, INVTEXT("The League announcer calls you by this name."))
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 10.f, 0.f, 4.f)
		[
			SNew(STextBlock).Text(INVTEXT("YOUR FIGHTER")).Font(Font(13, true)).ColorAndOpacity(TextDim)
		]
		+ SVerticalBox::Slot().AutoHeight() [ Grid ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 16.f, 0.f, 6.f)
		[
			Row(INVTEXT("Difficulty"),
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
				[ Chip(Owner, INVTEXT("RELAXED"), [this]() { CampaignDifficulty = 0; }, [this]() { return CampaignDifficulty == 0; }, 130.f, 15) ]
				+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
				[ Chip(Owner, INVTEXT("NORMAL"), [this]() { CampaignDifficulty = 1; }, [this]() { return CampaignDifficulty == 1; }, 130.f, 15) ]
				+ SHorizontalBox::Slot().AutoWidth()
				[ Chip(Owner, INVTEXT("HARD"), [this]() { CampaignDifficulty = 2; }, [this]() { return CampaignDifficulty == 2; }, 130.f, 15) ],
				170.f, INVTEXT("Relaxed: every opponent is one skill level weaker. Hard: one level stronger."))
		];

	TSharedRef<SWidget> Footer = SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 10.f, 0.f)
		[
			Chip(Owner, INVTEXT("BACK"), [this]() { SetCampaignView(0); }, nullptr, 130.f, 18)
		]
		+ SHorizontalBox::Slot().AutoWidth()
		[
			PrimaryButton(Owner, INVTEXT("START THE LEAGUE"), [this]()
			{
				if (UIACampaignSubsystem* C = GetCamp(Owner))
				{
					C->StartNewCampaign(CampaignName, CampaignLook, CampaignDifficulty);
					CampaignSelected = 0;
					SetCampaignView(2);
				}
			}, 300.f)
		];
	return Frame(INVTEXT("NEW CAMPAIGN"), Body, Footer);
}

// ---------------------------------------------------------------- ladder

TSharedRef<SWidget> SIAMainMenu::BuildCampaignLadder()
{
	UIACampaignSubsystem* Camp = GetCamp(Owner);
	const TArray<FIACampaignMatch>& Matches = IACampaign::Matches();
	const TArray<IACampaign::FChapter>& Chapters = IACampaign::Chapters();
	CampaignSelected = FMath::Clamp(CampaignSelected, 0, IACampaign::MatchCount - 1);
	const FIACampaignMatch& Sel = Matches[CampaignSelected];
	const int32 Chapter = Sel.Chapter;

	TSharedRef<SVerticalBox> Body = SNew(SVerticalBox);

	// What happened in the match that was just played.
	if (Camp->LastResult.Match >= 0 && Matches.IsValidIndex(Camp->LastResult.Match))
	{
		const FIACampaignMatch& Last = Matches[Camp->LastResult.Match];
		const bool bWon = Camp->LastResult.bWon;
		Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 14.f)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(bWon ? FLinearColor(0.1f, 0.35f, 0.12f, 0.55f) : FLinearColor(0.4f, 0.1f, 0.08f, 0.55f))
			.Padding(FMargin(14.f, 10.f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(STextBlock)
					.Text(FText::Format(bWon ? INVTEXT("VICTORY: {0}   ({1} of 3 stars)") : INVTEXT("DEFEAT: {0}"),
						FText::FromString(Last.Title), Camp->LastResult.Stars))
					.Font(Font(20, true)).ColorAndOpacity(FLinearColor::White)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
				[
					Paragraph(FText::FromString(bWon ? Last.WinLine : Last.LoseLine), 16)
				]
			]
		];
		Camp->LastResult.Match = -1;
	}

	// Chapter heading and intro.
	Body->AddSlot().AutoHeight()
	[
		SNew(STextBlock)
		.Text(FText::Format(INVTEXT("CHAPTER {0}: {1}   -   {2}"), Chapter + 1, FText::FromString(Chapters[Chapter].Name), FText::FromString(Chapters[Chapter].Planet)))
		.Font(SpacedFont(22, true, 40)).ColorAndOpacity(Accent)
	];
	Body->AddSlot().AutoHeight().Padding(0.f, 4.f, 0.f, 12.f)
	[
		Paragraph(FText::FromString(Chapters[Chapter].Intro), 15, TextDim)
	];

	// The four matches of the chapter.
	for (int32 Index = 0; Index < IACampaign::MatchCount; ++Index)
	{
		if (Matches[Index].Chapter != Chapter) { continue; }
		const bool bOpen = Camp->IsMatchUnlocked(Index);
		const int32 Stars = Camp->GetStars(Index);
		Body->AddSlot().AutoHeight().Padding(0.f, 2.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().FillWidth(1.f)
			[
				Chip(Owner,
					bOpen ? FText::Format(INVTEXT("{0}.  {1}      {2}  -  {3}"), Index + 1, FText::FromString(Matches[Index].Title), ModeName(Matches[Index].Mode), FText::FromString(Matches[Index].Map))
					      : FText::Format(INVTEXT("{0}.  LOCKED"), Index + 1),
					[this, Index, bOpen]() { if (bOpen) { CampaignSelected = Index; SetCampaignView(2); } },
					[this, Index]() { return CampaignSelected == Index; }, 0.f, 16)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(12.f, 0.f, 4.f, 0.f)
			[
				StarRow(Stars)
			]
		];
	}

	// The selected match.
	const int32 Skill = Camp->GetEffectiveSkill(CampaignSelected);
	FString SquadNames;
	for (int32 Look : Camp->BuildAllyLooks(CampaignSelected))
	{
		SquadNames += (SquadNames.IsEmpty() ? TEXT("") : TEXT(", ")) + FString(IACharacters::GetLook(Look).Name);
	}
	const FIACampaignFaction& Faction = IACampaign::Factions()[Sel.Faction];
	Body->AddSlot().AutoHeight().Padding(0.f, 16.f, 0.f, 4.f)
	[
		SNew(STextBlock).Text(FText::FromString(Sel.Title)).Font(Font(28, true)).ColorAndOpacity(FLinearColor::White)
	];
	Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 8.f)
	[
		Paragraph(FText::FromString(Sel.Briefing), 17)
	];
	Body->AddSlot().AutoHeight()
	[
		Paragraph(FText::Format(INVTEXT("{0} on {1}.  Opponents: {2} ({3}), skill: {4}."), ModeName(Sel.Mode), FText::FromString(Sel.Map),
			FText::FromString(Faction.Name), Sel.EnemyCount, IABots::SkillName(Skill)), 15, TextDim)
	];
	if (Sel.AllyCount > 0)
	{
		Body->AddSlot().AutoHeight()
		[
			Paragraph(FText::Format(INVTEXT("Your side: {0}"), FText::FromString(SquadNames)), 15, TextDim)
		];
	}
	Body->AddSlot().AutoHeight()
	[
		Paragraph(GoalText(Sel), 15, TextDim)
	];
	Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 6.f)
	[
		Paragraph(FText::Format(INVTEXT("Stars: a win, a clear win, and:  {0}"), FText::FromString(Sel.Bonus.ToText())), 15, FLinearColor(1.f, 0.82f, 0.35f))
	];
	if (Sel.RecruitLook >= 0 && !Camp->IsRecruited(Sel.RecruitLook))
	{
		Body->AddSlot().AutoHeight()
		[
			Paragraph(FText::Format(INVTEXT("Win to recruit {0} to your squad."), FText::FromString(IACharacters::GetLook(Sel.RecruitLook).Name)), 15, FLinearColor(0.5f, 0.9f, 0.55f))
		];
	}

	// The end of the ladder: the player chooses how the story ends.
	if (Camp->IsComplete())
	{
		const TArray<IACampaign::FEnding>& Endings = IACampaign::Endings();
		Body->AddSlot().AutoHeight().Padding(0.f, 20.f, 0.f, 6.f)
		[
			SNew(STextBlock).Text(INVTEXT("THE THRONE IS YOURS")).Font(SpacedFont(24, true, 40)).ColorAndOpacity(Accent)
		];
		if (Camp->GetEnding() == 0)
		{
			Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 8.f)
			[
				Paragraph(INVTEXT("Sovereign is beaten. Voss is on every screen, waiting for your answer. What do you do?"), 17)
			];
			TSharedRef<SHorizontalBox> Choices = SNew(SHorizontalBox);
			for (int32 E = 0; E < Endings.Num(); ++E)
			{
				Choices->AddSlot().AutoWidth().Padding(0.f, 0.f, 10.f, 0.f)
				[
					PrimaryButton(Owner, FText::FromString(Endings[E].ChoiceLabel), [this, E]()
					{
						if (UIACampaignSubsystem* C = GetCamp(Owner)) { C->SetEnding(E + 1); }
						SetCampaignView(2);
					}, 240.f)
				];
			}
			Body->AddSlot().AutoHeight() [ Choices ];
		}
		else
		{
			const IACampaign::FEnding& Chosen = Endings[Camp->GetEnding() - 1];
			Body->AddSlot().AutoHeight()
			[
				SNew(STextBlock).Text(FText::FromString(Chosen.Title)).Font(Font(20, true)).ColorAndOpacity(FLinearColor::White)
			];
			Body->AddSlot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
			[
				Paragraph(FText::FromString(Chosen.Text), 16)
			];
		}
	}

	// Footer: back, chapter arrows and PLAY.
	TSharedRef<SHorizontalBox> Footer = SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 10.f, 0.f)
		[
			Chip(Owner, INVTEXT("BACK"), [this]() { SetCampaignView(0); }, nullptr, 110.f, 18)
		]
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
		[
			Chip(Owner, INVTEXT("< CHAPTER"), [this]()
			{
				const int32 Target = IACampaign::Matches()[CampaignSelected].Chapter - 1;
				for (int32 I = 0; I < IACampaign::MatchCount; ++I) { if (IACampaign::Matches()[I].Chapter == Target) { CampaignSelected = I; break; } }
				SetCampaignView(2);
			}, nullptr, 130.f, 15)
		]
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 10.f, 0.f)
		[
			Chip(Owner, INVTEXT("CHAPTER >"), [this]()
			{
				const UIACampaignSubsystem* C = GetCamp(Owner);
				const int32 Target = IACampaign::Matches()[CampaignSelected].Chapter + 1;
				for (int32 I = 0; I < IACampaign::MatchCount; ++I)
				{
					if (IACampaign::Matches()[I].Chapter == Target && C && C->IsMatchUnlocked(I)) { CampaignSelected = I; break; }
				}
				SetCampaignView(2);
			}, nullptr, 130.f, 15)
		]
		+ SHorizontalBox::Slot().AutoWidth()
		[
			PrimaryButton(Owner, Camp->GetStars(CampaignSelected) > 0 ? INVTEXT("PLAY AGAIN") : INVTEXT("PLAY MATCH"),
				[this]() { StartCampaignMatch(CampaignSelected); }, 220.f)
		];
	return Frame(INVTEXT("CAMPAIGN"), Body, Footer);
}

void SIAMainMenu::StartCampaignMatch(int32 MatchIndex)
{
	APlayerController* PC = Owner.Get();
	UIACampaignSubsystem* Camp = GetCamp(Owner);
	if (!PC || !Camp || !Camp->IsMatchUnlocked(MatchIndex))
	{
		return;
	}

	FString Options = Camp->BuildTravelOptions(MatchIndex);
	FString Name;
	for (TCHAR Ch : Camp->GetHeroName())
	{
		if (FChar::IsAlnum(Ch) || Ch == TEXT('_') || Ch == TEXT('-')) { Name.AppendChar(Ch); }
	}
	if (!Name.IsEmpty())
	{
		Options += TEXT("?Name=") + Name;
	}
	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(PC))
	{
		Audio->Play2D(EIASound::UIStart);
	}
	const FString Map = UIACampaignSubsystem::MapPath(IACampaign::Matches()[MatchIndex].Map);
	UE_LOG(LogInstagib, Log, TEXT("Menu: campaign match %d, opening %s with options %s"), MatchIndex + 1, *Map, *Options);
	UGameplayStatics::OpenLevel(PC, FName(*Map), true, Options);
}
