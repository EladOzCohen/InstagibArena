// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IAImpactEffect.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UPointLightComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class USkeletalMeshComponent;

/**
 * A short burst of light and sparks: where a shot lands, or where a player is destroyed.
 * Made from basic shapes and a point light, so it needs no particle assets.
 * Cosmetic only, created locally on every machine.
 *
 * Kill effects (InitKill): the look of a death chosen by the KILLER's loadout (FIACosmeticLoadout::KillEffect):
 * 1 Ash, 2 Gold Shatter, 3 Frost, 4 Glitch (pixel dissolve), 5 Ember, 6 Poof (a cartoon cloud with stars).
 * The effect follows the body until it bursts; the character hides the body at GetKillVanishTime.
 */
UCLASS()
class INSTAGIBARENA_API AIAImpactEffect : public AActor
{
	GENERATED_BODY()

public:
	AIAImpactEffect();

	/**
	 * Sets the burst up. Normal is the direction the sparks fly (away from the surface),
	 * Scale 1 is a wall hit, 2 or more is a player being destroyed.
	 */
	void Init(const FVector& Normal, const FLinearColor& Color, float InScale, int32 SparkCount);

	/** A kill effect of the given style (1..6) on a body (may be null: then around the actor's location). */
	void InitKill(uint8 Style, const FLinearColor& VictimColor, USkeletalMeshComponent* Body);

	/** Seconds after the death when the body disappears for this kill effect (the standard death keeps the body for 3.6 s). */
	static float GetKillVanishTime(uint8 Style);

	virtual void Tick(float DeltaSeconds) override;

private:
	/** One piece of a kill effect: a shape that is born, flies, spins, grows or shrinks and dies. */
	struct FBit
	{
		int32 Comp = INDEX_NONE;      // index into Sparks
		int32 Kind = 0;               // 0 debris, 1 glitch voxel (jumps around), 2 orbiting star, 3 puff (grows then shrinks), 4 spike (grows in place)
		FVector Pos = FVector::ZeroVector;
		FVector Vel = FVector::ZeroVector;
		FVector Anchor = FVector::ZeroVector;
		FRotator Rot = FRotator::ZeroRotator;
		FRotator Spin = FRotator::ZeroRotator;
		FVector Size = FVector(1.f);
		float Birth = 0.f;
		float Life = 1.f;
		float Gravity = 980.f;        // negative: rises
		float Drag = 0.f;
		float Grow = 0.f;             // seconds to reach full size
		float Phase = 0.f;
		float NextJump = 0.f;
		bool bBorn = false;
		bool bBounce = false;
		bool bFromBody = true;        // born at a random point of the body (otherwise at Anchor)
	};

	void TickKill(float DeltaSeconds);
	FVector RandomBodyPoint() const;
	UMaterialInstanceDynamic* LitMaterial(const FLinearColor& Color, float Roughness, float Metallic, float Glow = 0.f);
	UMaterialInstanceDynamic* GlowMaterial(const FLinearColor& Color, float Glow);
	FBit& AddBit(UStaticMesh* Shape, UMaterialInterface* Material, int32 Kind, float Birth, float Life, const FVector& Size);

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Flash;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Sparks;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> SparkMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> FlashMaterial;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> KillMaterials;

	TArray<FVector> Velocities;
	float Age = 0.f;
	float Life = 0.7f;
	float Scale = 1.f;
	float FlashGlow = 14.f;

	// ---- kill effect state
	uint8 KillStyle = 0;
	TArray<FBit> Bits;
	TWeakObjectPtr<USkeletalMeshComponent> Body;
	TArray<FName> BodyBones;
	float FloorZ = -1.e9f;
	float FollowUntil = 0.f;
	float FlashDelay = 0.f;
	float LightPeak = 0.f;
	float LightLength = 0.3f;
	bool bLightFlicker = false;
};
