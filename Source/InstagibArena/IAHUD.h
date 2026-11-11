// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "Fonts/SlateFontInfo.h"
#include "IAAudioSubsystem.h"
#include "IAGameState.h"
#include "IAHUD.generated.h"

class AIAPlayerState;
class SWidget;

/**
 * The in-match HUD, drawn on the canvas (cheap, no widget tree):
 * top bar (rank and leader, or team scores, plus the clock), personal stats, crosshair from the player's settings,
 * kill feed, animated banners for medals and lead changes, the countdown, and the death panel.
 * The Tab scoreboard is a Slate widget (SIAScoreboard) shown while the key is held.
 * Everything scales with the screen height (1080 = scale 1).
 */
UCLASS()
class INSTAGIBARENA_API AIAHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void DrawHUD() override;

	/** Flashes an X around the crosshair: white for a hit, red and bigger for a kill. */
	void ShowHitMarker(bool bKilled);

	/** Shows a line of text under the crosshair for a few seconds. */
	void AddMessage(const FString& Text, const FLinearColor& Color, float Duration);

private:
	struct FMessage
	{
		FString Text;
		FLinearColor Color;
		float EndTime;
	};

	struct FBanner
	{
		FString Title;
		FString Sub;
		FLinearColor Color = FLinearColor::White;
		float Size = 1.f;       // 1 = medal size, smaller for lead changes
		int32 Priority = 1;
		float Duration = 1.9f;
		float Start = 0.f;
		bool bHasSound = false;
		EIASound Sound = EIASound::MedalLow;
	};

	// ---- events
	void BindState(AIAGameState* GS);
	void HandleAnnounce(EIAAnnounce Kind, int32 Subject, int32 Param);
	void QueueBanner(const FBanner& Banner);
	void UpdatePhase(const AIAGameState& GS, float Now);
	void UpdateClockCues(const AIAGameState& GS);
	void UpdateScoreboardWidget(const AIAGameState& GS);
	const AIAPlayerState* FindPlayer(int32 PlayerId) const;
	const AIAPlayerState* GetLocalState() const;

	// ---- drawing
	float Text(const FString& Value, float X, float Y, float Px, const FLinearColor& Color, int32 Align = 0, float Scale = 1.f);
	float TextWidth(const FString& Value, float Px) const;
	FSlateFontInfo MakeFont(float Px) const;
	static constexpr float FontPxToSize = 0.8f;   // Slate font size per pixel of text height
	void Panel(float X, float Y, float W, float H, float Alpha, const FLinearColor& Accent, bool bTopLine = true);
	void DrawCrosshair(float CX, float CY);
	void DrawHitMarker(float CX, float CY, float Now);
	void DrawTopBar(const AIAGameState& GS, float Now);
	void DrawStats(const AIAGameState& GS);
	void DrawKillFeed(const AIAGameState& GS, float Now);
	void DrawBanner(float Now);
	void DrawCountdown(const AIAGameState& GS, float Now);
	void DrawDeath(float Now);
	void DrawMessages(float Now);
	void DrawProtection(const AIAGameState& GS, float Now);
	void DrawTriangle(const FVector2D& A, const FVector2D& B, const FVector2D& C, const FLinearColor& Color);

	float S = 1.f;            // screen scale
	float FontRefHeight = 20.f;
	UPROPERTY(Transient)
	TObjectPtr<UFont> HudFont;

	TArray<FMessage> Messages;
	float HitMarkerStart = -10.f;
	bool bHitMarkerKill = false;

	TWeakObjectPtr<AIAGameState> BoundState;
	FDelegateHandle AnnounceHandle;

	TArray<FBanner> BannerQueue;
	FBanner CurrentBanner;
	bool bBannerActive = false;

	uint8 LastPhase = 255;
	int32 LastCountdownNumber = -1;
	float FightStart = -10.f;
	int32 LastClockCue = -1;

	TSharedPtr<SWidget> ScoreboardWidget;
	bool bScoreboardShown = false;
};
