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
	inline const TCHAR* const GameVersion = TEXT("1.1.0");

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

	INSTAGIBARENA_API bool IsFullscreen();
	INSTAGIBARENA_API void ApplyDisplayMode(bool bFullscreen);
}
