// Instagib Arena
//
// The Hall of Champions: the player's card (rank, title), the rewards with their requirements, and the medals.
// Data: IAProfileSubsystem and IARewardData.h. Design: docs/REWARDS_DESIGN.md.

#include "SIAMainMenu.h"
#include "IAMenuStyle.h"
#include "IAProfileSubsystem.h"
#include "IARewardData.h"
#include "InstagibArena.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/Notifications/SProgressBar.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

namespace
{
	UIAProfileSubsystem* GetProfile(const TWeakObjectPtr<APlayerController>& Owner)
	{
		const APlayerController* PC = Owner.Get();
		UGameInstance* Instance = PC ? PC->GetGameInstance() : nullptr;
		return Instance ? Instance->GetSubsystem<UIAProfileSubsystem>() : nullptr;
	}

	FLinearColor RankColor(int32 Rank)
	{
		static const FLinearColor Colors[7] = {
			FLinearColor(0.55f, 0.57f, 0.62f), FLinearColor(0.80f, 0.52f, 0.28f), FLinearColor(0.78f, 0.80f, 0.86f), FLinearColor(1.f, 0.78f, 0.12f),
			FLinearColor(0.35f, 0.80f, 1.f), FLinearColor(0.78f, 0.45f, 1.f), FLinearColor(1.f, 0.30f, 0.20f) };
		return Colors[FMath::Clamp(Rank, 0, 6)];
	}

	FLinearColor TierColor(int32 Tier)   // 0 = rust .. 4 = obsidian
	{
		static const FLinearColor Colors[5] = {
			FLinearColor(0.60f, 0.30f, 0.16f), FLinearColor(0.80f, 0.52f, 0.28f), FLinearColor(0.78f, 0.80f, 0.86f), FLinearColor(1.f, 0.78f, 0.12f), FLinearColor(0.55f, 0.20f, 0.95f) };
		return Colors[FMath::Clamp(Tier, 0, 4)];
	}

	TSharedRef<SWidget> Square(const FLinearColor& Color, float Size)
	{
		return SNew(SBox).WidthOverride(Size).HeightOverride(Size)
		[
			SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Color)
		];
	}

	TSharedRef<SWidget> Bar(float Percent, const FLinearColor& Color, float Width, float Height = 8.f)
	{
		return SNew(SBox).WidthOverride(Width).HeightOverride(Height)
		[
			SNew(SProgressBar).Percent(Percent).FillColorAndOpacity(Color)
		];
	}

	TSharedRef<SWidget> Text(const FString& S, int32 Size = 16, bool bBold = false, const FLinearColor& Color = FLinearColor(0.86f, 0.88f, 0.94f))
	{
		return SNew(STextBlock).Text(FText::FromString(S)).Font(Font(Size, bBold)).ColorAndOpacity(Color).AutoWrapText(true);
	}

	FString WithCommas(int64 N)
	{
		return FText::AsNumber(N).ToString();
	}
}

void SIAMainMenu::SetHallView(int32 View)
{
	HallView = View;
	PageTime = 1.f;
	PageHost->SetContent(BuildHallPage());
	FSlateApplication::Get().SetKeyboardFocus(SharedThis(this), EFocusCause::SetDirectly);
}

