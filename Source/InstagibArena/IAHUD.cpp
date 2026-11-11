// Instagib Arena

#include "IAHUD.h"
#include "IACharacterRoster.h"
#include "IAInputConfig.h"
#include "IAMenuStyle.h"
#include "IAPlayerController.h"
#include "IAPlayerState.h"
#include "IASettings.h"
#include "SIAScoreboard.h"
#include "CanvasItem.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/SlateRenderer.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	const FLinearColor RedTeam(1.f, 0.36f, 0.34f);
	const FLinearColor BlueTeam(0.42f, 0.62f, 1.f);
	const FLinearColor Gold(1.f, 0.82f, 0.22f);
	const FLinearColor Dim(0.66f, 0.69f, 0.76f);
	const FLinearColor Accent(1.f, 0.42f, 0.f);

	FLinearColor TeamTint(uint8 Team, const FLinearColor& Fallback)
	{
		if (Team == 0) { return RedTeam; }
		if (Team == 1) { return BlueTeam; }
		return Fallback;
	}

	float EaseOut(float T)
	{
		T = FMath::Clamp(T, 0.f, 1.f);
		return 1.f - (1.f - T) * (1.f - T) * (1.f - T);
	}

	FString ClockText(int32 Seconds)
	{
		return FString::Printf(TEXT("%02d:%02d"), Seconds / 60, Seconds % 60);
	}
}

// ---------------------------------------------------------------- life cycle

void AIAHUD::BeginPlay()
{
	Super::BeginPlay();
	HudFont = GEngine ? GEngine->GetLargeFont() : nullptr;

#if !UE_BUILD_SHIPPING
	// Test helpers: -IACrosshair=style,color,scale sets (and saves) the crosshair, for screenshots.
	FString CrosshairText;
	if (FParse::Value(FCommandLine::Get(), TEXT("IACrosshair="), CrosshairText, /*bShouldStopOnSeparator*/ false))
	{
		TArray<FString> Parts;
		CrosshairText.ParseIntoArray(Parts, TEXT(","));
		if (Parts.Num() == 3)
		{
			IASettings::SetCrosshairStyle(FCString::Atoi(*Parts[0]));
			IASettings::SetCrosshairColorIndex(FCString::Atoi(*Parts[1]));
			IASettings::SetCrosshairScale(FCString::Atof(*Parts[2]));
		}
	}
#endif
}

void AIAHUD::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	BindState(nullptr);
	if (ScoreboardWidget.IsValid())
	{
		if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
		{
			Viewport->RemoveViewportWidgetContent(ScoreboardWidget.ToSharedRef());
		}
		ScoreboardWidget.Reset();
	}
	Super::EndPlay(EndPlayReason);
}

void AIAHUD::ShowHitMarker(bool bKilled)
{
	HitMarkerStart = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	bHitMarkerKill = bKilled;
}

void AIAHUD::AddMessage(const FString& Text, const FLinearColor& Color, float Duration)
{
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	Messages.Add({ Text, Color, Now + Duration });
	if (Messages.Num() > 3)
	{
		Messages.RemoveAt(0);
	}
}

void AIAHUD::BindState(AIAGameState* GS)
{
	if (BoundState.Get() == GS)
	{
		return;
	}
	if (AIAGameState* Old = BoundState.Get())
	{
		Old->OnAnnounce.Remove(AnnounceHandle);
	}
	BoundState = GS;
	AnnounceHandle.Reset();
	if (GS)
	{
		AnnounceHandle = GS->OnAnnounce.AddUObject(this, &AIAHUD::HandleAnnounce);
	}
}

const AIAPlayerState* AIAHUD::GetLocalState() const
{
	return PlayerOwner ? PlayerOwner->GetPlayerState<AIAPlayerState>() : nullptr;
}

const AIAPlayerState* AIAHUD::FindPlayer(int32 PlayerId) const
{
	if (const AGameStateBase* GS = GetWorld() ? GetWorld()->GetGameState() : nullptr)
	{
		for (APlayerState* PS : GS->PlayerArray)
		{
			const AIAPlayerState* State = Cast<AIAPlayerState>(PS);
			if (State && State->SlotId == PlayerId)
			{
				return State;
			}
		}
	}
	return nullptr;
}

// ---------------------------------------------------------------- announcements

void AIAHUD::QueueBanner(const FBanner& Banner)
{
	// A more important banner replaces a lesser one that is showing; otherwise they play one after the other.
	if (bBannerActive && Banner.Priority > CurrentBanner.Priority)
	{
		bBannerActive = false;
	}
	BannerQueue.Add(Banner);
	if (BannerQueue.Num() > 3)
	{
		BannerQueue.RemoveAt(0);
	}
}

