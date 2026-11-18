// Instagib Arena
#pragma once

#include "CoreMinimal.h"
#include "IACharacterRoster.h"

/**
 * Colour variants ("liveries") of a roster character: the same model and gear, other colours (docs/REWARDS_DESIGN.md 5.3 C6/C7, 5.6 R5).
 * Chosen by FIACosmeticLoadout::CharacterVariant. Works for every look (0..LookCount-1); the roster entries are not touched.
 */
namespace IACharacterVariants
{
	enum : uint8
	{
		Standard = 0,
		Veteran = 1,    // darker, weathered and less saturated; the accent is kept
		Elite = 2,      // gold accent, more metal
		Obsidian = 3,   // near black, gold accent, red glow
		Count = 4
	};

	/**
	 * The look with the colours of the variant. OutGlow is the colour of the small lit parts (visors, eyes): the accent, except for
	 * Obsidian (red). Standard returns the look unchanged.
	 */
	INSTAGIBARENA_API FIACharacterLook Apply(const FIACharacterLook& Base, uint8 Variant, FLinearColor& OutGlow);
}
