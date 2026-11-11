// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "IAAnimInstance.generated.h"

class UAnimSequence;

/**
 * Third-person animation of every character, written in code (no animation blueprint).
 *
 * It blends the Mannequin pack's rifle clips directly: 8 directions of walking and jogging, an idle pose,
 * jump, fall and landing, a lowered crouch pose, and an aim offset that bends the upper body with the
 * player's view pitch. The poses are extracted from the animation sequences in the proxy (see IAAnimInstance.cpp).
 * Everything the clips need lives under /Game/Characters/Mannequins, which is always cooked.
 */
UCLASS(Transient)
class INSTAGIBARENA_API UIAAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;

	/** One line with the state of the animation (developer logs). */
	FString GetDebugString() const;

	/** Keeps the loaded clips alive. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UAnimSequence>> Clips;
};
