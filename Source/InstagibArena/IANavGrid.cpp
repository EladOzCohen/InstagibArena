// Instagib Arena

#include "IANavGrid.h"
#include "InstagibArena.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "CollisionQueryParams.h"
#include "Algo/Reverse.h"
#include "GameFramework/PlayerStart.h"

namespace
{
	constexpr float CapsuleRadius = 30.f;
	constexpr float CapsuleHalfHeight = 88.f;
	constexpr float MaxStepUp = 110.f;   // largest height difference between linked cells
	constexpr float SweepLift = 25.f;    // lets the capsule glide over tiny bumps
}

bool UIANavGrid::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->IsGameWorld() && World->GetNetMode() != NM_Client;
}

void UIANavGrid::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	Build(InWorld);
}

void UIANavGrid::Build(UWorld& World)
{
	const double StartTime = FPlatformTime::Seconds();

	FBox Bounds(ForceInit);
	for (TActorIterator<AStaticMeshActor> It(&World); It; ++It)
	{
		Bounds += It->GetComponentsBoundingBox();
	}
	if (!Bounds.IsValid)
	{
		UE_LOG(LogInstagib, Warning, TEXT("NavGrid: no static geometry found, bots will not be able to path"));
		return;
	}

	const float Top = Bounds.Max.Z + 200.f;
	const float Bottom = Bounds.Min.Z - 200.f;
	const int32 CellsX = FMath::CeilToInt((Bounds.Max.X - Bounds.Min.X) / CellSize);
	const int32 CellsY = FMath::CeilToInt((Bounds.Max.Y - Bounds.Min.Y) / CellSize);

	const FCollisionObjectQueryParams ObjectParams(ECC_WorldStatic);
	const FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(IANavBuild), false);
	const FCollisionShape Capsule = FCollisionShape::MakeCapsule(CapsuleRadius, CapsuleHalfHeight);

	TMap<FIntPoint, TArray<int32>> CellNodes;

	for (int32 IX = 0; IX < CellsX; ++IX)
	{
		for (int32 IY = 0; IY < CellsY; ++IY)
		{
			const float X = Bounds.Min.X + (IX + 0.5f) * CellSize;
			const float Y = Bounds.Min.Y + (IY + 0.5f) * CellSize;

			TArray<FHitResult> Hits;
			World.LineTraceMultiByObjectType(Hits, FVector(X, Y, Top), FVector(X, Y, Bottom), ObjectParams, QueryParams);

			for (const FHitResult& Hit : Hits)
			{
				if (Hit.ImpactNormal.Z < 0.7f)
				{
					continue; // walls and undersides
				}

				const FVector Ground = Hit.ImpactPoint;
				const FVector CapsuleCenter = Ground + FVector(0.f, 0.f, CapsuleHalfHeight + 2.f);
				if (World.OverlapAnyTestByObjectType(CapsuleCenter, FQuat::Identity, ObjectParams, Capsule, QueryParams))
				{
					continue; // not enough room to stand
				}

				FNavNode Node;
				Node.Location = Ground;
				Node.Cell = FIntPoint(IX, IY);
				const int32 Index = Nodes.Add(Node);
				CellNodes.FindOrAdd(Node.Cell).Add(Index);
			}
		}
	}

	// Link neighbouring cells when the capsule can move between them.
	int32 LinkCount = 0;
	for (int32 I = 0; I < Nodes.Num(); ++I)
	{
		for (int32 DX = -1; DX <= 1; ++DX)
		{
			for (int32 DY = -1; DY <= 1; ++DY)
			{
				if (DX == 0 && DY == 0)
				{
					continue;
				}

				const TArray<int32>* Neighbours = CellNodes.Find(Nodes[I].Cell + FIntPoint(DX, DY));
				if (!Neighbours)
				{
					continue;
				}

				for (const int32 J : *Neighbours)
				{
					if (FMath::Abs(Nodes[J].Location.Z - Nodes[I].Location.Z) > MaxStepUp)
					{
						continue;
					}

					// Three sweeps: up from the start, across at the height of the higher cell
					// (clears stair edges), and down onto the end. Ramps and stairs both work.
					const float CenterOffset = CapsuleHalfHeight + 2.f + SweepLift;
					const FVector A = Nodes[I].Location;
					const FVector B = Nodes[J].Location;
					const float CrossZ = FMath::Max(A.Z, B.Z) + CenterOffset;
					const FVector AStart = A + FVector(0.f, 0.f, CenterOffset);
					const FVector BEnd = B + FVector(0.f, 0.f, CenterOffset);
					const FVector AUp(A.X, A.Y, CrossZ);
					const FVector BUp(B.X, B.Y, CrossZ);

					FHitResult Blocked;
					if (World.SweepSingleByObjectType(Blocked, AStart, AUp, FQuat::Identity, ObjectParams, Capsule, QueryParams)
						|| World.SweepSingleByObjectType(Blocked, AUp, BUp, FQuat::Identity, ObjectParams, Capsule, QueryParams)
						|| World.SweepSingleByObjectType(Blocked, BUp, BEnd, FQuat::Identity, ObjectParams, Capsule, QueryParams))
					{
						continue;
					}

					Nodes[I].Links.Add(J);
					++LinkCount;
				}
			}
		}
	}

	// Label connected areas so that bots never pick a goal on an island they cannot reach.
	int32 ComponentCount = 0;
	TArray<int32> Stack;
	for (int32 Seed = 0; Seed < Nodes.Num(); ++Seed)
	{
		if (Nodes[Seed].ComponentId != INDEX_NONE)
		{
			continue;
		}
		Nodes[Seed].ComponentId = ComponentCount;
		Stack.Add(Seed);
		while (Stack.Num() > 0)
		{
			const int32 Current = Stack.Pop();
			for (const int32 Next : Nodes[Current].Links)
			{
				if (Nodes[Next].ComponentId == INDEX_NONE)
				{
					Nodes[Next].ComponentId = ComponentCount;
					Stack.Add(Next);
				}
			}
		}
		++ComponentCount;
	}

	UE_LOG(LogInstagib, Log, TEXT("NavGrid: %d nodes, %d links, %d connected areas, built in %.0f ms"),
		Nodes.Num(), LinkCount, ComponentCount, (FPlatformTime::Seconds() - StartTime) * 1000.0);

	// Map check: every player start should sit in the largest connected area (the one bots can roam).
	TArray<int32> AreaSizes;
	AreaSizes.Init(0, ComponentCount);
	for (const FNavNode& Node : Nodes)
	{
		++AreaSizes[Node.ComponentId];
	}
	int32 Largest = 0;
	for (int32 I = 1; I < ComponentCount; ++I)
	{
		Largest = AreaSizes[I] > AreaSizes[Largest] ? I : Largest;
	}
	{
		// The few biggest areas with their centre, to see what is cut off from what.
		TArray<int32> Order;
		for (int32 I = 0; I < ComponentCount; ++I)
		{
			Order.Add(I);
		}
		Order.Sort([&AreaSizes](int32 A, int32 B) { return AreaSizes[A] > AreaSizes[B]; });
		for (int32 K = 0; K < FMath::Min(6, Order.Num()); ++K)
		{
			FVector Sum = FVector::ZeroVector;
			for (const FNavNode& Node : Nodes)
			{
				if (Node.ComponentId == Order[K])
				{
					Sum += Node.Location;
				}
			}
			UE_LOG(LogInstagib, Log, TEXT("NavGrid: area %d has %d nodes around %s"), Order[K], AreaSizes[Order[K]],
				*(Sum / FMath::Max(1, AreaSizes[Order[K]])).ToCompactString());
		}
	}
	int32 Starts = 0, StartsOutside = 0;
	for (TActorIterator<APlayerStart> It(&World); It; ++It)
	{
		++Starts;
		const int32 Node = FindNearestNode(It->GetActorLocation() - FVector(0.f, 0.f, 110.f));
		if (Node == INDEX_NONE || Nodes[Node].ComponentId != Largest)
		{
			++StartsOutside;
			UE_LOG(LogInstagib, Warning, TEXT("NavGrid: PlayerStart %s at %s is not in the largest area"),
				*It->GetName(), *It->GetActorLocation().ToString());
		}
	}
	UE_LOG(LogInstagib, Log, TEXT("NavGrid: largest area %d of %d nodes; %d of %d player starts outside it"),
		Largest < ComponentCount ? AreaSizes[Largest] : 0, Nodes.Num(), StartsOutside, Starts);
}

