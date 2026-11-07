// Instagib Arena

#include "IAPlayerController.h"
#include "IAMapList.h"
#include "IAAudioSubsystem.h"
#include "IAHUD.h"
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
	MenuAction = MakeAction(TEXT("IA_Menu"), false);

	// Move: W/S go on the Y axis (swizzle), S and A are negated.
	{
		FEnhancedActionKeyMapping& W = MappingContext->MapKey(MoveAction, EKeys::W);
		W.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(this));

		FEnhancedActionKeyMapping& S = MappingContext->MapKey(MoveAction, EKeys::S);
		S.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(this));
		S.Modifiers.Add(NewObject<UInputModifierNegate>(this));

		FEnhancedActionKeyMapping& A = MappingContext->MapKey(MoveAction, EKeys::A);
		A.Modifiers.Add(NewObject<UInputModifierNegate>(this));

		MappingContext->MapKey(MoveAction, EKeys::D);
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
	MappingContext->MapKey(JumpAction, EKeys::SpaceBar);
	MappingContext->MapKey(FireAction, EKeys::LeftMouseButton);

	// The same keys also feed the double-tap dodge detection.
	MappingContext->MapKey(DodgeForwardAction, EKeys::W);
	MappingContext->MapKey(DodgeBackAction, EKeys::S);
	MappingContext->MapKey(DodgeLeftAction, EKeys::A);
	MappingContext->MapKey(DodgeRightAction, EKeys::D);
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
		Input->BindAction(MenuAction, ETriggerEvent::Started, this, &AIAPlayerController::ReturnToMenu);
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

void AIAPlayerController::ReturnToMenu()
{
	ClientTravel(IAMaps::MenuPath, TRAVEL_Absolute);
}
