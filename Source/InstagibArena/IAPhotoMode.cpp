// Instagib Arena

#include "IAPhotoMode.h"
#include "IAMenuStyle.h"
#include "IAProfileSubsystem.h"
#include "IASettings.h"
#include "InstagibArena.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformTime.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/DateTime.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"

namespace
{
	constexpr float MoveSpeed = 650.f;        // cm per second, Shift x3
	constexpr float LookDegreesPerUnit = 0.12f;
	constexpr float MinFov = 20.f;
	constexpr float MaxFov = 120.f;
}

bool FIAPhotoMode::CanStart(const APlayerController* PC, FText* Reason)
{
	const UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(PC);
	if (!Profile || !Profile->IsUnlocked(FName(TEXT("A3"))))
	{
		if (Reason) { *Reason = INVTEXT("Finish the campaign to unlock"); }
		return false;
	}
	if (!PC || PC->GetNetMode() != NM_Standalone)
	{
		if (Reason) { *Reason = INVTEXT("Offline matches only"); }
		return false;
	}
	if (Reason) { *Reason = INVTEXT("Free camera, the match stays paused"); }
	return true;
}

FIAPhotoMode::FIAPhotoMode(APlayerController* InPC)
	: PC(InPC)
{
	UWorld* World = InPC ? InPC->GetWorld() : nullptr;
	if (!World)
	{
		return;
	}
	StartTime = FPlatformTime::Seconds();

	// The camera starts where the player looks from.
	if (InPC->PlayerCameraManager)
	{
		Location = InPC->PlayerCameraManager->GetCameraLocation();
		Rotation = InPC->PlayerCameraManager->GetCameraRotation();
		Fov = InPC->PlayerCameraManager->GetFOVAngle();
	}
	Rotation.Roll = 0.f;
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (ACameraActor* NewCamera = World->SpawnActor<ACameraActor>(Location, Rotation, Params))
	{
		NewCamera->GetCameraComponent()->SetConstraintAspectRatio(false);
		NewCamera->GetCameraComponent()->SetFieldOfView(Fov);
		Camera = NewCamera;
		OldViewTarget = InPC->GetViewTarget();
		InPC->SetViewTarget(NewCamera);
	}

	if (AHUD* Hud = InPC->GetHUD())
	{
		bHudWasShown = Hud->bShowHUD;
		Hud->bShowHUD = false;
	}

	// The controller sets bShouldPerformFullTickWhenPaused: the paused world still ticks it fully (input, PlayerTick, camera).
	if (!UGameplayStatics::IsGamePaused(InPC))
	{
		bPausedByUs = UGameplayStatics::SetGamePaused(InPC, true);
	}
	InPC->SetIgnoreMoveInput(true);
	InPC->SetIgnoreLookInput(true);
	InPC->SetShowMouseCursor(false);
	InPC->SetInputMode(FInputModeGameOnly());

	// One line of help at the bottom (not in the saved pictures).
	if (UGameViewportClient* Viewport = World->GetGameViewport())
	{
		Hint = SNew(SBox)
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Bottom)
			.Padding(FMargin(0.f, 0.f, 0.f, 28.f))
			.Visibility(EVisibility::HitTestInvisible)
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.55f))
				.Padding(FMargin(18.f, 8.f))
				[
					SNew(STextBlock)
					.Font(IAMenu::Font(15, true))
					.ColorAndOpacity(FLinearColor(0.95f, 0.95f, 0.95f))
					.Text_Lambda([this]()
					{
						if (FPlatformTime::Seconds() < SavedUntil)
						{
							return FText::Format(INVTEXT("SAVED  {0}"), FText::FromString(SavedName));
						}
						return FText::Format(INVTEXT("PHOTO MODE    WASD move    Q / E down / up    Shift faster    Wheel zoom ({0})    P save    Esc back"),
							FText::AsNumber(FMath::RoundToInt(Fov)));
					})
				]
			];
		Viewport->AddViewportWidgetContent(Hint.ToSharedRef(), 30);
	}
	UE_LOG(LogInstagib, Log, TEXT("Photo mode: on at %s"), *Location.ToCompactString());
}

FIAPhotoMode::~FIAPhotoMode()
{
	End();
}

