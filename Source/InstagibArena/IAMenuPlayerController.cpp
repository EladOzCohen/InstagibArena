// Instagib Arena

#include "IAMenuPlayerController.h"
#include "SIAMainMenu.h"
#include "IAAudioSubsystem.h"
#include "IAPlayerCharacter.h"
#include "IACharacterRoster.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Camera/CameraActor.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Widgets/SWeakWidget.h"

AIAMenuPlayerController::AIAMenuPlayerController()
{
	PrimaryActorTick.bCanEverTick = true;
}

void AIAMenuPlayerController::BeginPlay()
{
	Super::BeginPlay();

	if (!IsLocalController())
	{
		return;
	}

	// Use the first camera placed in the menu level as the backdrop view.
	const ACameraActor* MenuCamera = nullptr;
	for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It)
	{
		MenuCamera = *It;
		SetViewTarget(*It);
		break;
	}

	UGameViewportClient* Viewport = GetWorld()->GetGameViewport();
	if (!Viewport)
	{
		return;
	}

	if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(this))
	{
		Audio->PlayMusic(EIAMusic::Menu);
	}

	SpawnPreview(MenuCamera);

	Menu = SNew(SIAMainMenu)
		.OwnerController(this)
		.OnCharacterChanged([this](int32 CharacterIndex) { ShowPreviewCharacter(CharacterIndex); });
	Viewport->AddViewportWidgetContent(Menu.ToSharedRef(), 10);

	SetShowMouseCursor(true);
	FInputModeUIOnly InputMode;
	InputMode.SetWidgetToFocus(Menu);
	InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	SetInputMode(InputMode);
}

void AIAMenuPlayerController::SpawnPreview(const ACameraActor* Camera)
{
	if (!Camera)
	{
		return;
	}

	// On the stage, to the right of the menu panel as seen from the menu camera, facing the camera.
	const FVector CameraLocation = Camera->GetActorLocation();
	const FRotator FlatRotation(0.f, Camera->GetActorRotation().Yaw, 0.f);
	const FVector Forward = FlatRotation.Vector();
	const FVector Right = FRotator(0.f, FlatRotation.Yaw + 90.f, 0.f).Vector();

	PreviewLocation = CameraLocation + Forward * 430.f + Right * 190.f;
	PreviewLocation.Z = 96.f; // the stage floor is at height 0
	PreviewBaseYaw = (CameraLocation - PreviewLocation).Rotation().Yaw;

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Preview = GetWorld()->SpawnActor<AIAPlayerCharacter>(AIAPlayerCharacter::StaticClass(), PreviewLocation, FRotator(0.f, PreviewBaseYaw, 0.f), Params);
	ShowPreviewCharacter(0);
}

void AIAMenuPlayerController::ShowPreviewCharacter(int32 CharacterIndex)
{
	if (Preview)
	{
		Preview->SetForcedLook(CharacterIndex);
	}
}

void AIAMenuPlayerController::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

#if !UE_BUILD_SHIPPING
	// Developer check: -IAPreviewCycle steps through all characters, one every 1.2 seconds.
	static const bool bCycle = FParse::Param(FCommandLine::Get(), TEXT("IAPreviewCycle"));
	if (bCycle && Preview)
	{
		CycleTimer += DeltaSeconds;
		if (CycleTimer >= 1.2f)
		{
			CycleTimer = 0.f;
			CycleIndex = (CycleIndex + 1) % IACharacters::LookCount;
			ShowPreviewCharacter(CycleIndex);
		}
	}
#endif

	// A slow sway, so that the accessories can be seen from a little to each side.
	if (Preview)
	{
		const float Time = GetWorld()->GetTimeSeconds();
		Preview->SetActorLocationAndRotation(PreviewLocation, FRotator(0.f, PreviewBaseYaw + FMath::Sin(Time * 0.7f) * 32.f, 0.f));
	}
}

void AIAMenuPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Menu.IsValid())
	{
		if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
		{
			Viewport->RemoveViewportWidgetContent(Menu.ToSharedRef());
		}
		Menu.Reset();
	}

	if (Preview)
	{
		Preview->Destroy();
		Preview = nullptr;
	}

	Super::EndPlay(EndPlayReason);
}
