// Instagib Arena

#include "IADevSubsystem.h"
#include "IACharacterRoster.h"
#include "IAPlayerCharacter.h"
#include "IAPlayerController.h"
#include "IAGameState.h"
#include "IAHUD.h"
#include "IAImpactEffect.h"
#include "IAPlayerState.h"
#include "InstagibArena.h"
#include "EngineUtils.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/StaticMeshActor.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerStart.h"
#include "Containers/Ticker.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

void UIADevSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

#if !UE_BUILD_SHIPPING
	// Multiplayer test helpers, independent of the screenshot options below.
	if (FParse::Param(FCommandLine::Get(), TEXT("IAReport")))
	{
		ReportHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &UIADevSubsystem::Report), 4.f);
	}
	if (FParse::Param(FCommandLine::Get(), TEXT("IAWalk")))
	{
		WalkHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &UIADevSubsystem::Walk), 0.f);
	}
	float FireEvery = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("IAFireEvery="), FireEvery) && FireEvery > 0.f)
	{
		AutoFireHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &UIADevSubsystem::AutoFire), FireEvery);
	}

	// MENUS: -IAPauseAt=20 opens the pause menu 20 seconds after start (use -IAPauseScript to drive it).
	float PauseAt = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("IAPauseAt="), PauseAt) && PauseAt > 0.f)
	{
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([this](float)
		{
			UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
			if (World)
			{
				if (AIAPlayerController* PC = Cast<AIAPlayerController>(UGameplayStatics::GetPlayerController(World, 0)))
				{
					PC->OpenPause();
				}
			}
			return false;
		}), PauseAt);
	}

	float Delay = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("IAShotDelay="), Delay) && Delay > 0.f)
	{
		UE_LOG(LogInstagib, Log, TEXT("DevSubsystem: screenshot in %.0f s, then quit"), Delay);

		FParse::Value(FCommandLine::Get(), TEXT("IAShotName="), ShotName);

		if (FParse::Param(FCommandLine::Get(), TEXT("IAFire")))
		{
			FireHandle = FTSTicker::GetCoreTicker().AddTicker(
				FTickerDelegate::CreateUObject(this, &UIADevSubsystem::FireRifle), FMath::Max(0.5f, Delay - 0.12f));
		}

		if (FParse::Param(FCommandLine::Get(), TEXT("IAPause")))
		{
			// Opens the pause menu half a second before the screenshot.
			PauseHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([this](float)
			{
				UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
				if (World)
				{
					if (AIAPlayerController* PC = Cast<AIAPlayerController>(UGameplayStatics::GetPlayerController(World, 0)))
					{
						PC->OpenPause();
					}
				}
				return false;
			}), FMath::Max(0.5f, Delay - 1.f));
		}

		FString ImpactText;
		if (FParse::Value(FCommandLine::Get(), TEXT("IAImpact="), ImpactText, /*bShouldStopOnSeparator*/ false))
		{
			TArray<FString> Parts;
			ImpactText.ParseIntoArray(Parts, TEXT(","));
			if (Parts.Num() == 3)
			{
				ImpactLocation = FVector(FCString::Atof(*Parts[0]), FCString::Atof(*Parts[1]), FCString::Atof(*Parts[2]));
				ImpactHandle = FTSTicker::GetCoreTicker().AddTicker(
					FTickerDelegate::CreateUObject(this, &UIADevSubsystem::ImpactDemo), FMath::Max(0.5f, Delay - 0.18f));
			}
		}

		FString ShowroomText;
		if (FParse::Value(FCommandLine::Get(), TEXT("IAShowroom="), ShowroomText, /*bShouldStopOnSeparator*/ false))
		{
			TArray<FString> Parts;
			ShowroomText.ParseIntoArray(Parts, TEXT(","));
			if (Parts.Num() == 4)
			{
				ShowroomLocation = FVector(FCString::Atof(*Parts[0]), FCString::Atof(*Parts[1]), FCString::Atof(*Parts[2]));
				ShowroomYaw = FCString::Atof(*Parts[3]);
				ShowroomHandle = FTSTicker::GetCoreTicker().AddTicker(
					FTickerDelegate::CreateUObject(this, &UIADevSubsystem::SpawnShowroom), FMath::Max(0.5f, Delay - 6.f));
			}
		}

		FString CameraText;
		if (FParse::Value(FCommandLine::Get(), TEXT("IAShotCam="), CameraText, /*bShouldStopOnSeparator*/ false))
		{
			TArray<FString> Parts;
			CameraText.ParseIntoArray(Parts, TEXT(","));
			if (Parts.Num() == 5)
			{
				CameraLocation = FVector(FCString::Atof(*Parts[0]), FCString::Atof(*Parts[1]), FCString::Atof(*Parts[2]));
				CameraRotation = FRotator(FCString::Atof(*Parts[3]), FCString::Atof(*Parts[4]), 0.f);
				CameraHandle = FTSTicker::GetCoreTicker().AddTicker(
					FTickerDelegate::CreateUObject(this, &UIADevSubsystem::PlaceCamera), 0.25f);
			}
		}

		if (FParse::Param(FCommandLine::Get(), TEXT("IAShotAuto")))
		{
			bAutoShot = true;
			AutoShotHandle = FTSTicker::GetCoreTicker().AddTicker(
				FTickerDelegate::CreateUObject(this, &UIADevSubsystem::AutoShotCamera), 0.25f);
		}

		ShotHandle = FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateUObject(this, &UIADevSubsystem::TakeScreenshot), Delay);
	}
