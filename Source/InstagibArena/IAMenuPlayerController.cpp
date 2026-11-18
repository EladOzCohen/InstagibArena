// Instagib Arena

#include "IAMenuPlayerController.h"
#include "SIAMainMenu.h"
#include "IAAudioSubsystem.h"
#include "IALoadingScreen.h"
#include "IAMenuStateSubsystem.h"
#include "IAPlayerCharacter.h"
#include "IALoadoutRules.h"
#include "IAProfileSubsystem.h"
#include "Engine/GameInstance.h"
#include "IACharacterRoster.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
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

	// The view comes from a copy of the level's camera that can move (the placed camera is static): a slow drift on
	// the main screens and a move to a close-up on the Character screen.
	if (MenuCamera)
	{
		BaseCameraLocation = MenuCamera->GetActorLocation();
		BaseCameraRotation = MenuCamera->GetActorRotation();
		BaseCameraFov = MenuCamera->GetCameraComponent() ? MenuCamera->GetCameraComponent()->FieldOfView : 90.f;

		FActorSpawnParameters CameraParams;
		CameraParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		MenuCameraActor = GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), BaseCameraLocation, BaseCameraRotation, CameraParams);
		if (MenuCameraActor)
		{
			if (USceneComponent* Root = MenuCameraActor->GetRootComponent())
			{
				Root->SetMobility(EComponentMobility::Movable);
			}
			if (UCameraComponent* Component = MenuCameraActor->GetCameraComponent())
			{
				Component->SetFieldOfView(BaseCameraFov);
				Component->bConstrainAspectRatio = false;
			}
			SetViewTarget(MenuCameraActor);
		}
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

	// After a failed or lost connection the menu opens on the Join screen with the reason.
	FString InitialError;
	if (UIAMenuStateSubsystem* State = GetGameInstance() ? GetGameInstance()->GetSubsystem<UIAMenuStateSubsystem>() : nullptr)
	{
		InitialError = State->ConsumeError();
	}

	Menu = SNew(SIAMainMenu)
		.OwnerController(this)
		.InitialError(InitialError)
		.OnCharacterChanged([this](int32 CharacterIndex) { ShowPreviewCharacter(CharacterIndex); })
		.OnPageChanged([this](int32 PageIndex) { OnMenuPageChanged(PageIndex); });
	Viewport->AddViewportWidgetContent(Menu.ToSharedRef(), 10);

#if !UE_BUILD_SHIPPING
	// Developer check for screenshots: -IAMenuPage=3 opens the Character screen, -IAMenuTab=1 the Join tab.
	int32 TestPage = -1;
	int32 TestTab = 0;
	FParse::Value(FCommandLine::Get(), TEXT("IAMenuTab="), TestTab);
	if (FParse::Value(FCommandLine::Get(), TEXT("IAMenuPage="), TestPage))
	{
		Menu->ShowPageForTest(TestPage, TestTab);
	}

	// Developer check: -IALoadingPreview[ -IALoadingMap=/Game/Maps/DM-Foundry] covers the screen with the loading screen.
	if (FParse::Param(FCommandLine::Get(), TEXT("IALoadingPreview")))
	{
		FString LoadingMap;
		FParse::Value(FCommandLine::Get(), TEXT("IALoadingMap="), LoadingMap);
		Viewport->AddViewportWidgetContent(IALoadingScreen::MakeWidget(LoadingMap), 100);
	}
#endif

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
	PreviewYaw = PreviewBaseYaw;
	ShowPreviewCharacter(0);

	// The preview wears the player's saved loadout (colour variant, rifle) with the lifetime kills on the counter.
	const UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(this);
	FIACosmeticLoadout Loadout = Profile ? Profile->GetLoadout() : FIACosmeticLoadout();
	IALoadout::RemoveLocked(Loadout, Profile);
	SetPreviewLoadout(Loadout);
}

