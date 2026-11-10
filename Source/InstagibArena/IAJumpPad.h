// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IAJumpPad.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UMaterialInstanceDynamic;
class UPrimitiveComponent;

/**
 * A pad that throws any character that steps on it along a fixed velocity.
 *
 * The overlap is detected on every machine. The launch itself runs on the server (bots, remote players)
 * and on the machine that controls the character (so the owner does not see a correction), both with the
 * same velocity. Maps place pads with Tools/mapkit.py, which computes LaunchVelocity for a target point.
 */
UCLASS()
class INSTAGIBARENA_API AIAJumpPad : public AActor
{
	GENERATED_BODY()

public:
	AIAJumpPad();

	virtual void Tick(float DeltaSeconds) override;

	/** Velocity in cm/s given to the character (replaces its current velocity). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JumpPad")
	FVector LaunchVelocity = FVector(0.f, 0.f, 1400.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JumpPad")
	FLinearColor PadColor = FLinearColor(0.f, 0.8f, 1.f);

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void OnPadOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Base;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> GlowDisc;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Beam;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UBoxComponent> Trigger;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> GlowMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> BeamMaterial;

	/** Time of the last launch per character, so that one step does not fire twice. */
	TMap<TWeakObjectPtr<AActor>, double> LastLaunch;

	double FlashUntil = 0.0;
	float Phase = 0.f;
};
