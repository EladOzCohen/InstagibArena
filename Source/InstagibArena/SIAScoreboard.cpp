// Instagib Arena

#include "SIAScoreboard.h"
#include "IAGameState.h"
#include "IAMenuStyle.h"
#include "IAPlayerState.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	const float ColRank = 44.f;
	const float ColName = 300.f;
	const float ColKills = 84.f;
	const float ColDeaths = 96.f;
	const float ColKD = 74.f;
	const float ColAcc = 84.f;
	const float ColStreak = 96.f;
	const float ColPing = 74.f;

	const FLinearColor RedColor(1.f, 0.36f, 0.34f);
	const FLinearColor BlueColor(0.42f, 0.62f, 1.f);

	FLinearColor TeamColor(uint8 Team)
	{
		if (Team == 0) { return RedColor; }
		if (Team == 1) { return BlueColor; }
		return FLinearColor::White;
	}

	/** One fixed-width cell. */
	TSharedRef<SWidget> Cell(TAttribute<FText> Text, float Width, EHorizontalAlignment Align, const FLinearColor& Color, int32 Size, bool bBold = false)
	{
		return SNew(SBox).WidthOverride(Width)
		[
			SNew(STextBlock).Text(Text).Font(IAMenu::Font(Size, bBold)).ColorAndOpacity(Color)
				.Justification(Align == HAlign_Right ? ETextJustify::Right : (Align == HAlign_Center ? ETextJustify::Center : ETextJustify::Left))
				.OverflowPolicy(ETextOverflowPolicy::Clip)
		];
	}
}

void SIAScoreboard::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	ChildSlot
	[
		SAssignNew(Body, SVerticalBox)
	];
}

void SIAScoreboard::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

	const UWorld* World = Owner.IsValid() ? Owner->GetWorld() : nullptr;
	const AIAGameState* GS = World ? World->GetGameState<AIAGameState>() : nullptr;
	if (!GS)
	{
		return;
	}

	TArray<const AIAPlayerState*> Players;
	for (APlayerState* PS : GS->PlayerArray)
	{
		if (const AIAPlayerState* State = Cast<AIAPlayerState>(PS))
		{
			Players.Add(State);
		}
	}

	const bool bTeamGame = GS->IsTeamGame();
	Players.Sort([bTeamGame](const AIAPlayerState& A, const AIAPlayerState& B)
	{
		if (bTeamGame && A.Team != B.Team)
		{
			return A.Team < B.Team;
		}
		if (A.Kills != B.Kills)
		{
			return A.Kills > B.Kills;
		}
		if (A.Deaths != B.Deaths)
		{
			return A.Deaths < B.Deaths;
		}
		return A.SlotId < B.SlotId;
	});

	// In a team game the leading team goes first.
	if (bTeamGame && GS->BlueScore > GS->RedScore)
	{
		Players.StableSort([](const AIAPlayerState& A, const AIAPlayerState& B) { return A.Team > B.Team; });
	}

	TArray<int32> NewSignature;
	NewSignature.Add(bTeamGame ? 1 : 0);
	for (const AIAPlayerState* State : Players)
	{
		NewSignature.Add(State->SlotId);
		NewSignature.Add(State->Team);
	}
	if (NewSignature != Signature)
	{
		Signature = NewSignature;
		Rebuild(Players, bTeamGame, GS->RedScore, GS->BlueScore);
	}
}

TSharedRef<SWidget> SIAScoreboard::MakeHeaderRow() const
{
	const FLinearColor Dim = IAMenu::TextDim;
	return SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.f))
		.Padding(FMargin(14.f, 4.f))
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth() [ Cell(INVTEXT("#"), ColRank, HAlign_Left, Dim, 13) ]
			+ SHorizontalBox::Slot().AutoWidth() [ Cell(INVTEXT("PLAYER"), ColName, HAlign_Left, Dim, 13) ]
			+ SHorizontalBox::Slot().AutoWidth() [ Cell(INVTEXT("KILLS"), ColKills, HAlign_Right, Dim, 13) ]
			+ SHorizontalBox::Slot().AutoWidth() [ Cell(INVTEXT("DEATHS"), ColDeaths, HAlign_Right, Dim, 13) ]
			+ SHorizontalBox::Slot().AutoWidth() [ Cell(INVTEXT("K/D"), ColKD, HAlign_Right, Dim, 13) ]
			+ SHorizontalBox::Slot().AutoWidth() [ Cell(INVTEXT("ACC"), ColAcc, HAlign_Right, Dim, 13) ]
			+ SHorizontalBox::Slot().AutoWidth() [ Cell(INVTEXT("STREAK"), ColStreak, HAlign_Right, Dim, 13) ]
			+ SHorizontalBox::Slot().AutoWidth() [ Cell(INVTEXT("PING"), ColPing, HAlign_Right, Dim, 13) ]
		];
}

