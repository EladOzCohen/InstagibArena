// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "IAPlayerController.generated.h"

class UInputAction;
class UInputMappingContext;

/**
 * Owns the input actions and the mapping context. They are created in code,
 * so the project needs no input assets. The possessed character binds to them.
 */
UCLASS()
class INSTAGIBARENA_API AIAPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> MappingContext;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> JumpAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> FireAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> DodgeForwardAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> DodgeBackAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> DodgeLeftAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> DodgeRightAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> CrouchAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> WalkAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MenuAction;

	/** Text in the middle of this player's screen. Sent by the server, shown by the HUD. */
	UFUNCTION(Client, Reliable)
	void ClientShowMessage(const FString& Text, FLinearColor Color, float Duration);

	/** True while the pause menu is open. The character ignores firing, jumping and dodging then. */
	bool IsMenuOpen() const { return bMenuOpen; }

	void OpenPause();
	void ClosePause();

protected:
	virtual void SetupInputComponent() override;
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** Esc: opens the pause menu, or closes it again. */
	void TogglePause();

	/** Leaves the match and opens the main menu. */
	void ReturnToMenu();

private:
	void BuildInput();
	UInputAction* MakeAction(const TCHAR* Name, bool bAxis2D);

	TSharedPtr<class SIAPauseMenu> PauseMenu;
	bool bMenuOpen = false;
};
