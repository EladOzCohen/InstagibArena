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
		{ TEXT("Harbour Dock"), TEXT("/Game/Maps/DM-Dock"),
		  TEXT("A harbour transit shed with mezzanines, two storage tanks and stacks of containers.") },
		{ TEXT("Skyline"), TEXT("/Game/Maps/DM-Skyline"),
		  TEXT("Rooftops joined by bridges at sunset. Fall off and you are out.") },
		// --- MAPS: new maps
		{ TEXT("Neon Street"), TEXT("/Game/Maps/DM-Neon"),
		  TEXT("A city street at night, lit by shop windows and neon signs. Small, fast duels around an arcade hall.") },
		{ TEXT("Forge"), TEXT("/Game/Maps/DM-Forge"),
		  TEXT("A volcanic foundry around a lava pit, with bridges, gantries and jump pads.") },
		{ TEXT("Glacier"), TEXT("/Game/Maps/DM-Glacier"),
		  TEXT("An arctic outpost with an ice ridge, covered tunnels and a radio tower.") },
		{ TEXT("Canyon"), TEXT("/Game/Maps/DM-Canyon"),
		  TEXT("A huge desert canyon with rope bridges, high mesas and rock spires.") },
		{ TEXT("Citadel"), TEXT("/Game/Maps/DM-Citadel"),
		  TEXT("A big stone castle on a meadow: two keeps, a gatehouse, a courtyard and forest paths between. Made for Capture the Flag.") },
		{ TEXT("Quarry"), TEXT("/Game/Maps/DM-Quarry"),
		  TEXT("A huge open-pit quarry with haul roads, tunnels, a crushing plant and a loading dock. Made for Capture the Flag.") },
		{ TEXT("Downtown"), TEXT("/Game/Maps/DM-Downtown"),
		  TEXT("A big city district with streets, plazas, rooftops and underpasses. Made for Capture the Flag.") },
		{ TEXT("Orbital"), TEXT("/Game/Maps/DM-Orbital"),
		  TEXT("A research station on the edge of a gas giant: a long concourse under an open ceiling, a glowing reactor core, raised decks and two base halls.") },
		{ TEXT("Derelict"), TEXT("/Game/Maps/DM-Derelict"),
		  TEXT("A dead starship drifting in a nebula. A cargo bay with a hole in the floor, catwalks, red emergency lights, the engine room and the bridge.") },
		{ TEXT("Nexus"), TEXT("/Game/Maps/DM-Nexus"),
		  TEXT("The oldest arena of the Apex League: a stone disc floating beside a black hole, with a golden dais, eight arches and no walls.") },
	};

	inline constexpr int32 Count = UE_ARRAY_COUNT(List);

	/** Path of the main menu level. */
	inline const TCHAR* const MenuPath = TEXT("/Game/Maps/MainMenu");
}