TSharedRef<SWidget> SIAMainMenu::BuildHallPage()
{
	UIAProfileSubsystem* Profile = GetProfile(Owner);
	TSharedRef<SVerticalBox> Body = SNew(SVerticalBox);
	if (!Profile)
	{
		Body->AddSlot().AutoHeight() [ Text(TEXT("The profile is not available.")) ];
		return Frame(INVTEXT("HALL OF CHAMPIONS"), Body, BuildBackButton());
	}

	// The tabs.
	TSharedRef<SHorizontalBox> Tabs = SNew(SHorizontalBox);
	const TCHAR* TabNames[3] = { TEXT("OVERVIEW"), TEXT("REWARDS"), TEXT("MEDALS") };
	for (int32 I = 0; I < 3; ++I)
	{
		Tabs->AddSlot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
		[
			Chip(Owner, FText::FromString(TabNames[I]), [this, I]() { SetHallView(I); }, [this, I]() { return HallView == I; }, 150.f, 16)
		];
	}
	Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 14.f) [ Tabs ];

	if (HallView == 0)
	{
		// ---- overview: the card
		const int32 Rank = Profile->GetRank();
		const TArray<IAReward::FRank>& Ranks = IAReward::Ranks();
		const int64 AP = Profile->GetAP();
		const int64 From = Ranks[Rank].Points;
		const int64 To = Rank + 1 < Ranks.Num() ? Ranks[Rank + 1].Points : From;
		const float Fraction = To > From ? static_cast<float>(AP - From) / static_cast<float>(To - From) : 1.f;
		const FIACosmeticLoadout& Loadout = Profile->GetLoadout();
		FString TitleText;
		if (const IAReward::FReward* T = IAReward::Find(FName(*FString::Printf(TEXT("T%d"), Loadout.TitleId))); T && Loadout.TitleId > 0)
		{
			TitleText = T->Name;
		}
		Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 18.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 18.f, 0.f) [ Square(RankColor(Rank), 74.f) ]
			+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight() [ Text(FString(Ranks[Rank].Name).ToUpper(), 30, true, RankColor(Rank)) ]
				+ SVerticalBox::Slot().AutoHeight() [ Text(TitleText.IsEmpty() ? TEXT("No title chosen") : TitleText, 16, false, TextDim) ]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f, 0.f, 0.f) [ Bar(Fraction, RankColor(Rank), 420.f, 10.f) ]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
				[
					Text(Rank + 1 < Ranks.Num() ? FString::Printf(TEXT("%s apex points   -   next: %s at %s"), *WithCommas(AP), Ranks[Rank + 1].Name, *WithCommas(To))
						: FString::Printf(TEXT("%s apex points   -   the highest rank"), *WithCommas(AP)), 14, false, TextDim)
				]
			]
		];

		// ---- title chooser
		TSharedRef<SWrapBox> Titles = SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(8.f, 8.f));
		Titles->AddSlot() [ Chip(Owner, INVTEXT("NO TITLE"), [this, Profile]()
		{
			FIACosmeticLoadout L = Profile->GetLoadout(); L.TitleId = 0; Profile->SetLoadout(L); SetHallView(0);
		}, [Profile]() { return Profile->GetLoadout().TitleId == 0; }, 0.f, 14) ];
		for (const IAReward::FReward& R : IAReward::All())
		{
			if (R.Category != TEXT("Title") || !Profile->IsUnlocked(R.Id))
			{
				continue;
			}
			const int32 Id = FCString::Atoi(*R.Id.ToString().RightChop(1));
			Titles->AddSlot() [ Chip(Owner, FText::FromString(R.Name), [this, Profile, Id]()
			{
				FIACosmeticLoadout L = Profile->GetLoadout(); L.TitleId = Id; Profile->SetLoadout(L); SetHallView(0);
			}, [Profile, Id]() { return Profile->GetLoadout().TitleId == Id; }, 0.f, 14) ];
		}
		Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Text(TEXT("TITLE"), 14, true, Accent) ];
		Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 18.f) [ Titles ];

		// ---- the numbers
		Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f) [ Text(TEXT("CAREER"), 14, true, Accent) ];
		const TArray<TPair<FString, FString>> Lines = {
			{ TEXT("Kills counted"), WithCommas(Profile->GetStat("KillsCounted")) },
			{ TEXT("Matches played"), WithCommas(Profile->GetStat("Matches")) },
			{ TEXT("Wins"), WithCommas(Profile->GetStat("Wins")) },
			{ TEXT("Deaths"), WithCommas(Profile->GetStat("Deaths")) },
			{ TEXT("Flag captures"), WithCommas(Profile->GetStat("Captures")) },
			{ TEXT("Best kill streak"), WithCommas(Profile->GetStat("BestStreak")) },
			{ TEXT("Campaign stars"), FString::Printf(TEXT("%lld of 60"), Profile->GetStat("Stars")) },
			{ TEXT("Best survival wave"), WithCommas(Profile->GetStat("BestWave")) },
		};
		for (const TPair<FString, FString>& Line : Lines)
		{
			Body->AddSlot().AutoHeight().Padding(0.f, 2.f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth() [ SNew(SBox).WidthOverride(240.f) [ Text(Line.Key, 16, false, TextDim) ] ]
				+ SHorizontalBox::Slot().AutoWidth() [ Text(Line.Value, 16, true) ]
			];
		}
		Body->AddSlot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			Note([]() { return INVTEXT("Only finished matches of two minutes or more count. Kills against the easiest bots are worth little, and a match caps what it can give."); })
		];
		Body->AddSlot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				ChipDyn(Owner, [this]() { return bHallResetAsked ? INVTEXT("CLICK AGAIN TO ERASE EVERYTHING") : INVTEXT("RESET PROFILE"); },
					[this, Profile]()
					{
						if (bHallResetAsked) { Profile->ResetProfile(); bHallResetAsked = false; SetHallView(0); }
						else { bHallResetAsked = true; SetHallView(0); }
					}, [this]() { return bHallResetAsked; }, 0.f, 14)
			]
		];
	}
	else if (HallView == 1)
	{
		// ---- rewards, by category
		static const TCHAR* const Categories[7] = { TEXT("Gunsmith"), TEXT("Kill effect"), TEXT("Character"), TEXT("Title"), TEXT("Arena"), TEXT("Rules"), TEXT("Audio") };
		TSharedRef<SWrapBox> Cats = SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(8.f, 8.f));
		for (int32 I = 0; I < 7; ++I)
		{
			Cats->AddSlot() [ Chip(Owner, FText::FromString(FString(Categories[I]).ToUpper()), [this, I]() { HallCategory = I; SetHallView(1); },
				[this, I]() { return HallCategory == I; }, 0.f, 14) ];
		}
		Body->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 12.f) [ Cats ];

		int32 Shown = 0, Have = 0;
		for (const IAReward::FReward& R : IAReward::All())
		{
			if (R.Category != Categories[HallCategory])
			{
				continue;
			}
			const bool bHave = Profile->IsUnlocked(R.Id);
			const float Progress = Profile->GetProgress(R);
			++Shown;
			Have += bHave ? 1 : 0;
			FString Right = bHave ? TEXT("UNLOCKED") : R.Req;
			if (!bHave && !R.Stat.IsEmpty() && R.Threshold > 0)
			{
				Right = FString::Printf(TEXT("%s   (%s of %s)"), *R.Req, *WithCommas(Profile->GetStat(*R.Stat)), *WithCommas(R.Threshold));
			}
			Body->AddSlot().AutoHeight().Padding(0.f, 3.f)
			[
				SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(1.f, 1.f, 1.f, bHave ? 0.10f : 0.04f)).Padding(10.f, 6.f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 12.f, 0.f) [ Square(bHave ? Accent : FLinearColor(1.f, 1.f, 1.f, 0.18f), 12.f) ]
					+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot().AutoHeight() [ Text(R.Name, 17, true, bHave ? FLinearColor::White : FLinearColor(0.70f, 0.72f, 0.78f)) ]
						+ SVerticalBox::Slot().AutoHeight() [ Text(R.Desc, 13, false, TextDim) ]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 2.f, 0.f, 0.f) [ Text(Right, 13, false, bHave ? Accent : FLinearColor(0.90f, 0.78f, 0.45f)) ]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 3.f, 0.f, 0.f) [ bHave || R.Stat.IsEmpty() ? StaticCastSharedRef<SWidget>(SNullWidget::NullWidget) : Bar(Progress, Accent, 260.f, 6.f) ]
					]
				]
			];
		}
		Body->AddSlot().AutoHeight().Padding(0.f, 12.f, 0.f, 0.f) [ Text(FString::Printf(TEXT("%d of %d unlocked"), Have, Shown), 14, false, TextDim) ];
	}
	else
	{
		// ---- medals
		const TArray<IAReward::FMedal>& Medals = IAReward::Medals();
		for (int32 I = 0; I < Medals.Num(); ++I)
		{
			const IAReward::FMedal& M = Medals[I];
			const int32 Tier = Profile->GetMedalTier(I);
			const int64 Value = Profile->GetStat(M.Stat);
			const int32 NextTier = FMath::Min(Tier, 4);
			TSharedRef<SHorizontalBox> Plates = SNew(SHorizontalBox);
			for (int32 T = 0; T < 5; ++T)
			{
				Plates->AddSlot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f) [ Square(T < Tier ? TierColor(T) : FLinearColor(1.f, 1.f, 1.f, 0.14f), 22.f) ];
			}
			Body->AddSlot().AutoHeight().Padding(0.f, 4.f)
			[
				SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(1.f, 1.f, 1.f, 0.05f)).Padding(10.f, 6.f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot().AutoHeight() [ Text(M.Name, 17, true) ]
						+ SVerticalBox::Slot().AutoHeight()
						[
							Text(Tier >= 5 ? FString::Printf(TEXT("%s %s   -   complete"), *WithCommas(Value), M.What)
								: FString::Printf(TEXT("%s of %s %s for %s"), *WithCommas(Value), *WithCommas(M.Tier[NextTier]), M.What, IAReward::TierNames[NextTier]), 13, false, TextDim)
						]
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center) [ Plates ]
				]
			];
		}
		Body->AddSlot().AutoHeight().Padding(0.f, 10.f, 0.f, 0.f) [ Text(TEXT("Rust, Bronze, Silver, Gold, Obsidian. Every plate gives apex points."), 13, false, TextDim) ];
	}

	return Frame(INVTEXT("HALL OF CHAMPIONS"), Body, BuildBackButton());
}
