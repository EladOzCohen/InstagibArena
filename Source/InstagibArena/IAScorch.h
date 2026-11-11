// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "IAScorch.generated.h"

class UDecalComponent;
class UMaterialInstanceDynamic;

/**
 * The scorch marks that shots leave on walls. A small pool (about 30), the oldest mark is reused first.
 * A mark glows hot for a moment, then cools down and fades out. Cosmetic only: exists on every machine
 * that shows graphics, never on a dedicated server.
 */
UCLASS()
class INSTAGIBARENA_API UIAScorchSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(UIAScorchSubsystem, STATGROUP_Tickables); }

	/** Puts a mark on the surface at Location (Normal points away from the surface). */
	void AddMark(const FVector& Location, const FVector& Normal, const FLinearColor& Color);

	static UIAScorchSubsystem* Get(const UObject* WorldContext);

	static constexpr int32 MaxMarks = 30;
	static constexpr float Lifetime = 26.f;

private:
	struct FMark
	{
		TWeakObjectPtr<UDecalComponent> Decal;
		TWeakObjectPtr<UMaterialInstanceDynamic> Material;
		float Age = 0.f;
	};

	TArray<FMark> Marks;

	UPROPERTY(Transient)
	TObjectPtr<class UMaterialInterface> BaseMaterial;
};
