// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IAFlag.generated.h"

class ACharacter;
class UMaterialInstanceDynamic;
class UPointLightComponent;
class UStaticMeshComponent;

/** Where a flag is. */
UENUM(BlueprintType)
enum class EIAFlagState : uint8
{
	Home,      // standing on its base
	Carried,   // on the back of an enemy player
	Dropped    // lying where its carrier died; returns by itself after a while or when a team mate touches it
};

/**
 * One team's flag (Capture the Flag). The server (AIAGameMode) decides everything; the actor only replicates its state
 * (state, carrier, resting place, return time) and every machine shows it by itself:
 *  - Home / Dropped: stands at RestLocation. A dropped flag falls the last bit with a cheap local animation.
 *  - Carried: attached to the carrier's mesh (spine bone), so it follows smoothly on every machine.
 * Look: a pole with a cloth that waves in the material (world position offset, no simulation), a faint light beam so
 * it can be seen from far away and a small light. Assets are in /Game/CTF (Tools/make_ctf_assets.py); without them engine
 * shapes are used.
 */
UCLASS()
class INSTAGIBARENA_API AIAFlag : public AActor
{
	GENERATED_BODY()

public:
	AIAFlag();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** Server: sets the owner team and the home place right after spawning. */
	void InitFlag(uint8 InTeam, const FVector& InHome);

	uint8 GetFlagTeam() const { return Team; }
	EIAFlagState GetFlagState() const { return State; }
	bool IsHome() const { return State == EIAFlagState::Home; }
	ACharacter* GetCarrier() const { return Carrier; }
	const FVector& GetHomeLocation() const { return HomeLocation; }
	const FVector& GetRestLocation() const { return RestLocation; }

	/** Seconds until a dropped flag returns by itself (0 when it is not dropped). */
	float GetDropSecondsLeft() const;

	/** Server: where the carrier was the last time we looked (for a carrier that vanishes). */
	const FVector& GetLastCarrierLocation() const { return LastCarrierLocation; }
	float GetCarriedSeconds() const;

	// ---- server operations (called by the game mode)
	void ServerPickUp(ACharacter* NewCarrier);

	/** Drops the flag where the carrier stood. Returns false when that place is unsafe (below the kill height, no floor): the flag went home instead. */
	bool ServerDrop(const FVector& Where, float ReturnDelaySeconds);

	void ServerReturnHome();

	/** The flag of a team in this world, or null. Works on every machine. */
	static AIAFlag* Find(const UWorld* World, uint8 Team);

	/** The flag this pawn carries, or null. */
	static AIAFlag* FindCarriedBy(const UWorld* World, const AActor* Pawn);

	static FLinearColor TeamColor(uint8 Team);

protected:
	UFUNCTION()
	void OnRep_Flag();

private:
	void BuildVisuals();
	void ApplyState();
	void UpdateLook(float DeltaSeconds);

	UPROPERTY(Replicated)
	uint8 Team = 0;

	UPROPERTY(ReplicatedUsing = OnRep_Flag)
	EIAFlagState State = EIAFlagState::Home;

	UPROPERTY(ReplicatedUsing = OnRep_Flag)
	TObjectPtr<ACharacter> Carrier;

	/** Where the flag stands when it is not carried. */
	UPROPERTY(ReplicatedUsing = OnRep_Flag)
	FVector_NetQuantize RestLocation = FVector::ZeroVector;

	UPROPERTY(Replicated)
	FVector_NetQuantize HomeLocation = FVector::ZeroVector;

	/** Server world time at which a dropped flag goes home. */
	UPROPERTY(Replicated)
	float DropEndTime = 0.f;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> Visual;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> Pole;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> Cloth;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> Beam;

	UPROPERTY(Transient)
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> ClothMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> BeamMaterial;

	bool bVisualsBuilt = false;
	bool bAttachedToCarrier = false;
	bool bHiddenForCarrier = false;
	EIAFlagState AppliedState = EIAFlagState::Home;
	uint8 AppliedTeam = 255;

	// Cosmetic fall of a dropped flag.
	float FallOffset = 0.f;
	float FallVelocity = 0.f;
	float LookClock = 0.f;

	// Server only.
	FVector LastCarrierLocation = FVector::ZeroVector;
	double CarriedSince = 0.0;
};
