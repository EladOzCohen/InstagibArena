// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IAImpactEffect.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInstanceDynamic;

/**
 * A short burst of light and sparks: where a shot lands, or where a player is destroyed.
 * Made from basic shapes and a point light, so it needs no particle assets.
 * Cosmetic only, created locally on every machine.
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

	virtual void Tick(float DeltaSeconds) override;

private:
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

	TArray<FVector> Velocities;
	float Age = 0.f;
	float Life = 0.7f;
	float Scale = 1.f;
};
