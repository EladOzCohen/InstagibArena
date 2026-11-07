// Instagib Arena

#pragma once

#include "CoreMinimal.h"

/** Maps offered by the main menu. Add a line here when a new map exists. */
struct FIAMapInfo
{
	const TCHAR* DisplayName;
	const TCHAR* AssetPath;
};

namespace IAMaps
{
	inline const FIAMapInfo List[] = {
		{ TEXT("Foundry"), TEXT("/Game/Maps/DM-Foundry") },
		{ TEXT("Sunken Temple"), TEXT("/Game/Maps/DM-Temple") },
		{ TEXT("Orbital Dock"), TEXT("/Game/Maps/DM-Dock") },
		{ TEXT("Skyline"), TEXT("/Game/Maps/DM-Skyline") },
	};

	inline constexpr int32 Count = UE_ARRAY_COUNT(List);

	/** Path of the main menu level. */
	inline const TCHAR* const MenuPath = TEXT("/Game/Maps/MainMenu");
}