int32 UIANavGrid::FindNearestNode(const FVector& Location) const
{
	int32 Best = INDEX_NONE;
	float BestCost = 700.f;
	for (int32 I = 0; I < Nodes.Num(); ++I)
	{
		const FVector Delta = Nodes[I].Location - Location;
		// Height differences are penalised so that we stay on the layer we are standing on.
		const float Cost = FVector2D(Delta.X, Delta.Y).Size() + 3.f * FMath::Abs(Delta.Z);
		if (Cost < BestCost)
		{
			BestCost = Cost;
			Best = I;
		}
	}
	return Best;
}

bool UIANavGrid::GetRandomLocation(const FVector& Avoid, float MinDistance, FVector& OutLocation) const
{
	const int32 Origin = FindNearestNode(Avoid);
	if (Nodes.IsEmpty() || Origin == INDEX_NONE)
	{
		return false;
	}

	// Only goals in the same connected area as the bot are reachable.
	const int32 Area = Nodes[Origin].ComponentId;
	for (int32 Try = 0; Try < 40; ++Try)
	{
		const FNavNode& Node = Nodes[FMath::RandRange(0, Nodes.Num() - 1)];
		if (Node.ComponentId == Area && FVector::Dist2D(Node.Location, Avoid) >= MinDistance)
		{
			OutLocation = Node.Location;
			return true;
		}
	}
	return false;
}