void AIAHUD::HandleAnnounce(EIAAnnounce Kind, int32 Subject, int32 Param)
{
	const AIAPlayerState* Me = GetLocalState();
	const bool bMe = Me && Subject >= 0 && Me->SlotId == Subject;
	const AIAPlayerState* Who = FindPlayer(Subject);
	const FString WhoName = Who ? Who->GetPlayerName() : TEXT("Someone");

	FBanner B;
	B.bHasSound = true;
	switch (Kind)
	{
	case EIAAnnounce::FirstBlood:
		B.Title = TEXT("FIRST BLOOD");
		B.Sub = bMe ? TEXT("You drew first blood") : WhoName;
		B.Color = FLinearColor(1.f, 0.25f, 0.2f);
		B.Priority = 2;
		B.Sound = EIASound::FirstBlood;
		break;
	case EIAAnnounce::DoubleKill:
	case EIAAnnounce::MultiKill:
	case EIAAnnounce::UltraKill:
	case EIAAnnounce::MonsterKill:
		if (!bMe)
		{
			return;
		}
		B.Title = Kind == EIAAnnounce::DoubleKill ? TEXT("DOUBLE KILL") : Kind == EIAAnnounce::MultiKill ? TEXT("MULTI KILL")
			: Kind == EIAAnnounce::UltraKill ? TEXT("ULTRA KILL") : TEXT("MONSTER KILL");
		B.Sub = FString::Printf(TEXT("%d kills in a row"), Param);
		B.Color = Kind == EIAAnnounce::DoubleKill ? Gold : (Kind == EIAAnnounce::MultiKill ? FLinearColor(1.f, 0.62f, 0.12f) : FLinearColor(1.f, 0.38f, 0.1f));
		B.Priority = 2;
		B.Sound = Kind == EIAAnnounce::DoubleKill ? EIASound::MedalLow : (Kind == EIAAnnounce::MonsterKill ? EIASound::MedalHigh : EIASound::MedalMid);
		break;
	case EIAAnnounce::KillingSpree:
	case EIAAnnounce::Rampage:
	case EIAAnnounce::Dominating:
	case EIAAnnounce::Unstoppable:
	case EIAAnnounce::GodLike:
	{
		const TCHAR* Title = Kind == EIAAnnounce::KillingSpree ? TEXT("KILLING SPREE") : Kind == EIAAnnounce::Rampage ? TEXT("RAMPAGE")
			: Kind == EIAAnnounce::Dominating ? TEXT("DOMINATING") : Kind == EIAAnnounce::Unstoppable ? TEXT("UNSTOPPABLE") : TEXT("GOD LIKE");
		if (!bMe)
		{
			const TCHAR* Verb = Kind == EIAAnnounce::KillingSpree ? TEXT("is on a killing spree") : Kind == EIAAnnounce::Rampage ? TEXT("is on a rampage")
				: Kind == EIAAnnounce::Dominating ? TEXT("is dominating") : Kind == EIAAnnounce::Unstoppable ? TEXT("is unstoppable") : TEXT("is God-like");
			AddMessage(FString::Printf(TEXT("%s %s!"), *WhoName, Verb), FLinearColor(1.f, 0.62f, 0.2f), 3.f);
			return;
		}
		B.Title = Title;
		B.Sub = FString::Printf(TEXT("%d kills without dying"), Param);
		B.Color = FLinearColor(1.f, 0.42f, 0.05f);
		B.Priority = 3;
		B.Duration = 2.3f;
		B.Sound = Kind == EIAAnnounce::GodLike ? EIASound::StreakHigh : ((Kind == EIAAnnounce::Dominating || Kind == EIAAnnounce::Unstoppable) ? EIASound::StreakMid : EIASound::StreakLow);
		break;
	}
	case EIAAnnounce::TookLead:
	case EIAAnnounce::LostLead:
	case EIAAnnounce::TiedLead:
	{
		B.Size = 0.55f;
		B.Duration = 1.8f;
		if (Subject >= 0)
		{
			if (!bMe) { return; }
			B.Title = Kind == EIAAnnounce::TookLead ? TEXT("YOU TOOK THE LEAD") : Kind == EIAAnnounce::LostLead ? TEXT("YOU LOST THE LEAD") : TEXT("TIED FOR THE LEAD");
		}
		else
		{
			if (!Me || Me->Team != Param) { return; }
			B.Title = Kind == EIAAnnounce::TookLead ? TEXT("YOUR TEAM TOOK THE LEAD") : Kind == EIAAnnounce::LostLead ? TEXT("YOUR TEAM LOST THE LEAD") : TEXT("TEAMS TIED FOR THE LEAD");
		}
		B.Color = Kind == EIAAnnounce::TookLead ? FLinearColor(0.35f, 1.f, 0.5f) : (Kind == EIAAnnounce::LostLead ? FLinearColor(1.f, 0.4f, 0.35f) : Gold);
		B.Sound = Kind == EIAAnnounce::TookLead ? EIASound::LeadGain : (Kind == EIAAnnounce::LostLead ? EIASound::LeadLose : EIASound::LeadTie);
		break;
	}
	case EIAAnnounce::FragsLeft:
		B.Size = Param == 1 ? 0.8f : 0.55f;
		B.Title = Param == 1 ? TEXT("MATCH POINT") : FString::Printf(TEXT("%d FRAGS LEFT"), Param);
		B.Sub = Param == 1 ? TEXT("1 frag left") : TEXT("");
		B.Color = Param == 1 ? FLinearColor(1.f, 0.3f, 0.25f) : Gold;
		B.Priority = 2;
		B.Sound = EIASound::Warning;
		break;
	}
	QueueBanner(B);
}

