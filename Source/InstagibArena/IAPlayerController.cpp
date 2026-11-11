// Instagib Arena

#include "IAPlayerController.h"
#include "IAMapList.h"
#include "IAAudioSubsystem.h"
#include "IAHUD.h"
#include "IAInputConfig.h"
#include "InstagibArena.h"
#include "IACharacterRoster.h"
#include "IAGameMode.h"
#include "IAGameState.h"
#include "IAPlayerCharacter.h"
#include "IAPlayerState.h"
#include "SIAMatchResults.h"
#include "SIAPauseMenu.h"
#include "Camera/CameraActor.h"
#include "Engine/GameViewportClient.h"
#include "Kismet/KismetMathLibrary.h"
#include "Engine/World.h"
#include "Kismet/KismetSystemLibrary.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Engine/LocalPlayer.h"

UInputAction* AIAPlayerController::MakeAction(const TCHAR* Name, bool bAxis2D)
{
	UInputAction* Action = NewObject<UInputAction>(this, Name);
	Action->ValueType = bAxis2D ? EInputActionValueType::Axis2D : EInputActionValueType::Boolean;
	return Action;
}

void AIAPlayerController::BuildInput()
{
	MappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Instagib"));

	MoveAction = MakeAction(TEXT("IA_Move"), true);
	LookAction = MakeAction(TEXT("IA_Look"), true);
	JumpAction = MakeAction(TEXT("IA_Jump"), false);
	FireAction = MakeAction(TEXT("IA_Fire"), false);
	DodgeForwardAction = MakeAction(TEXT("IA_DodgeForward"), false);
	DodgeBackAction = MakeAction(TEXT("IA_DodgeBack"), false);
	DodgeLeftAction = MakeAction(TEXT("IA_DodgeLeft"), false);
	DodgeRightAction = MakeAction(TEXT("IA_DodgeRight"), false);
	CrouchAction = MakeAction(TEXT("IA_Crouch"), false);
	WalkAction = MakeAction(TEXT("IA_Walk"), false);
	MenuAction = MakeAction(TEXT("IA_Menu"), false);

	// The keys come from the player's bindings (see IAInputConfig.h).
	const FKey ForwardKey = IAInput::GetKey(TEXT("Forward"));
	const FKey BackKey = IAInput::GetKey(TEXT("Back"));
	const FKey LeftKey = IAInput::GetKey(TEXT("Left"));
	const FKey RightKey = IAInput::GetKey(TEXT("Right"));

	// Move: forward/back go on the Y axis (swizzle), back and left are negated.
	{
		FEnhancedActionKeyMapping& Forward = MappingContext->MapKey(MoveAction, ForwardKey);
		Forward.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(this));

		FEnhancedActionKeyMapping& Back = MappingContext->MapKey(MoveAction, BackKey);
		Back.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(this));
		Back.Modifiers.Add(NewObject<UInputModifierNegate>(this));

		FEnhancedActionKeyMapping& Left = MappingContext->MapKey(MoveAction, LeftKey);
		Left.Modifiers.Add(NewObject<UInputModifierNegate>(this));

		MappingContext->MapKey(MoveAction, RightKey);
	}

	// Look: mouse, with Y inverted so that moving the mouse up looks up.
	{
		FEnhancedActionKeyMapping& Mouse = MappingContext->MapKey(LookAction, EKeys::Mouse2D);
		UInputModifierNegate* Negate = NewObject<UInputModifierNegate>(this);
		Negate->bX = false;
		Negate->bY = true;
		Negate->bZ = false;
		Mouse.Modifiers.Add(Negate);
	}

	MappingContext->MapKey(MenuAction, EKeys::Escape);
	MappingContext->MapKey(JumpAction, IAInput::GetKey(TEXT("Jump")));
	MappingContext->MapKey(FireAction, IAInput::GetKey(TEXT("Fire")));
	MappingContext->MapKey(CrouchAction, IAInput::GetKey(TEXT("Crouch")));
	MappingContext->MapKey(WalkAction, IAInput::GetKey(TEXT("Walk")));

	// The same keys also feed the double-tap dodge detection.
	MappingContext->MapKey(DodgeForwardAction, ForwardKey);
	MappingContext->MapKey(DodgeBackAction, BackKey);
	MappingContext->MapKey(DodgeLeftAction, LeftKey);
	MappingContext->MapKey(DodgeRightAction, RightKey);
}

void AIAPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	BuildInput();

	if (ULocalPlayer* LocalPlayer = GetLocalPlayer())
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			Subsystem->AddMappingContext(MappingContext, 0);
		}
	}

	if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent))
	{
		Input->BindAction(MenuAction, ETriggerEvent::Started, this, &AIAPlayerController::TogglePause);
	}
}

void AIAPlayerController::ClientShowMessage_Implementation(const FString& Text, FLinearColor Color, float Duration)
{
	if (AIAHUD* Hud = Cast<AIAHUD>(GetHUD()))
	{
		Hud->AddMessage(Text, Color, Duration);
	}
}