bool FIAPhotoMode::Tick()
{
	APlayerController* Owner = PC.Get();
	ACameraActor* Cam = Camera.Get();
	if (!Owner || !Cam)
	{
		return false;
	}
	const float Dt = FMath::Min(static_cast<float>(FApp::GetDeltaTime()), 0.1f);   // real time: the world is paused

	if (Owner->WasInputKeyJustPressed(EKeys::Escape))
	{
		return false;
	}

	// Look.
	float DX = 0.f, DY = 0.f;
	Owner->GetInputMouseDelta(DX, DY);
	const float Look = LookDegreesPerUnit * IASettings::GetMouseSensitivity() * (Fov / 90.f);
	Rotation.Yaw += DX * Look;
	Rotation.Pitch = FMath::Clamp(Rotation.Pitch + DY * Look, -89.f, 89.f);

	// Move.
	const FRotationMatrix Axes(Rotation);
	FVector Move = FVector::ZeroVector;
	if (Owner->IsInputKeyDown(EKeys::W)) { Move += Axes.GetUnitAxis(EAxis::X); }
	if (Owner->IsInputKeyDown(EKeys::S)) { Move -= Axes.GetUnitAxis(EAxis::X); }
	if (Owner->IsInputKeyDown(EKeys::D)) { Move += Axes.GetUnitAxis(EAxis::Y); }
	if (Owner->IsInputKeyDown(EKeys::A)) { Move -= Axes.GetUnitAxis(EAxis::Y); }
	if (Owner->IsInputKeyDown(EKeys::E)) { Move += FVector::UpVector; }
	if (Owner->IsInputKeyDown(EKeys::Q)) { Move -= FVector::UpVector; }
	const bool bFast = Owner->IsInputKeyDown(EKeys::LeftShift) || Owner->IsInputKeyDown(EKeys::RightShift);
	Location += Move.GetClampedToMaxSize(1.f) * MoveSpeed * (bFast ? 3.f : 1.f) * Dt;

	// Zoom.
	if (Owner->WasInputKeyJustPressed(EKeys::MouseScrollUp)) { Fov = FMath::Max(MinFov, Fov - 5.f); }
	if (Owner->WasInputKeyJustPressed(EKeys::MouseScrollDown)) { Fov = FMath::Min(MaxFov, Fov + 5.f); }

#if !UE_BUILD_SHIPPING
	// -IAPhotoAuto: rise and look down after a second, save a picture after two.
	if (FParse::Param(FCommandLine::Get(), TEXT("IAPhotoAuto")))
	{
		const double Age = FPlatformTime::Seconds() - StartTime;
		if (AutoStep == 0 && Age > 1.0) { AutoStep = 1; Location += FVector(0.f, 0.f, 260.f) - Rotation.Vector() * 300.f; Rotation.Pitch = -22.f; Fov = 75.f; }
		if (AutoStep == 1 && Age > 2.5) { AutoStep = 2; SavePhoto(); }
	}
#endif

	Cam->SetActorLocationAndRotation(Location, Rotation);
	Cam->GetCameraComponent()->SetFieldOfView(Fov);

	if (Owner->WasInputKeyJustPressed(EKeys::P))
	{
		SavePhoto();
	}
	return true;
}

void FIAPhotoMode::SavePhoto()
{
	SavedName = FString::Printf(TEXT("IAPhoto_%s.png"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")));
	const FString Path = FPaths::ConvertRelativePathToFull(FPaths::ScreenShotDir() / TEXT("Photos") / SavedName);
	FScreenshotRequest::RequestScreenshot(Path, /*bShowUI*/ false, /*bAddFilenameSuffix*/ false);
	SavedUntil = FPlatformTime::Seconds() + 2.0;
	UE_LOG(LogInstagib, Log, TEXT("Photo mode: saved %s"), *Path);
}

void FIAPhotoMode::End()
{
	APlayerController* Owner = PC.Get();
	PC.Reset();
	if (Hint.IsValid())
	{
		UWorld* World = Owner ? Owner->GetWorld() : nullptr;
		if (UGameViewportClient* Viewport = World ? World->GetGameViewport() : nullptr)
		{
			Viewport->RemoveViewportWidgetContent(Hint.ToSharedRef());
		}
		Hint.Reset();
	}
	if (Owner)
	{
		if (AHUD* Hud = Owner->GetHUD())
		{
			Hud->bShowHUD = bHudWasShown;
		}
		AActor* Back = OldViewTarget.Get();
		Owner->SetViewTarget(Back ? Back : static_cast<AActor*>(Owner->GetPawn()));
		if (bPausedByUs)
		{
			UGameplayStatics::SetGamePaused(Owner, false);
		}
		Owner->ResetIgnoreMoveInput();
		Owner->ResetIgnoreLookInput();
	}
	if (ACameraActor* Cam = Camera.Get())
	{
		Cam->Destroy();
	}
	Camera.Reset();
	UE_LOG(LogInstagib, Log, TEXT("Photo mode: off"));
}