void AIAMenuPlayerController::SetPreviewLoadout(const FIACosmeticLoadout& Loadout)
{
	if (Preview)
	{
		FIACosmeticLoadout Shown = Loadout;
		Shown.KillCounterValue = IALoadout::LifetimeKills(UIAProfileSubsystem::Get(this));
		Preview->SetForcedLoadout(Shown);
	}
}

void AIAMenuPlayerController::SetGunsmithView(bool bOn)
{
	GunsmithTarget = bOn ? 1.f : 0.f;
	DriftHold = 0.4f;
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

	// A slow sway, so that the accessories can be seen from a little to each side. In the Gunsmith the character turns its right side
	// (and the rifle) to the camera, as far as the player turns it, and only breathes a little.
	GunsmithBlend = FMath::FInterpConstantTo(GunsmithBlend, GunsmithTarget, DeltaSeconds, 1.f / 0.8f);
	if (Preview)
	{
		const float Time = GetWorld()->GetTimeSeconds();
		const float Sway = FMath::Sin(Time * 0.7f) * 32.f;
		const float GunsmithYaw = -90.f + GunsmithTurn + FMath::Sin(Time * 0.5f) * 6.f;
		const float Ease = GunsmithBlend * GunsmithBlend * (3.f - 2.f * GunsmithBlend);
		const float TargetYaw = PreviewBaseYaw + FMath::Lerp(Sway, GunsmithYaw, Ease);
		PreviewYaw = GunsmithBlend > 0.f ? FMath::FInterpTo(PreviewYaw, TargetYaw, DeltaSeconds, 6.f) : TargetYaw;
		Preview->SetActorLocationAndRotation(PreviewLocation, FRotator(0.f, PreviewYaw, 0.f));
	}

	UpdateMenuCamera(DeltaSeconds);
}

void AIAMenuPlayerController::OnMenuPageChanged(int32 PageIndex)
{
	// The Character screen (3) gets the close-up. The drift stays quiet for a moment while the camera moves.
	CloseUpTarget = (PageIndex == 3) ? 1.f : 0.f;
	DriftHold = 0.4f;
}

