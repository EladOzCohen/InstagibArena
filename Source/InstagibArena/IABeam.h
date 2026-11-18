// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IABeam.generated.h"

class UStaticMeshComponent;
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;

/**
 * The visible trail of an instagib shot: a glowing cylinder from the muzzle to the impact point
 * that thins out and vanishes. Purely cosmetic, so it is created locally on every machine.
 * Styles (the shooter's loadout, FIACosmeticLoadout::BeamStyle): 0 standard, 1 Needle (thin), 2 Lance (thick),
 * 3 Pulse (dashed), 4 Confetti (rainbow dashes and falling paper flakes).
 */
UCLASS()
class INSTAGIBARENA_API AIABeam : public AActor
{
	GENERATED_BODY()

public:
	AIABeam();

	/** bTeamColors: in team games the Confetti beam keeps the team colour in its dashes (only the paper flakes are colourful). */
	void Init(const FVector& Start, const FVector& End, const FLinearColor& Color, uint8 Style = 0, bool bTeamColors = false);

	virtual void Tick(float DeltaSeconds) override;

private:
	void BuildDashes(const FLinearColor& Color, bool bRainbow, float Period, float DashFraction, UMaterialInterface* ShellBase);
	void BuildFlakes(int32 Count);

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Mesh;

	/** Soft additive glow around the hot core (M_IAGlowShell). */
	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> Shell;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> ShellMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> Material;

	/** Pulse and Confetti: the dashes (children of the core, so they thin out with it), one component per colour. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UInstancedStaticMeshComponent>> Dashes;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> DashMaterials;

	/** Confetti: paper flakes in world space, one component per colour. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UInstancedStaticMeshComponent>> Flakes;

	struct FFlake
	{
		int32 Batch = 0;
		int32 Instance = 0;
		FVector Location = FVector::ZeroVector;
		FVector Velocity = FVector::ZeroVector;
		FRotator Rotation = FRotator::ZeroRotator;
		FRotator Spin = FRotator::ZeroRotator;
	};
	TArray<FFlake> FlakeState;

	FVector BeamStart = FVector::ZeroVector;
	FVector BeamEnd = FVector::ZeroVector;
	float Age = 0.f;
	float Lifetime = 0.4f;
	float StartThickness = 2.6f;
	float CoreGlow = 8.f;
	float ShellGlow = 2.2f;
	float FlakeLife = 0.f;
	float Length = 100.f;
};