void AIAPlayerController::BeginPlay()
{
	Super::BeginPlay();

	// Coming back from the menu the viewport may still be in UI mode.
	if (IsLocalController())
	{
		SetShowMouseCursor(false);
		SetInputMode(FInputModeGameOnly());

		if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
		{
			Audio->PlayMusic(EIAMusic::Battle);
		}
	}
}

void AIAPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	ClosePause();
	HideResults();
	EndDeathCamera();
	Super::EndPlay(EndPlayReason);
}

void AIAPlayerController::TogglePause()
{
	if (bMenuOpen)
	{
		ClosePause();
	}
	else
	{
		OpenPause();
	}
}

void AIAPlayerController::OpenPause()
{
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (bMenuOpen || !IsLocalController() || !Viewport)
	{
		return;
	}

	PauseMenu = SNew(SIAPauseMenu)
		.OwnerController(this)
		.OnResume([this]() { ClosePause(); })
		.OnLeave([this]() { ReturnToMenu(); })
		.OnQuit([this]() { UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false); });
	Viewport->AddViewportWidgetContent(PauseMenu.ToSharedRef(), 20);

	bMenuOpen = true;
	SetIgnoreLookInput(true);
	SetIgnoreMoveInput(true);
	SetShowMouseCursor(true);

	FInputModeGameAndUI InputMode;
	InputMode.SetWidgetToFocus(PauseMenu);
	InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	InputMode.SetHideCursorDuringCapture(false);
	SetInputMode(InputMode);
}

void AIAPlayerController::ClosePause()
{
	if (!bMenuOpen)
	{
		return;
	}

	if (PauseMenu.IsValid())
	{
		if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
		{
			Viewport->RemoveViewportWidgetContent(PauseMenu.ToSharedRef());
		}
		PauseMenu.Reset();
	}

	bMenuOpen = false;
	ResetIgnoreLookInput();
	ResetIgnoreMoveInput();
	ApplyInputMode();
}

void AIAPlayerController::ReturnToMenu()
{
	ClosePause();
	HideResults();
	ClientTravel(IAMaps::MenuPath, TRAVEL_Absolute);
}

// ---------------------------------------------------------------- match flow

void AIAPlayerController::ApplyInputMode()
{
	if (!IsLocalController() || bMenuOpen)
	{
		return;
	}
	if (ResultsScreen.IsValid())
	{
		// The results screen needs the mouse.
		SetShowMouseCursor(true);
		FInputModeGameAndUI InputMode;
		InputMode.SetWidgetToFocus(ResultsScreen);
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		InputMode.SetHideCursorDuringCapture(false);
		SetInputMode(InputMode);
	}
	else
	{
		SetShowMouseCursor(false);
		SetInputMode(FInputModeGameOnly());
	}
}

void AIAPlayerController::SetFireLocked(bool bLock)
{
	if (bFireLocked == bLock || !MappingContext || !FireAction)
	{
		return;
	}
	bFireLocked = bLock;

	const FKey FireKey = IAInput::GetKey(TEXT("Fire"));
	if (bLock)
	{
		MappingContext->UnmapKey(FireAction, FireKey);
	}
	else
	{
		MappingContext->MapKey(FireAction, FireKey);
	}
	if (ULocalPlayer* LocalPlayer = GetLocalPlayer())
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			Subsystem->RequestRebuildControlMappings();
		}
	}
}

void AIAPlayerController::ShowResults()
{
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (ResultsScreen.IsValid() || !IsLocalController() || !Viewport)
	{
		return;
	}

	ResultsScreen = SNew(SIAMatchResults)
		.OwnerController(this)
		.OnPlayAgain([this]() { RequestPlayAgain(); })
		.OnMainMenu([this]() { ReturnToMenu(); });
	Viewport->AddViewportWidgetContent(ResultsScreen.ToSharedRef(), 12);
	ApplyInputMode();
}

void AIAPlayerController::HideResults()
{
	if (!ResultsScreen.IsValid())
	{
		return;
	}
	if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
	{
		Viewport->RemoveViewportWidgetContent(ResultsScreen.ToSharedRef());
	}
	ResultsScreen.Reset();
	ApplyInputMode();
}

void AIAPlayerController::RequestPlayAgain()
{
	if (HasAuthority())
	{
		if (AIAGameMode* GM = GetWorld()->GetAuthGameMode<AIAGameMode>())
		{
			GM->StartNewMatch();
		}
	}
}

void AIAPlayerController::OnPhaseChanged(uint8 NewPhase)
{
	UE_LOG(LogInstagib, Log, TEXT("%s sees match phase %d"), GetNetMode() == NM_Client ? TEXT("Client") : TEXT("Local player"), static_cast<int32>(NewPhase));
	// Nobody fires in the countdown or on the results screen: the key does nothing, so there is no recoil either.
	SetFireLocked(NewPhase != static_cast<uint8>(EIAMatchPhase::Live));
	const bool bEnded = NewPhase == static_cast<uint8>(EIAMatchPhase::Ended);
	bMatchFrozen = bEnded;
	if (bEnded)
	{
		EndDeathCamera();
		ShowResults();
	}
	else
	{
		HideResults();
	}
}

void AIAPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);

	if (!IsLocalController())
	{
		return;
	}

	if (const AIAGameState* GS = GetWorld() ? GetWorld()->GetGameState<AIAGameState>() : nullptr)
	{
		const uint8 Phase = static_cast<uint8>(GS->Phase);
		if (Phase != LastPhase)
		{
			LastPhase = Phase;
			OnPhaseChanged(Phase);
		}
	}

	UpdateDeathCamera();
}

// ---------------------------------------------------------------- death camera

void AIAPlayerController::ClientYouDied_Implementation(APlayerState* KillerState, APawn* KillerPawn, FVector KillerLocation, FVector VictimLocation, FRotator VictimView, float RespawnDelay)
{
	if (!IsLocalController() || !GetWorld())
	{
		return;
	}

	UE_LOG(LogInstagib, Log, TEXT("%s: death camera on %s (%.0f m away, respawn in %.1f s)"), GetNetMode() == NM_Client ? TEXT("Client") : TEXT("Local player"),
		KillerState ? *KillerState->GetPlayerName() : TEXT("nobody"), FVector::Dist(KillerLocation, VictimLocation) / 100.f, RespawnDelay);
	EndDeathCamera();
	Death = FDeathInfo();
	Death.bActive = true;
	Death.StartTime = GetWorld()->GetTimeSeconds();
	Death.Duration = RespawnDelay;
	Death.VictimLocation = VictimLocation;
	Death.KillerPawn = KillerPawn;
	Death.KillerLocation = KillerLocation;
	DeathStartView = VictimView;

	if (const AIAPlayerState* Killer = Cast<AIAPlayerState>(KillerState))
	{
		Death.bHasKiller = true;
		Death.KillerName = Killer->GetPlayerName();
		Death.KillerCharacter = Killer->CharacterIndex;
		Death.KillerTeam = Killer->Team;
	}

	// The camera starts where the eyes were, then pulls back and turns toward the killer.
	FVector Target;
	if (Death.bHasKiller)
	{
		const FVector Away = (VictimLocation - KillerLocation).GetSafeNormal2D();
		Target = VictimLocation + Away * 230.f + FVector(0.f, 0.f, 95.f);
	}
	else
	{
		Target = VictimLocation - DeathStartView.Vector().GetSafeNormal2D() * 220.f + FVector(0.f, 0.f, 120.f);
	}
	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(DeathCam), false);
	if (GetWorld()->LineTraceSingleByChannel(Hit, VictimLocation, Target, ECC_Visibility, Params))
	{
		Target = VictimLocation + (Target - VictimLocation) * FMath::Max(0.f, Hit.Time - 0.08f);
	}
	DeathCameraTarget = Target;

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (ACameraActor* Camera = GetWorld()->SpawnActor<ACameraActor>(VictimLocation, VictimView, SpawnParams))
	{
		DeathCamera = Camera;
		SetViewTarget(Camera);
	}
}

void AIAPlayerController::UpdateDeathCamera()
{
	if (!Death.bActive || !GetWorld())
	{
		return;
	}

	const float Elapsed = GetWorld()->GetTimeSeconds() - Death.StartTime;

	// A new body ends it (the engine gives the view back to the pawn).
	const AIAPlayerCharacter* Body = Cast<AIAPlayerCharacter>(GetPawn());
	if ((Body && !Body->IsDead() && Elapsed > 0.3f) || Elapsed > Death.Duration + 4.f)
	{
		EndDeathCamera();
		return;
	}

	ACameraActor* Camera = DeathCamera.Get();
	if (!Camera)
	{
		return;
	}

	if (const APawn* KillerPawn = Death.KillerPawn.Get())
	{
		Death.KillerLocation = KillerPawn->GetActorLocation();
	}

	const float Blend = FMath::InterpEaseInOut(0.f, 1.f, FMath::Clamp((Elapsed - 0.3f) / 0.8f, 0.f, 1.f), 2.f);
	const FVector Position = FMath::Lerp(Death.VictimLocation, DeathCameraTarget, Blend);
	const FVector LookAt = Death.bHasKiller ? Death.KillerLocation + FVector(0.f, 0.f, 40.f) : Death.VictimLocation - FVector(0.f, 0.f, 50.f);
	const FRotator LookRotation = UKismetMathLibrary::FindLookAtRotation(Position, LookAt);
	const FRotator Rotation = FQuat::Slerp(DeathStartView.Quaternion(), LookRotation.Quaternion(), Blend).Rotator();
	Camera->SetActorLocationAndRotation(Position, Rotation);
}

void AIAPlayerController::EndDeathCamera()
{
	Death.bActive = false;
	if (ACameraActor* Camera = DeathCamera.Get())
	{
		if (GetViewTarget() == Camera)
		{
			// Back to the pawn if there is one; the engine does it on the next possession otherwise.
			SetViewTarget(GetPawn() ? static_cast<AActor*>(GetPawn()) : static_cast<AActor*>(this));
		}
		Camera->Destroy();
	}
	DeathCamera.Reset();
}
