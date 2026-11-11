// Instagib Arena

#include "IAHUD.h"
#include "IAAudioSubsystem.h"
#include "IAGameState.h"
#include "IAInputConfig.h"
#include "IAPlayerState.h"
#include "Engine/Canvas.h"
#include "Engine/World.h"

void AIAHUD::BeginPlay()
{
	Super::BeginPlay();

	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
	{
		Audio->Play2D(EIASound::MatchStart);
	}
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
	if (Messages.Num() > 4)
	{
		Messages.RemoveAt(0);
	}
}

void AIAHUD::DrawHUD()
{
	Super::DrawHUD();

	if (!Canvas)
	{
		return;
	}

	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;

	// Hit marker: four short diagonal strokes that open up and fade.
	{
		const float Duration = bHitMarkerKill ? 0.55f : 0.25f;
		const float T = (Now - HitMarkerStart) / Duration;
		if (T >= 0.f && T < 1.f)
		{
			const float CX = Canvas->ClipX * 0.5f;
			const float CY = Canvas->ClipY * 0.5f;
			const float Inner = (bHitMarkerKill ? 12.f : 9.f) + 8.f * T;
			const float Outer = Inner + (bHitMarkerKill ? 16.f : 10.f);
			FLinearColor Color = bHitMarkerKill ? FLinearColor(1.f, 0.15f, 0.1f) : FLinearColor::White;
			Color.A = 1.f - T;
			const float Thickness = bHitMarkerKill ? 3.5f : 2.5f;
			for (int32 SX = -1; SX <= 1; SX += 2)
			{
				for (int32 SY = -1; SY <= 1; SY += 2)
				{
					DrawLine(CX + SX * Inner, CY + SY * Inner, CX + SX * Outer, CY + SY * Outer, Color, Thickness);
				}
			}
		}
	}

	// Messages ("You fragged X", "Fragged by Y").
	Messages.RemoveAll([Now](const FMessage& M) { return M.EndTime <= Now; });
	float MessageY = Canvas->ClipY * 0.5f + 130.f;
	for (const FMessage& Message : Messages)
	{
		float Width = 0.f, Height = 0.f;
		GetTextSize(Message.Text, Width, Height, nullptr, 1.8f);
		FLinearColor Color = Message.Color;
		Color.A = FMath::Clamp((Message.EndTime - Now) / 0.5f, 0.f, 1.f);
		DrawText(Message.Text, Color, Canvas->ClipX * 0.5f - Width * 0.5f, MessageY, nullptr, 1.8f);
		MessageY += Height + 6.f;
	}

	// The HUD exists only on the local machine, so it is a convenient place for the end-of-match sound.
	if (const AIAGameState* State = GetWorld() ? GetWorld()->GetGameState<AIAGameState>() : nullptr)
	{
		if (State->bMatchOver && !bWasMatchOver)
		{
			if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
			{
				Audio->Play2D(EIASound::MatchEnd);
			}
		}
		bWasMatchOver = State->bMatchOver;
	}

	const float CenterX = Canvas->ClipX * 0.5f;
	const float CenterY = Canvas->ClipY * 0.5f;

	// Crosshair.
	DrawLine(CenterX - 12.f, CenterY, CenterX - 4.f, CenterY, FLinearColor::White, 2.f);
	DrawLine(CenterX + 4.f, CenterY, CenterX + 12.f, CenterY, FLinearColor::White, 2.f);
	DrawLine(CenterX, CenterY - 12.f, CenterX, CenterY - 4.f, FLinearColor::White, 2.f);
	DrawLine(CenterX, CenterY + 4.f, CenterX, CenterY + 12.f, FLinearColor::White, 2.f);

	const AIAGameState* GS = GetWorld() ? GetWorld()->GetGameState<AIAGameState>() : nullptr;
	if (!GS)
	{
		return;
	}

	// Clock and limits.
	const int32 Minutes = GS->ClockSeconds / 60;
	const int32 Seconds = GS->ClockSeconds % 60;
	FString Header = FString::Printf(TEXT("%s   %02d:%02d"), GS->IsTeamGame() ? TEXT("Team Deathmatch") : TEXT("Free For All"), Minutes, Seconds);
	if (GS->ScoreLimit > 0)
	{
		Header += FString::Printf(TEXT("   Score limit %d"), GS->ScoreLimit);
	}
	DrawText(Header, FLinearColor::White, 20.f, 16.f, nullptr, 1.4f);

	if (GS->IsTeamGame())
	{
		DrawText(FString::Printf(TEXT("RED %d"), GS->RedScore), FLinearColor(1.f, 0.2f, 0.2f), 20.f, 46.f, nullptr, 1.6f);
		DrawText(FString::Printf(TEXT("BLUE %d"), GS->BlueScore), FLinearColor(0.3f, 0.5f, 1.f), 140.f, 46.f, nullptr, 1.6f);
	}

	// Personal score.
	if (const AIAPlayerState* MyState = PlayerOwner ? PlayerOwner->GetPlayerState<AIAPlayerState>() : nullptr)
	{
		DrawText(FString::Printf(TEXT("Kills %d   Deaths %d"), MyState->Kills, MyState->Deaths),
			FLinearColor::White, 20.f, Canvas->ClipY - 50.f, nullptr, 1.4f);
	}

	// Scoreboard: always visible after the match, otherwise while Tab is held.
	const bool bShowBoard = GS->bMatchOver || (PlayerOwner && PlayerOwner->IsInputKeyDown(IAInput::GetKey(TEXT("Scoreboard"))));
	if (!bShowBoard)
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
	Players.Sort([](const AIAPlayerState& A, const AIAPlayerState& B) { return A.Kills > B.Kills; });

	float Y = CenterY - 120.f;
	if (GS->bMatchOver)
	{
		DrawText(GS->WinnerText, FLinearColor::Yellow, CenterX - 140.f, Y - 50.f, nullptr, 2.4f);
	}
	DrawText(TEXT("Player"), FLinearColor::Gray, CenterX - 220.f, Y, nullptr, 1.2f);
	DrawText(TEXT("Kills"), FLinearColor::Gray, CenterX + 60.f, Y, nullptr, 1.2f);
	DrawText(TEXT("Deaths"), FLinearColor::Gray, CenterX + 140.f, Y, nullptr, 1.2f);
	Y += 28.f;

	for (const AIAPlayerState* State : Players)
	{
		FLinearColor Color = FLinearColor::White;
		if (State->Team == 0) { Color = FLinearColor(1.f, 0.35f, 0.35f); }
		else if (State->Team == 1) { Color = FLinearColor(0.4f, 0.6f, 1.f); }

		const FString Name = State->bIsBotPlayer ? State->GetPlayerName() + TEXT(" (bot)") : State->GetPlayerName();
		DrawText(Name, Color, CenterX - 220.f, Y, nullptr, 1.2f);
		DrawText(FString::FromInt(State->Kills), Color, CenterX + 60.f, Y, nullptr, 1.2f);
		DrawText(FString::FromInt(State->Deaths), Color, CenterX + 140.f, Y, nullptr, 1.2f);
		Y += 24.f;
	}
}