TSharedRef<SWidget> SIAScoreboard::MakeTeamRow(int32 Team, TFunction<int32()> Score) const
{
	const FLinearColor Color = TeamColor(static_cast<uint8>(Team));
	return SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(Color.R, Color.G, Color.B, 0.22f))
		.Padding(FMargin(14.f, 5.f))
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().FillWidth(1.f)
			[
				SNew(STextBlock).Text(Team == 0 ? INVTEXT("RED TEAM") : INVTEXT("BLUE TEAM"))
					.Font(IAMenu::Font(18, true)).ColorAndOpacity(Color)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(STextBlock).Text_Lambda([Score]() { return FText::AsNumber(Score()); })
					.Font(IAMenu::Font(22, true)).ColorAndOpacity(Color)
			]
		];
}

TSharedRef<SWidget> SIAScoreboard::MakePlayerRow(TWeakObjectPtr<const AIAPlayerState> State, int32 Rank, bool bLocal) const
{
	const AIAPlayerState* S = State.Get();
	const FLinearColor NameColor = (S && S->Team != IA_NoTeam) ? TeamColor(S->Team) : FLinearColor::White;
	const bool bBot = S && S->bIsBotPlayer;

	auto Number = [State](TFunction<FText(const AIAPlayerState&)> Get)
	{
		return TAttribute<FText>::CreateLambda([State, Get]()
		{
			const AIAPlayerState* P = State.Get();
			return P ? Get(*P) : FText::GetEmpty();
		});
	};

	const FLinearColor Base = FLinearColor(0.92f, 0.93f, 0.97f);
	const FLinearColor Highlight = bLocal ? FLinearColor(1.f, 0.42f, 0.f, 0.30f) : FLinearColor(0.f, 0.f, 0.f, 0.34f);

	return SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(Highlight)
		.Padding(FMargin(14.f, 5.f))
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Cell(Rank > 0 ? FText::AsNumber(Rank) : FText::GetEmpty(), ColRank, HAlign_Left, IAMenu::TextDim, 18)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SBox).WidthOverride(ColName)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth()
					[
						SNew(STextBlock).Text(Number([](const AIAPlayerState& P) { return FText::FromString(P.GetPlayerName()); }))
							.Font(IAMenu::Font(18, bLocal)).ColorAndOpacity(NameColor)
							.OverflowPolicy(ETextOverflowPolicy::Ellipsis)
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8.f, 1.f, 0.f, 0.f)
					[
						SNew(STextBlock).Text(bBot ? INVTEXT("BOT") : (bLocal ? INVTEXT("YOU") : FText::GetEmpty()))
							.Font(IAMenu::Font(11, true)).ColorAndOpacity(bBot ? IAMenu::TextDim : IAMenu::Accent)
					]
				]
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Cell(Number([](const AIAPlayerState& P) { return FText::AsNumber(P.Kills); }), ColKills, HAlign_Right, FLinearColor::White, 20, true)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Cell(Number([](const AIAPlayerState& P) { return FText::AsNumber(P.Deaths); }), ColDeaths, HAlign_Right, Base, 18)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Cell(Number([](const AIAPlayerState& P) { return FText::FromString(FString::Printf(TEXT("%.2f"), P.GetKillDeathRatio())); }),
					ColKD, HAlign_Right, Base, 18)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Cell(Number([](const AIAPlayerState& P)
				{
					return P.ShotsFired > 0 ? FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(P.GetAccuracy()))) : INVTEXT("-");
				}), ColAcc, HAlign_Right, Base, 18)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Cell(Number([](const AIAPlayerState& P) { return FText::AsNumber(P.BestStreak); }), ColStreak, HAlign_Right, Base, 18)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				Cell(Number([](const AIAPlayerState& P)
				{
					return P.bIsBotPlayer ? INVTEXT("-") : FText::AsNumber(FMath::RoundToInt(P.GetPingInMilliseconds()));
				}), ColPing, HAlign_Right, IAMenu::TextDim, 16)
			]
		];
}

void SIAScoreboard::Rebuild(const TArray<const AIAPlayerState*>& Ordered, bool bTeamGame, int32 RedScore, int32 BlueScore)
{
	Body->ClearChildren();
	Body->AddSlot().AutoHeight() [ MakeHeaderRow() ];

	const APlayerState* LocalState = Owner.IsValid() ? Owner->PlayerState : nullptr;
	const TWeakObjectPtr<APlayerController> WeakOwner = Owner;
	int32 Rank = 0;
	int32 LastTeam = -2;
	for (const AIAPlayerState* State : Ordered)
	{
		if (bTeamGame && State->Team != LastTeam)
		{
			LastTeam = State->Team;
			Rank = 0;
			const int32 Team = State->Team;
			Body->AddSlot().AutoHeight().Padding(0.f, 6.f, 0.f, 2.f)
			[
				MakeTeamRow(Team, [WeakOwner, Team]()
				{
					const AIAGameState* GS = WeakOwner.IsValid() ? WeakOwner->GetWorld()->GetGameState<AIAGameState>() : nullptr;
					return GS ? (Team == 0 ? GS->RedScore : GS->BlueScore) : 0;
				})
			];
		}
		++Rank;
		Body->AddSlot().AutoHeight().Padding(0.f, 1.f)
		[
			MakePlayerRow(State, Rank, State == LocalState)
		];
	}
}
