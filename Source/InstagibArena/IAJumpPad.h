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
class ACharacter;

/**
 * A pad that throws any character that steps on it along a fixed velocity.
 *
 * Look: a square steel launch plate set into the floor with a raised rim, chevrons painted (and lit) in PadColor
 * pointing along the launch direction, and a faint column of rising light streaks. All animation is done by
 * the materials (M_IAPad, M_IAPadColumn in /Game/Materials/FX) from the time node, so the pad costs one small
 * light and a handful of static meshes; it only writes a material parameter during the flash after a launch.
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

	/** The steel slab the pad is made of (its top is flush with the rim's inner edge). */
	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Base;

	/** The painted deck with the chevrons (a flat plane just above the slab). */
	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Deck;

	/** Four bars around the deck: the raised rim. */
	UPROPERTY(VisibleAnywhere)
	TArray<TObjectPtr<UStaticMeshComponent>> Rim;

	/** Open cylinder of rising light streaks. */
	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Column;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UBoxComponent> Trigger;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> DeckMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> ColumnMaterial;

	/** Time of the last launch per character, so that one step does not fire twice. */
	TMap<TWeakObjectPtr<AActor>, double> LastLaunch;

#if !UE_BUILD_SHIPPING
	/** Development test (-IAPadTest): the server drops every human player onto the first pad every few seconds,
	 *  and every machine logs the launched character's position so that server and client can be compared. */
	void PadTestStep();
	bool bPadTest = false;
	FTimerHandle PadTestTimer;
	TArray<TPair<TWeakObjectPtr<ACharacter>, double>> Watched;
#endif

	double FlashUntil = 0.0;
	float Phase = 0.f;
	bool bFlashShown = false;
};
