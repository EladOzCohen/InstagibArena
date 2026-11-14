// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "UObject/ObjectPtr.h"

class AActor;
class USkeletalMesh;
class USkeletalMeshComponent;
class UStaticMeshComponent;
struct FIACharacterLook;

namespace IAGear
{
	/**
	 * Attaches the modelled gear of a character look (helmets, plates, pauldrons, packs, cloth ... made by Tools/make_gear_assets.py,
	 * listed in IACharacterGear.inl) to the bones of the mannequin. Every piece is a static mesh in the bone's own space, so there is
	 * nothing to place. All pieces of one character share one dynamic material whose seven palette roles (plate, cloth, accent, team,
	 * trim, glow, light) get the colors of the look. Returns the number of pieces attached; 0 means the gear assets are missing and the
	 * caller falls back to the primitive accessories of the roster.
	 */
	int32 Attach(AActor* Owner, USkeletalMeshComponent* Skel, USkeletalMesh* MeshAsset, int32 LookIndex, const FIACharacterLook& Look,
		const FLinearColor& Body, const FLinearColor& AccentPaint, const FLinearColor& Accent, const FLinearColor& TeamColor, bool bTeamGame,
		float RimStrength, TArray<TObjectPtr<UStaticMeshComponent>>& OutComponents);
}