#endif
}

void UIADevSubsystem::Deinitialize()
{
	FTSTicker::GetCoreTicker().RemoveTicker(PauseHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(ImpactHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(ReportHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(WalkHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(AutoFireHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(FireHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(ShowroomHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(CameraHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(AutoShotHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(ShotHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(QuitHandle);
	Super::Deinitialize();
}

bool UIADevSubsystem::ImpactDemo(float DeltaTime)
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!World)
	{
		return false;
	}

	// A wall hit, a player hit and a player being destroyed, side by side.
	const float Scales[3] = { 1.f, 1.4f, 2.2f };
	const int32 Sparks[3] = { 12, 24, 44 };
	const FLinearColor Colors[3] = { FLinearColor(0.f, 0.9f, 1.f), FLinearColor(1.f, 0.4f, 0.f), FLinearColor(0.9f, 0.05f, 0.05f) };
	for (int32 I = 0; I < 3; ++I)
	{
		if (AIAImpactEffect* Effect = World->SpawnActor<AIAImpactEffect>(ImpactLocation + FVector(0.f, (I - 1) * 140.f, 0.f), FRotator::ZeroRotator))
		{
			Effect->Init(FVector::UpVector, Colors[I], Scales[I], Sparks[I]);
		}
	}

	if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
	{
		if (AIAHUD* Hud = Cast<AIAHUD>(PC->GetHUD()))
		{
			Hud->ShowHitMarker(true);
			Hud->AddMessage(TEXT("You fragged Vesper"), FLinearColor(1.f, 0.85f, 0.2f), 2.f);
			Hud->AddMessage(TEXT("Fragged by Cinder"), FLinearColor(1.f, 0.25f, 0.2f), 2.f);
		}
	}
	return false;
}

bool UIADevSubsystem::Report(float DeltaTime)
{
	// One line describing what this machine sees, so that host and client logs can be compared.
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!World)
	{
		return true;
	}

	const TCHAR* Net = TEXT("?");
	switch (World->GetNetMode())
	{
	case NM_Standalone:       Net = TEXT("standalone"); break;
	case NM_ListenServer:     Net = TEXT("listen-server"); break;
	case NM_Client:           Net = TEXT("client"); break;
	case NM_DedicatedServer:  Net = TEXT("dedicated"); break;
	default: break;
	}

	FString Players;
	int32 Count = 0;
	int32 Clock = -1;
	int32 Red = 0, Blue = 0;
	bool bOver = false;
	if (const AIAGameState* GS = World->GetGameState<AIAGameState>())
	{
		Clock = GS->ClockSeconds;
		Red = GS->RedScore;
		Blue = GS->BlueScore;
		bOver = GS->bMatchOver;
		for (APlayerState* PS : GS->PlayerArray)
		{
			if (const AIAPlayerState* S = Cast<AIAPlayerState>(PS))
			{
				Players += FString::Printf(TEXT("%s[k%d d%d t%d c%d%s] "), *S->GetPlayerName(), S->Kills, S->Deaths,
					static_cast<int32>(S->Team), S->CharacterIndex, S->bIsBotPlayer ? TEXT(" bot") : TEXT(""));
				++Count;
			}
		}
	}

	// Where every human's pawn is, as seen by this machine (bots are left out to keep the line short).
	int32 Pawns = 0;
	FString Humans;
	for (TActorIterator<AIAPlayerCharacter> It(World); It; ++It)
	{
		++Pawns;
		const AIAPlayerState* S = It->GetPlayerState<AIAPlayerState>();
		if (S && !S->bIsBotPlayer)
		{
			Humans += FString::Printf(TEXT("%s@(%.0f,%.0f,%.0f) "), *S->GetPlayerName().Right(4), It->GetActorLocation().X, It->GetActorLocation().Y, It->GetActorLocation().Z);
		}
	}

	FString Local = TEXT("none");
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
	{
		if (const APawn* Pawn = PC->GetPawn())
		{
			Local = Pawn->GetActorLocation().ToCompactString();
		}
	}

	UE_LOG(LogInstagib, Log, TEXT("REPORT %s clock=%d red=%d blue=%d over=%d players=%d pawns=%d local=%s :: %s"),
		Net, Clock, Red, Blue, bOver ? 1 : 0, Count, Pawns, *Local, *Players);
	UE_LOG(LogInstagib, Log, TEXT("HUMANS %s clock=%d %s"), Net, Clock, *Humans);
	return true;
}

bool UIADevSubsystem::Walk(float DeltaTime)
{
	// Walks the local player forward and turns slowly, so that movement replication has something to show.
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (World)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
		{
			if (AIAPlayerCharacter* Pawn = Cast<AIAPlayerCharacter>(PC->GetPawn()))
			{
				if (!Pawn->IsDead())
				{
					Pawn->AddMovementInput(Pawn->GetActorForwardVector(), 1.f);
					Pawn->AddControllerYawInput(0.35f);
				}
			}
		}
	}
	return true;
}

bool UIADevSubsystem::AutoFire(float DeltaTime)
{
	FireRifle(DeltaTime);
	return true;
}

bool UIADevSubsystem::FireRifle(float DeltaTime)
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (World)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
		{
			if (AIAPlayerCharacter* Pawn = Cast<AIAPlayerCharacter>(PC->GetPawn()))
			{
				Pawn->TryFire();
			}
		}
	}
	return false;
}

bool UIADevSubsystem::SpawnShowroom(float DeltaTime)
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!World)
	{
		return false;
	}

	// Five characters side by side, each standing in its idle pose. -IAShowroomFrom=5 shows characters 5 to 9.
	int32 First = 0;
	FParse::Value(FCommandLine::Get(), TEXT("IAShowroomFrom="), First);
	const FVector Right = FRotator(0.f, ShowroomYaw + 90.f, 0.f).Vector();
	for (int32 I = 0; I < 5; ++I)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FVector Location = ShowroomLocation + Right * ((I - 2) * 130.f);
		if (AIAPlayerCharacter* Pawn = World->SpawnActor<AIAPlayerCharacter>(AIAPlayerCharacter::StaticClass(), Location, FRotator(0.f, ShowroomYaw, 0.f), Params))
		{
			Pawn->SetForcedLook((First + I) % IACharacters::LookCount);
		}
	}
	return false;
}

bool UIADevSubsystem::PlaceCamera(float DeltaTime)
{
	// Runs every quarter second until the screenshot: a respawn gives the view back to the player's pawn.
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (World)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
		{
			if (!Camera.IsValid())
			{
				Camera = World->SpawnActor<ACameraActor>(CameraLocation, CameraRotation);
			}
			if (Camera.IsValid() && PC->GetViewTarget() != Camera.Get())
			{
				PC->SetViewTarget(Camera.Get());
			}
		}
	}
	return true;
}