bool UIANavGrid::FindPath(const FVector& From, const FVector& To, TArray<FVector>& OutPath) const
{
	OutPath.Reset();

	const int32 Start = FindNearestNode(From);
	const int32 Goal = FindNearestNode(To);
	if (Start == INDEX_NONE || Goal == INDEX_NONE)
	{
		return false;
	}
	if (Start == Goal)
	{
		OutPath.Add(Nodes[Goal].Location);
		return true;
	}

	struct FOpenEntry
	{
		int32 Index;
		float F;
		bool operator<(const FOpenEntry& Other) const { return F < Other.F; }
	};

	TArray<float> GScore;
	GScore.Init(TNumericLimits<float>::Max(), Nodes.Num());
	TArray<int32> Parent;
	Parent.Init(INDEX_NONE, Nodes.Num());
	TBitArray<> Closed(false, Nodes.Num());

	TArray<FOpenEntry> Open;
	GScore[Start] = 0.f;
	Open.HeapPush({ Start, static_cast<float>(FVector::Dist(Nodes[Start].Location, Nodes[Goal].Location)) });

	bool bFound = false;
	while (Open.Num() > 0)
	{
		FOpenEntry Current;
		Open.HeapPop(Current);

		if (Closed[Current.Index])
		{
			continue;
		}
		Closed[Current.Index] = true;

		if (Current.Index == Goal)
		{
			bFound = true;
			break;
		}

		for (const int32 Next : Nodes[Current.Index].Links)
		{
			if (Closed[Next])
			{
				continue;
			}
			const float Tentative = GScore[Current.Index] + static_cast<float>(FVector::Dist(Nodes[Current.Index].Location, Nodes[Next].Location));
			if (Tentative < GScore[Next])
			{
				GScore[Next] = Tentative;
				Parent[Next] = Current.Index;
				Open.HeapPush({ Next, Tentative + static_cast<float>(FVector::Dist(Nodes[Next].Location, Nodes[Goal].Location)) });
			}
		}
	}

	if (!bFound)
	{
		return false;
	}

	for (int32 I = Goal; I != INDEX_NONE; I = Parent[I])
	{
		OutPath.Add(Nodes[I].Location);
	}
	Algo::Reverse(OutPath);
	return true;
}
