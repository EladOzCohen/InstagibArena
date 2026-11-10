// Instagib Arena

#pragma once

#include "CoreMinimal.h"

/** Maps offered by the main menu. Add a line here when a new map exists. */
struct FIAMapInfo
{
	const TCHAR* DisplayName;
	const TCHAR* AssetPath;
	const TCHAR* Description;
};

namespace IAMaps
{
	inline const FIAMapInfo List[] = {
		{ TEXT("Foundry"), TEXT("/Game/Maps/DM-Foundry"),
		  TEXT("An industrial yard with a central tower, ramps and a catwalk ring.") },
		{ TEXT("Sunken Temple"), TEXT("/Game/Maps/DM-Temple"),
		  TEXT("A sandstone ziggurat surrounded by columns and corner pavilions.") },
		{ TEXT("Orbital Dock"), TEXT("/Game/Maps/DM-Dock"),
		  TEXT("A closed space-station hangar with mezzanines and two reactor cores.") },
		{ TEXT("Skyline"), TEXT("/Game/Maps/DM-Skyline"),
		  TEXT("Rooftops joined by bridges at sunset. Fall off and you are out.") },
	};

	inline constexpr int32 Count = UE_ARRAY_COUNT(List);

	/** Path of the main menu level. */
	inline const TCHAR* const MenuPath = TEXT("/Game/Maps/MainMenu");
}