bool UIADevSubsystem::AutoShotCamera(float DeltaTime)
{
	// Runs every quarter second until the screenshot: a respawn gives the view back to the player's pawn.
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	APlayerController* PC = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
	if (!World || !PC)
	{
		return true;
	}

	if (!AutoCamera.IsValid())
	{
		// Bounds of everything solid that the level is made of.
		FBox Bounds(ForceInit);
		int32 MeshCount = 0;
		for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
		{
			const FBox Box = It->GetComponentsBoundingBox();
			if (Box.IsValid)
			{
				Bounds += Box;
				++MeshCount;
			}
		}
		int32 Starts = 0;
		for (TActorIterator<APlayerStart> It(World); It; ++It)
		{
			++Starts;
		}
		if (!Bounds.IsValid)
		{
			return true;
		}

		const FVector Center = Bounds.GetCenter();
		const FVector Extent = Bounds.GetExtent();
		const float Radius = Extent.Size();
		const float Fov = 80.f;
		const FVector Direction = FVector(-0.60f, -0.60f, 0.52f).GetSafeNormal();
		const float Distance = Radius / FMath::Tan(FMath::DegreesToRadians(Fov * 0.5f)) * 0.78f;
		FVector Location = Center + Direction * Distance;

		// A closed hall: stop in front of the wall and look from inside.
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(IAShotAuto), false);
		bool bInside = false;
		if (World->LineTraceSingleByChannel(Hit, Center, Location, ECC_Visibility, Params))
		{
			Location = Hit.ImpactPoint - Direction * 60.f;
			bInside = true;
		}

		const FRotator Rotation = (Center - Location).Rotation();
		ACameraActor* NewCamera = World->SpawnActor<ACameraActor>(Location, Rotation);
		if (NewCamera)
		{
			NewCamera->GetCameraComponent()->SetFieldOfView(bInside ? 100.f : Fov);
			AutoCamera = NewCamera;
		}
		UE_LOG(LogInstagib, Log, TEXT("THUMB_INFO map=%s starts=%d meshes=%d size=%.0f,%.0f,%.0f inside=%d camera=%s"),
			*World->GetMapName(), Starts, MeshCount, Extent.X * 2.f, Extent.Y * 2.f, Extent.Z * 2.f, bInside ? 1 : 0, *Location.ToCompactString());
	}

	if (AutoCamera.IsValid() && PC->GetViewTarget() != AutoCamera.Get())
	{
		PC->SetViewTarget(AutoCamera.Get());
	}
	if (APawn* Pawn = PC->GetPawn())
	{
		Pawn->SetActorHiddenInGame(true);
	}
	if (AHUD* Hud = PC->GetHUD())
	{
		Hud->bShowHUD = false;
	}
	return true;
}

bool UIADevSubsystem::TakeScreenshot(float DeltaTime)
{
	const FString Path = FPaths::ProjectSavedDir() / TEXT("IAShots") / (ShotName + TEXT(".png"));
	FScreenshotRequest::RequestScreenshot(FPaths::ConvertRelativePathToFull(Path), /*bShowUI*/ !bAutoShot, /*bAddFilenameSuffix*/ false);
	UE_LOG(LogInstagib, Log, TEXT("DevSubsystem: screenshot requested -> %s"), *Path);

	QuitHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([](float)
	{
		FPlatformMisc::RequestExit(false);
		return false;
	}), 4.f);

	return false; // run once
}