void AIAHUD::UpdatePhase(const AIAGameState& GS, float Now)
{
	const uint8 Phase = static_cast<uint8>(GS.Phase);
	UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this);

	if (Phase != LastPhase)
	{
		const uint8 Old = LastPhase;
		LastPhase = Phase;
		BannerQueue.Reset();
		bBannerActive = false;
		LastCountdownNumber = -1;
		LastClockCue = -1;

		if (GS.Phase == EIAMatchPhase::Live && Old == static_cast<uint8>(EIAMatchPhase::Warmup))
		{
			FightStart = Now;
			if (Audio) { Audio->Play2D(EIASound::CountdownGo, 0.9f); }
		}
		else if (GS.Phase == EIAMatchPhase::Ended)
		{
			// Won, lost or drawn, from this player's point of view.
			int32 Result = 0;
			if (const AIAPlayerState* Me = GetLocalState())
			{
				if (GS.IsTeamGame()) { Result = GS.WinnerTeam == IA_NoTeam ? 0 : (GS.WinnerTeam == Me->Team ? 1 : -1); }
				else { Result = GS.WinnerPlayerId < 0 ? 0 : (GS.WinnerPlayerId == Me->SlotId ? 1 : -1); }
			}
			if (Audio) { Audio->Play2D(Result > 0 ? EIASound::Victory : (Result < 0 ? EIASound::Defeat : EIASound::MatchEnd), 0.9f); }
		}
		else if (GS.Phase == EIAMatchPhase::Warmup)
		{
			const_cast<AIAGameState&>(GS).ClearKillFeed();
			Messages.Reset();
		}
	}

	if (GS.Phase == EIAMatchPhase::Warmup)
	{
		const int32 Number = FMath::CeilToInt(GS.GetPhaseSecondsLeft());
		if (Number != LastCountdownNumber)
		{
			LastCountdownNumber = Number;
			if (Number >= 1 && Number <= 3 && Audio) { Audio->Play2D(EIASound::CountdownTick, 0.9f); }
		}
	}
}

void AIAHUD::UpdateClockCues(const AIAGameState& GS)
{
	if (GS.Phase != EIAMatchPhase::Live || GS.TimeLimitSeconds <= 0 || GS.ClockSeconds == LastClockCue)
	{
		return;
	}
	LastClockCue = GS.ClockSeconds;
	UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this);
	if (GS.ClockSeconds >= 1 && GS.ClockSeconds <= 10)
	{
		if (Audio) { Audio->Play2D(EIASound::ClockTick, 0.8f); }
	}
	else if ((GS.ClockSeconds == 60 && GS.TimeLimitSeconds > 90) || (GS.ClockSeconds == 30 && GS.TimeLimitSeconds > 45))
	{
		FBanner B;
		B.Title = GS.ClockSeconds == 60 ? TEXT("1 MINUTE LEFT") : TEXT("30 SECONDS LEFT");
		B.Size = 0.55f;
		B.Color = Gold;
		B.Duration = 1.8f;
		B.bHasSound = true;
		B.Sound = EIASound::Warning;
		QueueBanner(B);
	}
}

// ---------------------------------------------------------------- text and shapes

float AIAHUD::TextWidth(const FString& Value, float Px) const
{
	if (!Canvas || !FSlateApplication::IsInitialized())
	{
		return 0.f;
	}
	const TSharedRef<FSlateFontMeasure> Measure = FSlateApplication::Get().GetRenderer()->GetFontMeasureService();
	return Measure->Measure(Value, MakeFont(Px)).X;
}

FSlateFontInfo AIAHUD::MakeFont(float Px) const
{
	// Slate fonts are drawn crisp at their own size (the engine's canvas fonts are bitmaps that blur when scaled).
	const int32 Size = FMath::Max(8, FMath::RoundToInt(Px * FontPxToSize));
	// The canvas needs the font's UFont object (Roboto, the same family as the menus) to draw with.
	return FSlateFontInfo(HudFont, Size, Px >= 26.f ? FName(TEXT("Bold")) : FName(TEXT("Regular")));
}

float AIAHUD::Text(const FString& Value, float X, float Y, float Px, const FLinearColor& Color, int32 Align, float Scale)
{
	if (!Canvas || !FSlateApplication::IsInitialized() || Value.IsEmpty() || Color.A <= 0.01f)
	{
		return 0.f;
	}
	Px = FMath::Max(Px, 11.f) * Scale;   // never smaller than a readable label
	const float W = TextWidth(Value, Px);
	const float DrawX = Align == 1 ? X - W * 0.5f : (Align == 2 ? X - W : X);
	FCanvasTextItem Item(FVector2D(DrawX, Y - (Scale - 1.f) * Px * 0.25f), FText::FromString(Value), MakeFont(Px), Color);
	Item.EnableShadow(FLinearColor(0.f, 0.f, 0.f, Color.A * 0.85f), FVector2D(FMath::Max(1.f, Px * 0.05f), FMath::Max(1.f, Px * 0.05f)));
	Canvas->DrawItem(Item);
	return W;
}

void AIAHUD::Panel(float X, float Y, float W, float H, float Alpha, const FLinearColor& AccentColor, bool bTopLine)
{
	DrawRect(FLinearColor(0.015f, 0.02f, 0.03f, Alpha), X, Y, W, H);
	if (bTopLine)
	{
		DrawRect(AccentColor, X, Y, W, FMath::Max(2.f, 2.f * S));
	}
}

void AIAHUD::DrawTriangle(const FVector2D& A, const FVector2D& B, const FVector2D& C, const FLinearColor& Color)
{
	// Filled with lines from the tip A across the base B-C (no texture needed).
	const int32 Steps = FMath::Max(6, FMath::CeilToInt(FVector2D::Distance(B, C) / 1.5f));
	for (int32 I = 0; I <= Steps; ++I)
	{
		const FVector2D P = FMath::Lerp(B, C, static_cast<float>(I) / Steps);
		DrawLine(A.X, A.Y, P.X, P.Y, Color, 2.f);
	}
}

// ---------------------------------------------------------------- crosshair and hit marker

