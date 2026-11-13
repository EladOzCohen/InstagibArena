// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IAFlame.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInstanceDynamic;

/**
 * A cheap decorative fire: torch, brazier, fire barrel, fire pit.
 *
 * Three crossed vertical quads carry an animated procedural flame material (M_IAFlame, noise scrolling upwards,
 * additive, no textures), two more carry a few drifting embers (M_IAEmbers), and a small shadowless point light
 * flickers. Everything animates in the material from the time node; the only per-frame work is the light, ticked
 * at 15 Hz. Dedicated servers destroy the actor (it is cosmetic).
 *
 * Maps place it through Tools/mapkit_fx.py: MapBuilder.flame(label, x, y, z, scale=1.0, colour=...).
 * Actor origin = bottom centre of the fire. FlameScale 1 = about 75 cm tall and 45 cm wide.
 */
UCLASS()
class INSTAGIBARENA_API AIAFlame : public AActor
{
	GENERATED_BODY()

public:
	AIAFlame();

	virtual void Tick(float DeltaSeconds) override;

	/** 1 = about 75 cm tall. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flame")
	float FlameScale = 1.f;

	/** Outer colour of the flame (the core is a hotter yellow). Orange by default; blue-green for chemical fires. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flame")
	FLinearColor FlameColor = FLinearColor(1.f, 0.30f, 0.05f);

	/** Brightness of the flame material (emissive multiplier). The world look has low bloom, so 1-2.5. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flame")
	float Glow = 1.3f;

	/** Flicker light in candela; 0 = no light (the map has its own accent light). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flame")
	float LightCandela = 25.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flame")
	float LightRadius = 450.f;

	/** A few drifting embers above the flame. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flame")
	bool bEmbers = true;

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Quads;

	float Seed = 0.f;
	float LightBase = 0.f;
	float TimeAcc = 0.f;
};
