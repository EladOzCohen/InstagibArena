// Instagib Arena

#include "IAPlayerController.h"
#include "IAMapList.h"
#include "IAAudioSubsystem.h"
#include "IAHUD.h"
#include "IAInputConfig.h"
#include "SIAPauseMenu.h"
#include "Engine/GameViewportClient.h"
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
	SetShowMouseCursor(false);
	SetInputMode(FInputModeGameOnly());
}

void AIAPlayerController::ReturnToMenu()
{
	ClosePause();
	ClientTravel(IAMaps::MenuPath, TRAVEL_Absolute);
}