void AIAHUD::DrawCrosshair(float CX, float CY)
{
	const int32 Style = IASettings::GetCrosshairStyle();
	const FLinearColor Color = IASettings::GetCrosshairColor();
	const FLinearColor Outline(0.f, 0.f, 0.f, 0.6f);
	const float K = IASettings::GetCrosshairScale() * FMath::Clamp(S, 0.85f, 2.f);

	auto Stroke = [&](float X1, float Y1, float X2, float Y2)
	{
		DrawLine(X1, Y1, X2, Y2, Outline, 4.f * FMath::Max(1.f, K * 0.6f));
		DrawLine(X1, Y1, X2, Y2, Color, 2.f * FMath::Max(1.f, K * 0.6f));
	};
	auto Cross = [&]()
	{
		const float Gap = 5.f * K;
		const float Len = 10.f * K;
		Stroke(CX - Gap - Len, CY, CX - Gap, CY);
		Stroke(CX + Gap, CY, CX + Gap + Len, CY);
		Stroke(CX, CY - Gap - Len, CX, CY - Gap);
		Stroke(CX, CY + Gap, CX, CY + Gap + Len);
	};
	auto Dot = [&](float Half)
	{
		DrawRect(Outline, CX - Half - 1.5f, CY - Half - 1.5f, 2.f * Half + 3.f, 2.f * Half + 3.f);
		DrawRect(Color, CX - Half, CY - Half, 2.f * Half, 2.f * Half);
	};

	switch (Style)
	{
	case 1:  // dot
		Dot(FMath::Max(1.5f, 2.2f * K));
		break;
	case 2:  // circle
	{
		const float Radius = 9.f * K;
		const int32 Segments = 28;
		for (int32 Pass = 0; Pass < 2; ++Pass)
		{
			for (int32 I = 0; I < Segments; ++I)
			{
				const float A0 = TWO_PI * I / Segments;
				const float A1 = TWO_PI * (I + 1) / Segments;
				DrawLine(CX + Radius * FMath::Cos(A0), CY + Radius * FMath::Sin(A0), CX + Radius * FMath::Cos(A1), CY + Radius * FMath::Sin(A1),
					Pass == 0 ? Outline : Color, Pass == 0 ? 4.f : 2.f);
			}
		}
		break;
	}
	case 3:  // cross with a dot
		Cross();
		Dot(FMath::Max(1.f, 1.4f * K));
		break;
	default: // cross
		Cross();
		break;
	}
}

void AIAHUD::DrawHitMarker(float CX, float CY, float Now)
{
	// Four short diagonal strokes that open up and fade.
	const float Duration = bHitMarkerKill ? 0.55f : 0.25f;
	const float T = (Now - HitMarkerStart) / Duration;
	if (T < 0.f || T >= 1.f)
	{
		return;
	}
	const float Sc = FMath::Clamp(S, 0.85f, 2.f);
	const float Inner = ((bHitMarkerKill ? 12.f : 9.f) + 8.f * T) * Sc;
	const float Outer = Inner + (bHitMarkerKill ? 16.f : 10.f) * Sc;
	FLinearColor Color = bHitMarkerKill ? FLinearColor(1.f, 0.15f, 0.1f) : FLinearColor::White;
	Color.A = 1.f - T;
	const float Thickness = (bHitMarkerKill ? 3.5f : 2.5f) * Sc;
	for (int32 SX = -1; SX <= 1; SX += 2)
	{
		for (int32 SY = -1; SY <= 1; SY += 2)
		{
			DrawLine(CX + SX * Inner, CY + SY * Inner, CX + SX * Outer, CY + SY * Outer, Color, Thickness);
		}
	}
}

// ---------------------------------------------------------------- top bar and stats

