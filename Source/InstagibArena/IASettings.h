// Instagib Arena

#pragma once

#include "CoreMinimal.h"

/** Everything the player chooses before a match. Remembered between sessions. */
struct INSTAGIBARENA_API FIAMatchSetup
{
	bool bTeamGame = false;
	int32 MapIndex = 0;
	int32 CharacterIndex = 0;
	int32 BotCount = 4;
	int32 BotSkill = 1;
	int32 ScoreLimit = 25;
	int32 TimeLimit = 10;

	void Load();
	void Save() const;
};

/** Player settings that live in GameUserSettings.ini, plus a few helpers for the menus. */
namespace IASettings
{
	/** Shown in the main menu. Keep in step with the installer's AppVersion. */
	inline const TCHAR* const GameVersion = TEXT("1.3.0");

	INSTAGIBARENA_API float GetMouseSensitivity();            // 0.1 to 3, default 1
	INSTAGIBARENA_API void SetMouseSensitivity(float Value);

	INSTAGIBARENA_API float GetFieldOfView();                 // 70 to 110 degrees, default 90
	INSTAGIBARENA_API void SetFieldOfView(float Value);

	INSTAGIBARENA_API FString GetPlayerName();                // empty when the player never set one
	INSTAGIBARENA_API void SetPlayerName(const FString& Name);

	/** The name with everything that cannot travel in a URL removed. Empty when there is nothing usable. */
	INSTAGIBARENA_API FString GetUrlSafePlayerName();

	INSTAGIBARENA_API FString GetJoinAddress();               // the host address typed last time
	INSTAGIBARENA_API void SetJoinAddress(const FString& Address);

	/** Best guess of this PC's address on the local network, for telling friends. Empty if unknown. */
	INSTAGIBARENA_API FString GetLocalAddressText();

	// ---- crosshair: the HUD draws it from these, the settings screen changes them
	inline constexpr int32 CrosshairStyleCount = 4;   // 0 cross, 1 dot, 2 circle, 3 cross with a dot
	inline constexpr int32 CrosshairColorCount = 6;   // white, green, cyan, yellow, orange, red

	INSTAGIBARENA_API int32 GetCrosshairStyle();
	INSTAGIBARENA_API void SetCrosshairStyle(int32 Style);
	INSTAGIBARENA_API int32 GetCrosshairColorIndex();
	INSTAGIBARENA_API void SetCrosshairColorIndex(int32 Index);
	INSTAGIBARENA_API FLinearColor GetCrosshairColor();
	INSTAGIBARENA_API float GetCrosshairScale();              // 0.5 to 2, default 1
	INSTAGIBARENA_API void SetCrosshairScale(float Scale);

	// ---- camera comfort: FEEL reads these, MENUS shows them. Same text in both branches on purpose.
	INSTAGIBARENA_API bool IsCameraBobEnabled();        // default true
	INSTAGIBARENA_API void SetCameraBobEnabled(bool bEnabled);
	INSTAGIBARENA_API bool IsViewRollEnabled();         // default true
	INSTAGIBARENA_API void SetViewRollEnabled(bool bEnabled);
	INSTAGIBARENA_API bool IsReducedMotion();           // default false; when true all camera motion is off
	INSTAGIBARENA_API void SetReducedMotion(bool bEnabled);

	INSTAGIBARENA_API bool IsFullscreen();
	INSTAGIBARENA_API void ApplyDisplayMode(bool bFullscreen);
}

// ===================================================================================================
// MENUS block: video, audio, interface and first-run settings. Append new keys below this line.
// ===================================================================================================
namespace IASettings
{
	/** Extra scale for the menus on top of the automatic one. 0.8 to 1.5 in steps of 0.1, default 1. */
	INSTAGIBARENA_API float GetUiScale();
	INSTAGIBARENA_API void SetUiScale(float Scale);

	/** Motion blur on or off (default on). Applies at once. */
	INSTAGIBARENA_API bool IsMotionBlurEnabled();
	INSTAGIBARENA_API void SetMotionBlurEnabled(bool bEnabled);

	/** When true (default) the game is silent while its window is not in front. Applies at once. */
	INSTAGIBARENA_API bool GetMuteWhenUnfocused();
	INSTAGIBARENA_API void SetMuteWhenUnfocused(bool bMute);

	/** False until the player has been through the welcome screen. */
	INSTAGIBARENA_API bool IsTutorialDone();
	INSTAGIBARENA_API void SetTutorialDone(bool bDone);

	/** The last addresses the player joined, newest first (at most 5). */
	INSTAGIBARENA_API TArray<FString> GetRecentAddresses();
	INSTAGIBARENA_API void AddRecentAddress(const FString& Address);

	/** Checks what the player typed on the Join screen. Returns false and fills Problem with a sentence if it cannot work. */
	INSTAGIBARENA_API bool ValidateJoinAddress(const FString& Address, FText& Problem);

	/** Applies the saved settings that Unreal does not apply by itself (motion blur, sound when unfocused). Called once at start. */
	INSTAGIBARENA_API void ApplyStartupSettings();
}
