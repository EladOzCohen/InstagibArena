// Instagib Arena

#pragma once

#include "CoreMinimal.h"

class UWorld;

/**
 * Times of day of a map (reward M1, docs/REWARDS_DESIGN.md 5.5): URL option Variant=dusk|night, replicated in
 * AIAGameState::MapVariant and applied on every machine when the match begins.
 *
 * The maps are lit by the actors Tools/maplooks.py places (apply_look): one movable DirectionalLight (the sun), a SkyLight
 * with the panorama cube map, an ExponentialHeightFog, one unbound PostProcessVolume (fixed exposure) and the sky dome
 * (a StaticMeshActor with the material instance MI_Sky_<map>, parent M_IASkySun). Apply() drives the same actors at runtime:
 * the dusk / night panorama (/Game/Sky/T_Sky_dusk, T_Sky_night_city) is turned so that its sun or moon is where the light
 * comes from, and sun, ambient, fog and exposure take the preset of the variant (plus a small per-map correction).
 * The built look is remembered on the first call, so applying "day" again restores it.
 *
 * Development (not in shipping builds):
 *   -IAVariantTune="ev=0.4,sun=7,pitch=-14,sky=1.1,bright=0.5,fog=0.002,sat=1,con=1.08,bloom=0.2,moon=1"  overrides the preset
 *   -IAVariantShots=prefix [-IAVariantShotsAt=18]  takes Saved/IAShots/<prefix>_day|dusk|night.png (no HUD) in one run
 */
namespace IAMapVariant
{
	/** 0 = day (as built), 1 = dusk, 2 = night. Does nothing on maps without variants (space arenas, Quarry). */
	void Apply(UWorld* World, int32 Variant);
}