void AIAHUD::DrawTopBar(const AIAGameState& GS, float Now)
{
	const float CX = Canvas->ClipX * 0.5f;
	const float Y0 = 14.f * S;
	const float H = 60.f * S;
	const float TimerW = 176.f * S;
	const float SideW = 230.f * S;
	const float Gap = 6.f * S;
	const float Pad = 14.f * S;

	// The clock turns red and pulses in the last 10 seconds of a timed match.
	const bool bTimed = GS.TimeLimitSeconds > 0;
	const bool bUrgent = bTimed && GS.Phase == EIAMatchPhase::Live && GS.ClockSeconds <= 10 && GS.ClockSeconds > 0;
	FLinearColor ClockColor = FLinearColor::White;
	if (bUrgent)
	{
		const float Pulse = 0.5f + 0.5f * FMath::Sin(Now * 10.f);
		ClockColor = FMath::Lerp(FLinearColor(1.f, 0.3f, 0.25f), FLinearColor(1.f, 0.85f, 0.8f), Pulse * 0.5f);
	}
	Panel(CX - TimerW * 0.5f, Y0, TimerW, H, 0.62f, bUrgent ? FLinearColor(1.f, 0.25f, 0.2f) : Accent);
	Text(ClockText(GS.ClockSeconds), CX, Y0 + (H - 42.f * S) * 0.5f, 42.f * S, ClockColor, 1, bUrgent ? 1.f + 0.06f * FMath::Max(0.f, FMath::Sin(Now * 10.f)) : 1.f);

	// Caption under the clock.
	FString Caption = GS.IsTeamGame() ? TEXT("TEAM DEATHMATCH") : TEXT("FREE FOR ALL");
	if (GS.ScoreLimit > 0)
	{
		Caption += FString::Printf(TEXT("   -   FIRST TO %d"), GS.ScoreLimit);
	}
	Text(Caption, CX, Y0 + H + 5.f * S, 13.f * S, Dim, 1);

	const AIAPlayerState* Me = GetLocalState();
	const float LeftX = CX - TimerW * 0.5f - Gap - SideW;
	const float RightX = CX + TimerW * 0.5f + Gap;

	if (GS.IsTeamGame())
	{
		const uint8 MyTeam = Me ? Me->Team : IA_NoTeam;
		const struct { float X; uint8 Team; int32 Score; const TCHAR* Name; } Sides[2] = {
			{ LeftX, 0, GS.RedScore, TEXT("RED") }, { RightX, 1, GS.BlueScore, TEXT("BLUE") } };
		for (const auto& Side : Sides)
		{
			const FLinearColor Tint = TeamTint(Side.Team, FLinearColor::White);
			Panel(Side.X, Y0, SideW, H, 0.62f, Tint);
			DrawRect(FLinearColor(Tint.R, Tint.G, Tint.B, 0.16f), Side.X, Y0, SideW, H);
			Text(Side.Name, Side.X + Pad, Y0 + 10.f * S, 20.f * S, Tint, 0);
			if (MyTeam == Side.Team)
			{
				Text(TEXT("YOUR TEAM"), Side.X + Pad, Y0 + H - 22.f * S, 12.f * S, Dim, 0);
			}
			Text(FString::FromInt(Side.Score), Side.X + SideW - Pad, Y0 + (H - 44.f * S) * 0.5f, 44.f * S, FLinearColor::White, 2);
		}
		return;
	}

	// Free for all: your rank and kills on the left, the leader (or the player chasing you) on the right.
	TArray<const AIAPlayerState*> Players;
	for (APlayerState* PS : GS.PlayerArray)
	{
		if (const AIAPlayerState* State = Cast<AIAPlayerState>(PS))
		{
			Players.Add(State);
		}
	}
	Players.Sort([](const AIAPlayerState& A, const AIAPlayerState& B) { return A.Kills > B.Kills; });

	int32 Rank = 1;
	if (Me)
	{
		for (const AIAPlayerState* P : Players)
		{
			if (P != Me && P->Kills > Me->Kills) { ++Rank; }
		}
	}
	Panel(LeftX, Y0, SideW, H, 0.62f, Accent);
	Text(TEXT("RANK"), LeftX + Pad, Y0 + 8.f * S, 12.f * S, Dim, 0);
	Text(FString::Printf(TEXT("%d / %d"), Rank, Players.Num()), LeftX + Pad, Y0 + 24.f * S, 28.f * S, FLinearColor::White, 0);
	Text(FString::FromInt(Me ? Me->Kills : 0), LeftX + SideW - Pad, Y0 + (H - 44.f * S) * 0.5f, 44.f * S, Gold, 2);

	const AIAPlayerState* Other = nullptr;
	for (const AIAPlayerState* P : Players)
	{
		if (P != Me) { Other = P; break; }
	}
	Panel(RightX, Y0, SideW, H, 0.62f, Dim);
	if (Other)
	{
		const bool bIChase = Me && Players.Num() > 0 && Players[0] != Me;
		Text(bIChase ? TEXT("LEADER") : TEXT("CHASING YOU"), RightX + Pad, Y0 + 8.f * S, 12.f * S, Dim, 0);
		FString Name = Other->GetPlayerName();
		const float MaxName = SideW - 2.f * Pad - 70.f * S;
		while (Name.Len() > 2 && TextWidth(Name, 22.f * S) > MaxName)
		{
			Name.LeftChopInline(1);
		}
		Text(Name, RightX + Pad, Y0 + 26.f * S, 22.f * S, TeamTint(Other->Team, FLinearColor::White), 0);
		Text(FString::FromInt(Other->Kills), RightX + SideW - Pad, Y0 + (H - 44.f * S) * 0.5f, 44.f * S, FLinearColor::White, 2);
	}
}

void AIAHUD::DrawStats(const AIAGameState& GS)
{
	const AIAPlayerState* Me = GetLocalState();
	if (!Me)
	{
		return;
	}
	const float Margin = 28.f * S;
	const float ColW = 92.f * S;
	const float W = ColW * 4.f + 16.f * S;
	const float H = 72.f * S;
	const float X = Margin;
	const float Y = Canvas->ClipY - Margin - H;
	Panel(X, Y, W, H, 0.55f, Accent);

	const struct { const TCHAR* Label; FString Value; FLinearColor Color; } Cells[4] = {
		{ TEXT("KILLS"), FString::FromInt(Me->Kills), FLinearColor::White },
		{ TEXT("DEATHS"), FString::FromInt(Me->Deaths), FLinearColor(0.85f, 0.87f, 0.93f) },
		{ TEXT("STREAK"), FString::FromInt(Me->Streak), Me->Streak >= 3 ? Accent : FLinearColor::White },
		{ TEXT("ACCURACY"), Me->ShotsFired > 0 ? FString::Printf(TEXT("%d%%"), FMath::RoundToInt(Me->GetAccuracy())) : FString(TEXT("-")), FLinearColor(0.85f, 0.87f, 0.93f) },
	};
	for (int32 I = 0; I < 4; ++I)
	{
		const float CellX = X + 8.f * S + ColW * I + ColW * 0.5f;
		Text(Cells[I].Value, CellX, Y + 11.f * S, 34.f * S, Cells[I].Color, 1);
		Text(Cells[I].Label, CellX, Y + H - 21.f * S, 12.f * S, Dim, 1);
	}
}

// ---------------------------------------------------------------- kill feed and messages

