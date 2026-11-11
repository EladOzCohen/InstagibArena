// Instagib Arena

#include "SIAMatchResults.h"
#include "IAGameState.h"
#include "IAMenuStyle.h"
#include "IAPlayerState.h"
#include "SIAScoreboard.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

namespace
{
	const AIAGameState* GetState(const TWeakObjectPtr<APlayerController>& Owner)
	{
		return Owner.IsValid() && Owner->GetWorld() ? Owner->GetWorld()->GetGameState<AIAGameState>() : nullptr;
	}

	/** 1 = this player (or team) won, 0 = draw, -1 = lost. */
	int32 Outcome(const TWeakObjectPtr<APlayerController>& Owner)
	{
		const AIAGameState* GS = GetState(Owner);
		const AIAPlayerState* Me = Owner.IsValid() ? Owner->GetPlayerState<AIAPlayerState>() : nullptr;
		if (!GS || !Me)
		{
			return 0;
		}
		if (GS->IsTeamGame())
		{
			return GS->WinnerTeam == IA_NoTeam ? 0 : (GS->WinnerTeam == Me->Team ? 1 : -1);
		}
		return GS->WinnerPlayerId < 0 ? 0 : (GS->WinnerPlayerId == Me->GetPlayerId() ? 1 : -1);
	}
}

void SIAMatchResults::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	PlayAgain = InArgs._OnPlayAgain;
	const TFunction<void()> MainMenu = InArgs._OnMainMenu;
	bHost = Owner.IsValid() && Owner->HasAuthority();

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.62f))
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		[
			SNew(SVerticalBox)
			// Headline.
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
			[
				SNew(STextBlock)
				.Text_Lambda([this]() { return GetHeadline(); })
				.Font(Font(64, true))
				.ColorAndOpacity_Lambda([this]() { return FSlateColor(GetHeadlineColor()); })
				.ShadowOffset(FVector2D(2.f, 2.f))
				.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.8f))
			]
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0.f, 0.f, 0.f, 18.f)
			[
				SNew(STextBlock)
				.Text_Lambda([this]() { return GetSubline(); })
				.Font(Font(24))
				.ColorAndOpacity(FLinearColor(0.9f, 0.92f, 0.97f))
			]
			// The table appears a moment after the headline.
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(PanelColor)
				.Padding(FMargin(18.f, 12.f))
				.ColorAndOpacity(TAttribute<FLinearColor>::CreateLambda([this]() { return FLinearColor(1.f, 1.f, 1.f, FMath::Clamp((Age - 1.0f) / 0.5f, 0.f, 1.f)); }))
				[
					SNew(SIAScoreboard).OwnerController(Owner)
				]
			]
			// Choice and countdown.
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0.f, 22.f, 0.f, 0.f)
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.f))
				.ColorAndOpacity(TAttribute<FLinearColor>::CreateLambda([this]() { return FLinearColor(1.f, 1.f, 1.f, FMath::Clamp((Age - 1.4f) / 0.5f, 0.f, 1.f)); }))
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 28.f, 0.f)
					[
						SNew(STextBlock)
						.Text_Lambda([this]() { return GetCountdownText(); })
						.Font(Font(20))
						.ColorAndOpacity(FLinearColor(0.9f, 0.92f, 0.97f))
					]
					+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 14.f, 0.f)
					[
						SNew(SBox)
						.Visibility(bHost ? EVisibility::Visible : EVisibility::Collapsed)
						[
							PrimaryButton(Owner, INVTEXT("PLAY AGAIN"), [this]() { if (PlayAgain) { PlayAgain(); } }, 240.f)
						]
					]
					+ SHorizontalBox::Slot().AutoWidth()
					[
						Chip(Owner, INVTEXT("MAIN MENU"), [MainMenu]() { if (MainMenu) { MainMenu(); } }, nullptr, 200.f, 20)
					]
				]
			]
		]
	];
}

void SIAMatchResults::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);
	Age += InDeltaTime;
	SetRenderOpacity(FMath::Clamp(Age / 0.4f, 0.f, 1.f));
}

FReply SIAMatchResults::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (bHost && (InKeyEvent.GetKey() == EKeys::Enter || InKeyEvent.GetKey() == EKeys::SpaceBar) && PlayAgain)
	{
		PlayAgain();
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

FText SIAMatchResults::GetHeadline() const
{
	const int32 Result = Outcome(Owner);
	return Result > 0 ? INVTEXT("VICTORY") : (Result < 0 ? INVTEXT("DEFEAT") : INVTEXT("DRAW"));
}

FLinearColor SIAMatchResults::GetHeadlineColor() const
{
	const int32 Result = Outcome(Owner);
	return Result > 0 ? FLinearColor(1.f, 0.82f, 0.2f) : (Result < 0 ? FLinearColor(0.95f, 0.32f, 0.28f) : FLinearColor(0.7f, 0.76f, 0.9f));
}

FText SIAMatchResults::GetSubline() const
{
	const AIAGameState* GS = GetState(Owner);
	if (!GS)
	{
		return FText::GetEmpty();
	}
	FString Line = GS->WinnerText;
	if (GS->IsTeamGame())
	{
		Line += FString::Printf(TEXT("   Red %d : Blue %d"), GS->RedScore, GS->BlueScore);
	}
	return FText::FromString(Line);
}

FText SIAMatchResults::GetCountdownText() const
{
	const AIAGameState* GS = GetState(Owner);
	if (!GS)
	{
		return FText::GetEmpty();
	}
	const int32 Seconds = FMath::CeilToInt(GS->GetPhaseSecondsLeft());
	if (bHost)
	{
		return FText::FromString(FString::Printf(TEXT("Next match in %d"), Seconds));
	}
	return FText::FromString(FString::Printf(TEXT("Next match in %d  (the host can start it sooner)"), Seconds));
}
