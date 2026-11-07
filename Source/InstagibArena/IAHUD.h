// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "IAHUD.generated.h"

/** Minimal HUD: crosshair, match clock, scores and an end-of-match scoreboard. */
UCLASS()
class INSTAGIBARENA_API AIAHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void BeginPlay() override;
	virtual void DrawHUD() override;

	/** Flashes an X around the crosshair: white for a hit, red and bigger for a kill. */
	void ShowHitMarker(bool bKilled);

	/** Shows a line of text in the middle of the screen for a few seconds. */
	void AddMessage(const FString& Text, const FLinearColor& Color, float Duration);

private:
	struct FMessage
	{
		FString Text;
		FLinearColor Color;
		float EndTime;
	};

	TArray<FMessage> Messages;
	float HitMarkerStart = -10.f;
	bool bHitMarkerKill = false;
	bool bWasMatchOver = false;
};