void AIAHUD::DrawKillFeed(const AIAGameState& GS, float Now)
{
	const TArray<FIAFeedEntry>& Feed = GS.GetKillFeed();
	if (Feed.IsEmpty())
	{
		return;
	}

	const AIAPlayerState* Me = GetLocalState();
	const float Margin = 28.f * S;
	const float RowH = 32.f * S;
	const float Px = 19.f * S;
	const float Life = 6.f;
	const float FadeStart = 5.f;

	// The newest five that are still alive, oldest on top.
	TArray<const FIAFeedEntry*> Shown;
	for (int32 I = Feed.Num() - 1; I >= 0 && Shown.Num() < 5; --I)
	{
		if (Now - Feed[I].Time < Life)
		{
			Shown.Insert(&Feed[I], 0);
		}
	}

	float Y = Margin;
	for (const FIAFeedEntry* Entry : Shown)
	{
		const float Age = Now - Entry->Time;
		const float Alpha = Age > FadeStart ? 1.f - (Age - FadeStart) / (Life - FadeStart) : 1.f;
		const float Slide = (1.f - EaseOut(Age / 0.18f)) * 40.f * S;

		const bool bMineKill = Me && Entry->KillerId == Me->SlotId;
		const bool bMineDeath = Me && Entry->VictimId == Me->SlotId;
		const bool bMine = bMineKill || bMineDeath;

		const FLinearColor Neutral(0.92f, 0.94f, 0.98f);
		FLinearColor KillerColor = TeamTint(Entry->KillerTeam, Neutral);
		FLinearColor VictimColor = TeamTint(Entry->VictimTeam, Neutral);
		if (bMineKill && Entry->KillerTeam == IA_NoTeam) { KillerColor = Gold; }
		if (bMineDeath && Entry->VictimTeam == IA_NoTeam) { VictimColor = FLinearColor(1.f, 0.5f, 0.45f); }

		FString Middle;
		if (Entry->bFell) { Middle = TEXT("fell"); }
		else if (Entry->bSuicide) { Middle = TEXT("self-fragged"); }
		const bool bArrow = !Entry->bFell && !Entry->bSuicide;

		const float Pad = 10.f * S;
		const float ArrowW = bArrow ? 22.f * S : 0.f;
		const float KillerW = bArrow ? TextWidth(Entry->KillerName, Px) : 0.f;
		const float VictimW = TextWidth(Entry->VictimName, Px);
		const float MiddleW = Middle.IsEmpty() ? 0.f : TextWidth(Middle, Px * 0.85f) + 8.f * S;
		const float RowW = Pad * 2.f + KillerW + ArrowW + VictimW + MiddleW + (bArrow ? 8.f * S : 0.f);
		const float X = Canvas->ClipX - Margin - RowW + Slide;
		const float TextY = Y + (RowH - Px) * 0.5f - 1.f;

		DrawRect(FLinearColor(0.f, 0.f, 0.f, (bMine ? 0.62f : 0.46f) * Alpha), X, Y, RowW, RowH);
		if (bMine)
		{
			DrawRect(FLinearColor(Accent.R, Accent.G, Accent.B, Alpha), X, Y, 3.f * S, RowH);
			DrawRect(FLinearColor(Accent.R, Accent.G, Accent.B, 0.18f * Alpha), X, Y, RowW, RowH);
		}

		float Cursor = X + Pad + (bMine ? 3.f * S : 0.f);
		if (bArrow)
		{
			FLinearColor C = KillerColor; C.A = Alpha;
			Text(Entry->KillerName, Cursor, TextY, Px, C, 0);
			Cursor += KillerW + 4.f * S;
			// A small arrowhead between killer and victim.
			const float MidY = Y + RowH * 0.5f;
			FLinearColor ArrowColor = FLinearColor(0.75f, 0.78f, 0.85f, Alpha);
			DrawTriangle(FVector2D(Cursor, MidY - 6.f * S), FVector2D(Cursor, MidY + 6.f * S), FVector2D(Cursor + 11.f * S, MidY), ArrowColor);
			Cursor += ArrowW - 4.f * S + 4.f * S;
		}
		FLinearColor V = VictimColor; V.A = Alpha;
		Text(Entry->VictimName, Cursor, TextY, Px, V, 0);
		if (!Middle.IsEmpty())
		{
			Text(Middle, Cursor + VictimW + 8.f * S, TextY + 2.f * S, Px * 0.85f, FLinearColor(0.7f, 0.73f, 0.8f, Alpha), 0);
		}
		Y += RowH + 4.f * S;
	}
}

void AIAHUD::DrawMessages(float Now)
{
	Messages.RemoveAll([Now](const FMessage& M) { return M.EndTime <= Now; });
	float Y = Canvas->ClipY * 0.5f + 120.f * S;
	for (const FMessage& Message : Messages)
	{
		FLinearColor Color = Message.Color;
		Color.A = FMath::Clamp((Message.EndTime - Now) / 0.5f, 0.f, 1.f);
		Text(Message.Text, Canvas->ClipX * 0.5f, Y, 24.f * S, Color, 1);
		Y += 30.f * S;
	}
}

// ---------------------------------------------------------------- banners, countdown, death

