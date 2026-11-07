// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "IANavGrid.generated.h"

/**
 * Walkable-surface grid used by bots to find paths.
 *
 * Built once when the match world starts, straight from the level's static
 * geometry, so every map works without authored navigation data. Cells are
 * sampled with downward traces (several layers per column, so catwalks and
 * towers are found), then neighbours are linked when a capsule can walk
 * between them.
 */
UCLASS()
class INSTAGIBARENA_API UIANavGrid : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;

	bool IsReady() const { return Nodes.Num() > 0; }
	int32 NumNodes() const { return Nodes.Num(); }

	/** A* between the nodes nearest to the two locations. Returns false when no path exists. */
	bool FindPath(const FVector& From, const FVector& To, TArray<FVector>& OutPath) const;

	/** Picks a random node at least MinDistance away from Avoid. */
	bool GetRandomLocation(const FVector& Avoid, float MinDistance, FVector& OutLocation) const;

	/** Index of the node closest to the location, or INDEX_NONE if none is near. */
	int32 FindNearestNode(const FVector& Location) const;

	static constexpr float CellSize = 150.f;

private:
	struct FNavNode
	{
		FVector Location = FVector::ZeroVector;
		FIntPoint Cell = FIntPoint::ZeroValue;
		int32 ComponentId = INDEX_NONE; // which connected walkable area this node belongs to
		TArray<int32, TInlineAllocator<8>> Links;
	};

	void Build(UWorld& World);

	TArray<FNavNode> Nodes;
};
