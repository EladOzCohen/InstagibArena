// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "IACosmetics.h"
#include "IAMenuPlayerController.generated.h"

class SIAMainMenu;
class AIAPlayerCharacter;

/**
 * Shows the main menu, frees the mouse and looks through the menu level's camera.
 * Also stands the selected character on the stage, slowly turning, as a preview.
 */
UCLASS()
class INSTAGIBARENA_API AIAMenuPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AIAMenuPlayerController();

	virtual void Tick(float DeltaSeconds) override;

	// ---- the Gunsmith (SIAGunsmith): a close look at the rifle of the preview character

	/** Shows this loadout on the preview character (rifle, colour variant). */
	void SetPreviewLoadout(const FIACosmeticLoadout& Loadout);

	/** Moves the camera to a close-up of the preview character's rifle (true) or back (false). */
	void SetGunsmithView(bool bOn);

	/** Turns the preview character (degrees, 0 = the rifle seen from the side). */
	void SetGunsmithTurn(float Degrees) { GunsmithTurn = Degrees; }
	float GetGunsmithTurn() const { return GunsmithTurn; }

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void SpawnPreview(const class ACameraActor* Camera);
	void ShowPreviewCharacter(int32 CharacterIndex);

	/** A screen opened (0 main ... 6 how to play): the Character screen moves the camera in for a close-up. */
	void OnMenuPageChanged(int32 PageIndex);
	/** Moves the menu camera: a slow drift on the main screens, a smooth move to the close-up on the Character screen. */
	void UpdateMenuCamera(float DeltaSeconds);

	TSharedPtr<SIAMainMenu> Menu;

	UPROPERTY(Transient)
	TObjectPtr<AIAPlayerCharacter> Preview;

	UPROPERTY(Transient)
	TObjectPtr<class ACameraActor> MenuCameraActor;

	FVector PreviewLocation = FVector::ZeroVector;
	float PreviewBaseYaw = 0.f;
	float CycleTimer = 0.f;
	int32 CycleIndex = 0;

	// The camera as placed in the level, and the state of its motion.
	FVector BaseCameraLocation = FVector::ZeroVector;
	FRotator BaseCameraRotation = FRotator::ZeroRotator;
	float BaseCameraFov = 90.f;
	float CloseUp = 0.f;           // 0 = the camera of the level, 1 = the close-up of the character
	float CloseUpTarget = 0.f;
	float DriftWeight = 0.f;       // 0 = still, 1 = drifting (fades out while the camera moves between screens)
	float DriftHold = 0.f;         // seconds the drift stays quiet after a screen change
	float DriftTime = 0.f;

	// The Gunsmith close-up of the rifle.
	float GunsmithBlend = 0.f;     // 0 = the other cameras, 1 = the rifle close-up
	float GunsmithTarget = 0.f;
	float GunsmithTurn = 0.f;
	float PreviewYaw = 0.f;
	FVector RifleFocus = FVector::ZeroVector;
	bool bHaveRifleFocus = false;
};