void AIAHUD::DrawBanner(float Now)
{
	if (bBannerActive && Now - CurrentBanner.Start > CurrentBanner.Duration)
	{
		bBannerActive = false;
	}
	if (!bBannerActive && BannerQueue.Num() > 0)
	{
		CurrentBanner = BannerQueue[0];
		BannerQueue.RemoveAt(0);
		CurrentBanner.Start = Now;
		bBannerActive = true;
		if (CurrentBanner.bHasSound)
		{
			if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
			{
				Audio->Play2D(CurrentBanner.Sound, 0.95f);
			}
		}
	}
	if (!bBannerActive)
	{
		return;
	}

	const float Age = Now - CurrentBanner.Start;
	const float InT = EaseOut(Age / 0.22f);
	const float OutT = FMath::Clamp((Age - (CurrentBanner.Duration - 0.4f)) / 0.4f, 0.f, 1.f);
	const float Alpha = InT * (1.f - OutT);
	const float Pop = FMath::Lerp(1.7f, 1.f, InT);
	const float CX = Canvas->ClipX * 0.5f;
	const float BaseY = Canvas->ClipY * 0.26f - OutT * 26.f * S;
	const float TitlePx = 66.f * S * CurrentBanner.Size;

	FLinearColor Color = CurrentBanner.Color;
	Color.A = Alpha;
	Text(CurrentBanner.Title, CX, BaseY - TitlePx * 0.5f, TitlePx, Color, 1, Pop);

	// A line that grows from the middle.
	const float LineW = 420.f * S * CurrentBanner.Size * EaseOut(Age / 0.4f);
	const float LineY = BaseY + TitlePx * 0.62f;
	DrawRect(FLinearColor(Color.R, Color.G, Color.B, Alpha * 0.9f), CX - LineW * 0.5f, LineY, LineW, FMath::Max(2.f, 3.f * S * CurrentBanner.Size));

	if (!CurrentBanner.Sub.IsEmpty())
	{
		Text(CurrentBanner.Sub, CX, LineY + 8.f * S, 24.f * S * FMath::Max(0.8f, CurrentBanner.Size), FLinearColor(0.93f, 0.95f, 1.f, Alpha), 1);
	}
}

void AIAHUD::DrawCountdown(const AIAGameState& GS, float Now)
{
	const float CX = Canvas->ClipX * 0.5f;
	const float CY = Canvas->ClipY * 0.34f;

	if (GS.Phase == EIAMatchPhase::Warmup)
	{
		const float Left = GS.GetPhaseSecondsLeft();
		const int32 Number = FMath::CeilToInt(Left);
		if (Number < 1)
		{
			return;
		}
		const float Frac = Number - Left;               // 0 right after the number changed
		const float Pop = 1.f + 0.55f * (1.f - EaseOut(Frac / 0.3f));
		const float Fade = 1.f - 0.5f * FMath::Clamp((Frac - 0.7f) / 0.3f, 0.f, 1.f);

		Text(TEXT("GET READY"), CX, CY - 120.f * S, 34.f * S, FLinearColor(0.92f, 0.94f, 1.f, 0.95f), 1);
		const FLinearColor NumberColor = Number == 1 ? FLinearColor(1.f, 0.55f, 0.1f, Fade) : FLinearColor(1.f, 1.f, 1.f, Fade);
		Text(FString::FromInt(Number), CX, CY - 70.f * S, Number <= 3 ? 150.f * S : 100.f * S, NumberColor, 1, Pop);
		Text(GS.IsTeamGame() ? TEXT("Team Deathmatch") : TEXT("Free For All"), CX, CY + 100.f * S, 22.f * S, Dim, 1);
		return;
	}

	const float FightAge = Now - FightStart;
	if (GS.Phase == EIAMatchPhase::Live && FightAge >= 0.f && FightAge < 1.4f)
	{
		const float Pop = 1.f + 0.7f * (1.f - EaseOut(FightAge / 0.25f));
		const float Alpha = 1.f - FMath::Clamp((FightAge - 0.9f) / 0.5f, 0.f, 1.f);
		Text(TEXT("FIGHT!"), CX, CY - 60.f * S, 130.f * S, FLinearColor(1.f, 0.45f, 0.05f, Alpha), 1, Pop);
	}
}

void AIAHUD::DrawDeath(float Now)
{
	const AIAPlayerController* PC = Cast<AIAPlayerController>(PlayerOwner);
	if (!PC || !PC->GetDeathInfo().bActive)
	{
		return;
	}
	const AIAPlayerController::FDeathInfo& Info = PC->GetDeathInfo();
	const float Age = Now - Info.StartTime;
	const float Alpha = EaseOut(Age / 0.25f);
	const float CX = Canvas->ClipX * 0.5f;
	const float CY = Canvas->ClipY * 0.5f;

	// Darken the edges a little.
	DrawRect(FLinearColor(0.15f, 0.f, 0.f, 0.22f * Alpha), 0.f, 0.f, Canvas->ClipX, Canvas->ClipY);

	const float PanelY = Canvas->ClipY * 0.66f;
	if (Info.bHasKiller)
	{
		const FLinearColor NameColor = TeamTint(Info.KillerTeam, FLinearColor(1.f, 0.95f, 0.85f));
		Text(TEXT("FRAGGED BY"), CX, PanelY, 20.f * S, FLinearColor(0.85f, 0.4f, 0.38f, Alpha), 1);
		Text(Info.KillerName, CX, PanelY + 24.f * S, 56.f * S, FLinearColor(NameColor.R, NameColor.G, NameColor.B, Alpha), 1);
		FString Detail = FString(IACharacters::GetLook(Info.KillerCharacter).Name);
		const float Meters = FVector::Dist(Info.KillerLocation, Info.VictimLocation) / 100.f;
		Detail += FString::Printf(TEXT("   -   %d m away"), FMath::RoundToInt(Meters));
		Text(Detail, CX, PanelY + 86.f * S, 20.f * S, FLinearColor(0.78f, 0.8f, 0.88f, Alpha), 1);
	}
	else
	{
		Text(TEXT("YOU FELL"), CX, PanelY + 10.f * S, 56.f * S, FLinearColor(1.f, 0.95f, 0.85f, Alpha), 1);
	}

	// Respawn timer with a bar.
	const float Left = FMath::Max(0.f, Info.Duration - Age);
	const float BarW = 340.f * S;
	const float BarY = PanelY + 128.f * S;
	Text(Left > 0.f ? FString::Printf(TEXT("Respawn in %.1f"), Left) : FString(TEXT("Respawning")), CX, BarY, 22.f * S, FLinearColor(1.f, 1.f, 1.f, Alpha), 1);
	DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.5f * Alpha), CX - BarW * 0.5f, BarY + 30.f * S, BarW, 6.f * S);
	DrawRect(FLinearColor(Accent.R, Accent.G, Accent.B, Alpha), CX - BarW * 0.5f, BarY + 30.f * S, BarW * FMath::Clamp(Age / FMath::Max(0.1f, Info.Duration), 0.f, 1.f), 6.f * S);

	// An arrow around the middle of the screen that points toward the killer, relative to where the camera looks.
	if (Info.bHasKiller && PlayerOwner && PlayerOwner->PlayerCameraManager)
	{
		const FVector CamLocation = PlayerOwner->PlayerCameraManager->GetCameraLocation();
		const FRotator CamRotation = PlayerOwner->PlayerCameraManager->GetCameraRotation();
		const FVector ToKiller = Info.KillerLocation - CamLocation;
		const float Relative = FMath::DegreesToRadians(FRotator::NormalizeAxis(ToKiller.Rotation().Yaw - CamRotation.Yaw));
		const FVector2D Dir(FMath::Sin(Relative), -FMath::Cos(Relative));
		const FVector2D Side(-Dir.Y, Dir.X);
		const float Radius = 170.f * S;
		const FVector2D Base = FVector2D(CX, CY) + Dir * Radius;
		const FLinearColor ArrowColor(1.f, 0.25f, 0.2f, Alpha);
		DrawTriangle(Base + Dir * 22.f * S, Base - Dir * 8.f * S + Side * 18.f * S, Base - Dir * 8.f * S - Side * 18.f * S, ArrowColor);
	}
}

