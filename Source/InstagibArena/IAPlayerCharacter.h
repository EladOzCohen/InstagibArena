// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "IACharacterMovement.h"
#include "IAPlayerCharacter.generated.h"

class UCameraComponent;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;
struct FInputActionValue;

/**
 * The player pawn: first-person camera, UT-style movement and the instagib rifle.
 * One hit from the rifle kills.
 */
UCLASS()
class INSTAGIBARENA_API AIAPlayerCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AIAPlayerCharacter(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void Landed(const FHitResult& Hit) override;
	virtual void FellOutOfWorld(const UDamageType& DamageType) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual float TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** Fires the rifle. Used by player input and by bots. */
	void TryFire();

	/** Dodge request. Used by player input and by bots. */
	void Dodge(EIADodgeDir Direction);

	bool IsDead() const { return bDead; }

	/** Shows a roster look without any player state. Used by the developer showroom. */
	void SetForcedLook(int32 CharacterIndex) { ForcedLook = CharacterIndex; }

	/** True for the pawn a human on this machine is controlling (not bots, not other players). */
	bool IsLocalHuman() const { return IsLocallyControlled() && Cast<APlayerController>(GetController()) != nullptr; }

	/** Time in seconds between shots. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Instagib")
	float FireInterval = 0.8f;

	/** Damage of one shot. Anything above the health kills. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Instagib")
	float ShotDamage = 1000.f;

	/** Max seconds between two taps of the same key to count as a dodge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dodge")
	float DoubleTapWindow = 0.25f;

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UCameraComponent> FirstPersonCamera;

	/** Placeholder body, visible to others only. Replaced by real character meshes later. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> BodyMesh;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> BodyMaterial;

	UPROPERTY(ReplicatedUsing = OnRep_Dead)
	bool bDead = false;

	UFUNCTION()
	void OnRep_Dead();

	UFUNCTION(Server, Reliable)
	void ServerFire();

	UFUNCTION(NetMulticast, Unreliable)
	void MulticastShotEffect(FVector Start, FVector End, FVector Normal, uint8 HitType);

	/** Tells the shooter that a shot hit someone (a short sound on the shooter's machine). */
	UFUNCTION(Client, Unreliable)
	void ClientHitConfirm(bool bKilled);

private:
	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
	void JumpPressed();
	void JumpReleased();
	void FirePressed();
	void CrouchPressed();
	void CrouchReleased();
	void WalkPressed();
	void WalkReleased();
	bool IsPauseMenuOpen() const;
	void DodgeForwardTap() { RegisterTap(0); }
	void DodgeBackTap() { RegisterTap(1); }
	void DodgeLeftTap() { RegisterTap(2); }
	void DodgeRightTap() { RegisterTap(3); }
	void RegisterTap(int32 DirIndex);

	void Die(AController* Killer);
	void UpdateBodyColor();
	void UpdateLook();
	void ApplyLook(int32 CharacterIndex, uint8 Team);
	void UpdateMovementAudio(float DeltaSeconds);

	// ---- the rifle, built from basic shapes
	void BuildWeapon(bool bFirstPerson, USkeletalMesh* MeshAsset);
	void DestroyWeapon(bool bFirstPerson);
	void UpdateWeaponView(float DeltaSeconds);
	FVector GetMuzzleLocation(const FVector& Fallback) const;

	/** The rifle the owner sees, attached to the camera. */
	UPROPERTY(Transient)
	TObjectPtr<USceneComponent> FPWeaponRoot;

	/** The rifle everyone else sees, attached to the character's torso. */
	UPROPERTY(Transient)
	TObjectPtr<USceneComponent> TPWeaponRoot;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> FPWeaponParts;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> TPWeaponParts;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> FPCoreMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> FPMuzzleFlash;

	// ---- first-person camera feel (only runs for the human playing on this machine)
	void UpdateCamera(float DeltaSeconds);

	float CamEyeOffset = 0.f;        // smooths crouching and steps (cm, decays to 0)
	float CamPrevEyeZ = 0.f;
	float CamPrevHalfHeight = 0.f;
	bool bCamHavePrev = false;
	bool bCamPrevGrounded = false;
	float CamBobPhase = 0.f;
	float CamBobAlpha = 0.f;
	float CamRoll = 0.f;             // degrees, from strafing
	float CamKick = 0.f;             // 1 right after a dodge, falls to 0
	float CamKickRoll = 0.f;         // direction of the dodge roll (-1 left, 1 right, 0 none)
	float CamLastKickTime = -10.f;
	int32 CamSeenDodgeCount = 0;
	float CamDip = 0.f;              // landing dip (cm), a damped spring
	float CamDipVelocity = 0.f;
	float CamSeenLandingTime = -10.f;
	float CamSettingsTimer = 0.f;
	bool bCamBob = true;
	bool bCamRoll = true;
	bool bCamReduced = false;

	FLinearColor CurrentAccent = FLinearColor(0.f, 0.9f, 1.f);
	float Recoil = 0.f;
	float BobTime = 0.f;

	/** Pieces attached to the skeleton (helmets, spikes, ...). */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Accessories;

	int32 ForcedLook = -1;
	int32 AppliedLookKey = INT32_MIN;
	FLinearColor GetBodyColor() const;

	float LastTapTime[4] = { -10.f, -10.f, -10.f, -10.f };
	float LastFireTime = -10.f;

	// State used to turn movement into sounds.
	float StepDistance = 0.f;
	float PrevSpeed2D = 0.f;
	float PrevVelocityZ = 0.f;
	bool bWasGrounded = true;

	// Cache used to notice team or player changes and refresh the color.
	uint8 ColoredTeam = 254;
	int32 ColoredId = -1;
};