void AIAMenuPlayerController::UpdateMenuCamera(float DeltaSeconds)
{
	ACameraActor* Camera = MenuCameraActor;
	if (!Camera)
	{
		return;
	}
	const float Dt = FMath::Clamp(DeltaSeconds, 0.f, 0.1f);

	CloseUp = FMath::FInterpConstantTo(CloseUp, CloseUpTarget, Dt, 1.f / 0.9f);
	DriftHold = FMath::Max(0.f, DriftHold - Dt);
	const bool bMoving = !FMath::IsNearlyEqual(CloseUp, CloseUpTarget) || DriftHold > 0.f;
	DriftWeight = FMath::FInterpTo(DriftWeight, bMoving ? 0.f : 1.f, Dt, bMoving ? 4.f : 0.6f);
	DriftTime += Dt;
	const float Ease = CloseUp * CloseUp * (3.f - 2.f * CloseUp);

	// The close-up: nearer to the character, a narrower lens, the character a little right of the middle (clear of the panel).
	const FVector FromPreview = BaseCameraLocation - PreviewLocation;
	FVector CloseLocation = PreviewLocation + FVector(FromPreview.X, FromPreview.Y, 0.f) * 0.92f;
	CloseLocation.Z = PreviewLocation.Z + 34.f;
	const float CloseFov = 66.f;
	const FVector ToPreview = PreviewLocation - CloseLocation;
	const float Flat = FMath::Max(1.f, FVector2D(ToPreview.X, ToPreview.Y).Size());
	const float CharacterAngle = FMath::RadiansToDegrees(FMath::Atan2(ToPreview.Y, ToPreview.X));
	const float AngleFromCentre = FMath::RadiansToDegrees(FMath::Atan(0.40f * FMath::Tan(FMath::DegreesToRadians(CloseFov * 0.5f))));
	const float CloseYaw = CharacterAngle - AngleFromCentre;
	const float ClosePitch = FMath::RadiansToDegrees(FMath::Atan2(PreviewLocation.Z + 4.f - CloseLocation.Z, Flat));

	FVector Location = FMath::Lerp(BaseCameraLocation, CloseLocation, Ease);
	FRotator Rotation(
		BaseCameraRotation.Pitch + FMath::FindDeltaAngleDegrees(BaseCameraRotation.Pitch, ClosePitch) * Ease,
		BaseCameraRotation.Yaw + FMath::FindDeltaAngleDegrees(BaseCameraRotation.Yaw, CloseYaw) * Ease,
		0.f);
	float Fov = FMath::Lerp(BaseCameraFov, CloseFov, Ease);

	// The Gunsmith: a close-up of the rifle in the character's hands, the rifle right of the middle (clear of the wider panel).
	FVector RifleCentre;
	FRotator RifleRotation;
	if (Preview && Preview->GetRifleViewPoint(RifleCentre, RifleRotation))
	{
		RifleFocus = bHaveRifleFocus ? FMath::VInterpTo(RifleFocus, RifleCentre, Dt, 5.f) : RifleCentre;
		bHaveRifleFocus = true;
	}
	float GunEase = 0.f;
	if (GunsmithBlend > 0.f && bHaveRifleFocus)
	{
		const float G = GunsmithBlend * GunsmithBlend * (3.f - 2.f * GunsmithBlend);
		GunEase = G;
		const FVector Away = FVector(BaseCameraLocation.X - PreviewLocation.X, BaseCameraLocation.Y - PreviewLocation.Y, 0.f).GetSafeNormal();
		const FVector GunLocation = RifleFocus + Away * 92.f + FVector(0.f, 0.f, 14.f);
		const float GunFov = 52.f;
		const FVector ToRifle = RifleFocus - GunLocation;
		const float GunFlat = FMath::Max(1.f, FVector2D(ToRifle.X, ToRifle.Y).Size());
		const float GunOffAngle = FMath::RadiansToDegrees(FMath::Atan(0.42f * FMath::Tan(FMath::DegreesToRadians(GunFov * 0.5f))));
		const float GunYaw = FMath::RadiansToDegrees(FMath::Atan2(ToRifle.Y, ToRifle.X)) - GunOffAngle;
		const float GunPitch = FMath::RadiansToDegrees(FMath::Atan2(ToRifle.Z, GunFlat));
		Location = FMath::Lerp(Location, GunLocation, G);
		Rotation.Pitch += FMath::FindDeltaAngleDegrees(Rotation.Pitch, GunPitch) * G;
		Rotation.Yaw += FMath::FindDeltaAngleDegrees(Rotation.Yaw, GunYaw) * G;
		Fov = FMath::Lerp(Fov, GunFov, G);
	}

	// The drift: a few degrees of yaw, a breath of pitch, a little sideways and up-down movement. Calm on purpose.
	const float Weight = DriftWeight * (1.f - 0.7f * Ease) * (1.f - 0.9f * GunEase);
	const float T = DriftTime;
	Rotation.Yaw += (1.5f * FMath::Sin(T * 0.21f) + 0.5f * FMath::Sin(T * 0.53f + 1.3f)) * Weight;
	Rotation.Pitch += 0.35f * FMath::Sin(T * 0.29f + 0.7f) * Weight;
	const FVector Right = FRotationMatrix(Rotation).GetScaledAxis(EAxis::Y);
	Location += Right * (10.f * FMath::Sin(T * 0.17f + 2.f) * Weight) + FVector(0.f, 0.f, 2.5f * FMath::Sin(T * 0.37f) * Weight);

	Camera->SetActorLocationAndRotation(Location, Rotation);
	if (UCameraComponent* Component = Camera->GetCameraComponent())
	{
		Component->SetFieldOfView(Fov);
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
	if (MenuCameraActor)
	{
		MenuCameraActor->Destroy();
		MenuCameraActor = nullptr;
	}

	Super::EndPlay(EndPlayReason);
}