// ---------------------------------------------------------------- the Tab scoreboard

void AIAHUD::UpdateScoreboardWidget(const AIAGameState& GS)
{
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (!Viewport || !PlayerOwner)
	{
		return;
	}
	const bool bWant = GS.Phase != EIAMatchPhase::Ended && PlayerOwner->IsInputKeyDown(IAInput::GetKey(TEXT("Scoreboard")));
	if (bWant == bScoreboardShown)
	{
		return;
	}
	bScoreboardShown = bWant;

	if (!bWant)
	{
		if (ScoreboardWidget.IsValid())
		{
			Viewport->RemoveViewportWidgetContent(ScoreboardWidget.ToSharedRef());
			ScoreboardWidget.Reset();
		}
		return;
	}

	const TWeakObjectPtr<AIAGameState> WeakState(const_cast<AIAGameState*>(&GS));
	ScoreboardWidget = SNew(SBox)
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		.Visibility(EVisibility::HitTestInvisible)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(IAMenu::PanelColor)
			.Padding(FMargin(20.f, 14.f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 8.f)
				[
					SNew(STextBlock)
					.Font(IAMenu::Font(22, true))
					.ColorAndOpacity(IAMenu::Accent)
					.Text_Lambda([WeakState]()
					{
						const AIAGameState* State = WeakState.Get();
						if (!State) { return FText::GetEmpty(); }
						FString Line = State->IsTeamGame() ? TEXT("TEAM DEATHMATCH") : TEXT("FREE FOR ALL");
						if (State->ScoreLimit > 0) { Line += FString::Printf(TEXT("   -   first to %d"), State->ScoreLimit); }
						if (State->TimeLimitSeconds > 0) { Line += FString::Printf(TEXT("   -   %s left"), *ClockText(State->ClockSeconds)); }
						return FText::FromString(Line);
					})
				]
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(SIAScoreboard).OwnerController(PlayerOwner)
				]
			]
		];
	Viewport->AddViewportWidgetContent(ScoreboardWidget.ToSharedRef(), 8);
}

// ---------------------------------------------------------------- the frame

void AIAHUD::DrawHUD()
{
	Super::DrawHUD();

	if (!Canvas || !GetWorld())
	{
		return;
	}
	if (!HudFont && GEngine)
	{
		HudFont = GEngine->GetLargeFont();
	}
	if (!HudFont)
	{
		return;
	}

	S = FMath::Clamp(Canvas->ClipY / 900.f, 0.7f, 2.5f);
	{
		float W = 0.f, H = 0.f;
		Canvas->TextSize(HudFont, TEXT("Ag"), W, H, 1.f, 1.f);
		FontRefHeight = FMath::Max(1.f, H);
	}

	const float Now = GetWorld()->GetTimeSeconds();
	AIAGameState* GS = GetWorld()->GetGameState<AIAGameState>();
	BindState(GS);
	if (!GS)
	{
		return;
	}

	UpdatePhase(*GS, Now);
	UpdateClockCues(*GS);
	UpdateScoreboardWidget(*GS);

	if (GS->Phase == EIAMatchPhase::Ended)
	{
		return;   // the results screen (Slate) takes over
	}

	const AIAPlayerController* PC = Cast<AIAPlayerController>(PlayerOwner);
	const bool bDeadView = PC && PC->GetDeathInfo().bActive;
	const float CX = Canvas->ClipX * 0.5f;
	const float CY = Canvas->ClipY * 0.5f;

	if (!bDeadView)
	{
		DrawCrosshair(CX, CY);
		DrawHitMarker(CX, CY, Now);
	}

	DrawTopBar(*GS, Now);
	DrawStats(*GS);
	DrawKillFeed(*GS, Now);
	DrawMessages(Now);
	DrawBanner(Now);
	DrawCountdown(*GS, Now);
	DrawDeath(Now);
}
