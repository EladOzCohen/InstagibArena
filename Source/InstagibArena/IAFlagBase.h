// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IAFlagBase.generated.h"

class AIAFlag;
class UMaterialInstanceDynamic;
class UStaticMeshComponent;

/**
 * CONTRACT for maps (Capture the Flag): the home of one team's flag. Maps place exactly one per team with
 * Tools/mapkit.py (unreal.IAFlagBase, property flag_team: 0 = red, 1 = blue) at the centre of the team's base, on the
 * ground. The Capture the Flag game mode spawns that team's flag here and a carrier scores by bringing the enemy flag
 * back to this base (inside CaptureRadius) while their own flag is at home. Team spawn points are ordinary PlayerStarts
 * with PlayerStartTag "Red" or "Blue"; untagged starts are used by every mode. Maps without bases still work: the game
 * mode creates two bases itself (AIAGameMode::CreateFallbackBases).
 *
 * The base draws a pad with a team coloured ring (the capture zone) and a socket for the pole. It is only visible in
 * Capture the Flag; in the other modes it hides itself. The flag is a separate actor (AIAFlag) spawned by the server.
 */
UCLASS()
class INSTAGIBARENA_API AIAFlagBase : public AActor
{
	GENERATED_BODY()

public:
	AIAFlagBase();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** 0 = red, 1 = blue (same numbers as AIAPlayerState::Team). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, ReplicatedUsing = OnRep_Base, Category = "CTF", meta = (ClampMin = "0", ClampMax = "1"))
	uint8 FlagTeam = 0;

	/** Radius of the capture zone in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, ReplicatedUsing = OnRep_Base, Category = "CTF")
	float CaptureRadius = 220.f;

	/** Where the flag stands (the middle of the pad, a little above the floor). */
	FVector GetFlagHome() const { return GetActorLocation() + FVector(0.f, 0.f, 6.f); }

	/** Server: creates this team's flag if it does not exist yet, and returns it. */
	AIAFlag* SpawnFlag();

	/** The base of a team in this world, or null. Works on every machine. */
	static AIAFlagBase* Find(const UWorld* World, uint8 Team);

	/** True when the pad was made by the game mode because the map has none. */
	bool bFallback = false;

protected:
	UFUNCTION()
	void OnRep_Base();

private:
	void BuildVisuals();
	void RefreshLook();

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> Pad;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> PadMaterial;

	bool bVisualsBuilt = false;
	int32 ShownMode = -1;
	uint8 AppliedTeam = 255;
	float AppliedRadius = -1.f;
};
