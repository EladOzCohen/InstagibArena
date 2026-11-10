// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
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

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void SpawnPreview(const class ACameraActor* Camera);
	void ShowPreviewCharacter(int32 CharacterIndex);

	TSharedPtr<SIAMainMenu> Menu;

	UPROPERTY(Transient)
	TObjectPtr<AIAPlayerCharacter> Preview;

	FVector PreviewLocation = FVector::ZeroVector;
	float PreviewBaseYaw = 0.f;
	float CycleTimer = 0.f;
	int32 CycleIndex = 0;
};
