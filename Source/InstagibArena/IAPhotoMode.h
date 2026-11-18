// Instagib Arena

#pragma once

#include "CoreMinimal.h"

class APlayerController;
class ACameraActor;
class AActor;
class SWidget;

/**
 * Photo Mode (reward A3, opened from the pause menu): the match is paused, the HUD hidden, and a free camera flies
 * through the arena. WASD move, mouse looks, Q / E down / up, Shift faster, mouse wheel zoom (field of view),
 * P saves a picture (Saved/Screenshots/Photos, without the hint line) and Esc goes back to the pause menu.
 * Offline matches only (a game with other players cannot be paused).
 *
 * The controller owns it and calls Tick from PlayerTick (bShouldPerformFullTickWhenPaused is on while it runs, so the
 * camera and the input keep working in the paused world). Development: -IAPhotoAuto moves the camera and saves a picture.
 */
class FIAPhotoMode
{
public:
	/** True when this player may open it now; otherwise Reason says why (for the pause menu). */
	static bool CanStart(const APlayerController* PC, FText* Reason = nullptr);

	explicit FIAPhotoMode(APlayerController* InPC);
	~FIAPhotoMode();

	/** Every frame (real time). Returns false when the player wants to leave (Esc). */
	bool Tick();

private:
	void SavePhoto();
	void End();

	TWeakObjectPtr<APlayerController> PC;
	TWeakObjectPtr<ACameraActor> Camera;
	TWeakObjectPtr<AActor> OldViewTarget;
	TSharedPtr<SWidget> Hint;
	FVector Location = FVector::ZeroVector;
	FRotator Rotation = FRotator::ZeroRotator;
	float Fov = 90.f;
	bool bHudWasShown = true;
	bool bPausedByUs = false;
	double StartTime = 0.0;
	double SavedUntil = 0.0;
	FString SavedName;
	int32 AutoStep = 0;
};
