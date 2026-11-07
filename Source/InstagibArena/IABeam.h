// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IABeam.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;

/**
 * The visible trail of an instagib shot: a glowing cylinder from the muzzle to the impact point
 * that thins out and vanishes. Purely cosmetic, so it is created locally on every machine.
 */
UCLASS()
class INSTAGIBARENA_API AIABeam : public AActor
{
	GENERATED_BODY()

public:
	AIABeam();

	void Init(const FVector& Start, const FVector& End, const FLinearColor& Color);

	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> Material;

	float Age = 0.f;
	float Lifetime = 0.4f;
	float StartThickness = 5.f;
	float Length = 100.f;
};
