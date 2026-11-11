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
	TObjectPtr<UInputAction> MenuAction;

	/** Text in the middle of this player's screen. Sent by the server, shown by the HUD. */
	UFUNCTION(Client, Reliable)
	void ClientShowMessage(const FString& Text, FLinearColor Color, float Duration);

	/**
	 * True while the pause menu is open or the match is over (results screen). The character ignores
	 * firing, jumping and dodging then.
	 */
	bool IsMenuOpen() const { return bMenuOpen || bMatchFrozen; }

	void OpenPause();
	void ClosePause();

	/** Server to the dead player: who killed you, from where, and how long until you respawn. Drives the death camera and the HUD panel. */
	UFUNCTION(Client, Reliable)
	void ClientYouDied(APlayerState* KillerState, APawn* KillerPawn, FVector KillerLocation, FVector VictimLocation, FRotator VictimView, float RespawnDelay);

	/** What the HUD needs to show the "you were killed by" panel. Valid while bActive. */
	struct FDeathInfo
	{
		bool bActive = false;
		bool bHasKiller = false;
		float StartTime = 0.f;
		float Duration = 2.f;
		FString KillerName;
		int32 KillerCharacter = 0;
		uint8 KillerTeam = 255;
		FVector KillerLocation = FVector::ZeroVector;
		FVector VictimLocation = FVector::ZeroVector;
		TWeakObjectPtr<APawn> KillerPawn;
	};
	const FDeathInfo& GetDeathInfo() const { return Death; }

	/** The results screen: leaves the match for the main menu. */
	void LeaveToMenu() { ReturnToMenu(); }

	/** The results screen: the host starts the next match without waiting. Does nothing on a client. */
	void RequestPlayAgain();

	/** True from the end of the match until the next one begins. */
	bool IsMatchFrozen() const { return bMatchFrozen; }

	virtual void PlayerTick(float DeltaTime) override;
	virtual bool IsMoveInputIgnored() const override { return Super::IsMoveInputIgnored() || bMatchFrozen; }
	virtual bool IsLookInputIgnored() const override { return Super::IsLookInputIgnored() || bMatchFrozen; }

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

	// ---- match flow (local controller only)
	void OnPhaseChanged(uint8 NewPhase);
	void ShowResults();
	void HideResults();
	void ApplyInputMode();
	void SetFireLocked(bool bLock);
	bool bFireLocked = false;
	void UpdateDeathCamera();
	void EndDeathCamera();

	TSharedPtr<class SIAMatchResults> ResultsScreen;
	bool bMatchFrozen = false;
	uint8 LastPhase = 255;

	FDeathInfo Death;
	FRotator DeathStartView = FRotator::ZeroRotator;
	FVector DeathCameraTarget = FVector::ZeroVector;
	TWeakObjectPtr<class ACameraActor> DeathCamera;
};
