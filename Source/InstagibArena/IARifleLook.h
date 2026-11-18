// Instagib Arena
#pragma once

#include "CoreMinimal.h"
#include "IACosmetics.h"
#include "UObject/ObjectPtr.h"

class AActor;
class USceneComponent;
class UStaticMeshComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;

/**
 * The look of the rifle from a cosmetic loadout (the Gunsmith, docs/REWARDS_DESIGN.md 5.1): colours and finishes of the six material
 * slots of SM_IARifle_FP / SM_IARifle_TP, and the extra parts (barrels, stocks, fins, charms, faction liveries, the kill counter).
 * Looks only: the muzzle point, the size of the rifle and every timing stay exactly the same. Parts are only ever added, never removed,
 * and they are small, so the first-person rifle never covers less of the screen than the standard one (and not much more).
 * The extra parts are batched: one instanced component per shape and material, so a fully dressed rifle costs a handful of draw calls.
 */
namespace IARifleLook
{
	/** The material slots of the rifle meshes, in order. */
	enum ESlot : int32 { SlotBody, SlotTrim, SlotRubber, SlotAccent, SlotCore, SlotGlass, SlotCount };

	/** The colour of the glowing core and the muzzle flash: the custom core colour, the livery's, or the character accent. */
	INSTAGIBARENA_API FLinearColor CoreColor(const FIACosmeticLoadout& Loadout, const FLinearColor& Accent);

	/** Paints one slot of the rifle (finish, livery, custom colours). Accent = the character's accent colour. */
	INSTAGIBARENA_API void StyleSlot(UMaterialInstanceDynamic* Material, int32 Slot, const FIACosmeticLoadout& Loadout, const FLinearColor& Accent);

	/**
	 * Adds the extra parts of the loadout under Root (rifle space: X forward, Y right, Z up, cm). First person: only the owner sees them;
	 * otherwise everybody but the owner. WeaponMaterial is the master material of the rifle (M_IAWeapon); the components are added to OutParts.
	 */
	INSTAGIBARENA_API void AddParts(AActor* Owner, USceneComponent* Root, bool bFirstPerson, const FIACosmeticLoadout& Loadout,
		const FLinearColor& Accent, UMaterialInterface* WeaponMaterial, TArray<TObjectPtr<UStaticMeshComponent>>& OutParts);

	/** The beam colour of a shot: the custom beam colour in free for all, otherwise the given default (team or character colour). */
	INSTAGIBARENA_API FLinearColor BeamColor(const FIACosmeticLoadout& Loadout, const FLinearColor& Default, bool bTeamGame);
}
