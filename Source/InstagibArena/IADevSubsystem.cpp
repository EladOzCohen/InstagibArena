// Instagib Arena

#include "IADevSubsystem.h"
#include "IACharacterRoster.h"
#include "IAAnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
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

	if (FParse::Param(FCommandLine::Get(), TEXT("IAReport")))
	{
		FrameStatHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([this](float Dt)
		{
			FrameTimeMax = FMath::Max(FrameTimeMax, Dt);
			FrameTimeSum += Dt;
			++FrameTimeCount;
			if (Dt > 0.1f)
			{
				++FrameHitches;
			}
			return true;
		}), 0.f);
	}
	if (FParse::Param(FCommandLine::Get(), TEXT("IAMoveTest")))
	{
		MoveTestHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &UIADevSubsystem::MoveTest), 0.f);
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
	FTSTicker::GetCoreTicker().RemoveTicker(FrameStatHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(MoveTestHandle);
	FTSTicker::GetCoreTicker().RemoveTicker(ShowroomWalkHandle);
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
	UE_LOG(LogInstagib, Log, TEXT("FRAMES %s clock=%d avg=%.1f ms max=%.1f ms over100ms=%d (frames=%d)"), Net, Clock,
		FrameTimeCount > 0 ? FrameTimeSum / FrameTimeCount * 1000.f : 0.f, FrameTimeMax * 1000.f, FrameHitches, FrameTimeCount);
	FrameTimeMax = 0.f;
	FrameTimeSum = 0.f;
	FrameTimeCount = 0;
	FrameHitches = 0;
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
			ShowroomPawns.Add(Pawn);
			ShowroomHome.Add(Location);
			if (FParse::Param(FCommandLine::Get(), TEXT("IAShowroomWalk")))
			{
				Pawn->GetCharacterMovement()->bRunPhysicsWithNoController = true;
				Pawn->GetCharacterMovement()->SetDefaultMovementMode(); // pawns that nobody possesses start without movement
				Pawn->DevAimPitch = (I - 2) * 22.f; // looking down ... up across the row
				if (FParse::Param(FCommandLine::Get(), TEXT("IAShowroomCrouch")) && I == 4)
				{
					Pawn->Crouch();
				}
			}
		}
	}
	if (FParse::Param(FCommandLine::Get(), TEXT("IAShowroomWalk")))
	{
		ShowroomWalkHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &UIADevSubsystem::ShowroomWalk), 0.f);
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
		FCollisionQueryParams Params(SCENE_QUERY_STAT(IAShotAuto), false);

		// The playable area: where the player starts are, with some margin. Scenery far outside it (skyline towers,
		// mountains, giant floors) is cut off at the edge of this region so that it does not shrink the picture.
		FBox StartBox(ForceInit);
		int32 Starts = 0;
		int32 Covered = 0;
		for (TActorIterator<APlayerStart> It(World); It; ++It)
		{
			++Starts;
			StartBox += It->GetActorLocation();
			// Is there a ceiling over this start? Then the level is a closed hall.
			FHitResult UpHit;
			if (World->LineTraceSingleByChannel(UpHit, It->GetActorLocation() + FVector(0.f, 0.f, 150.f),
				It->GetActorLocation() + FVector(0.f, 0.f, 9000.f), ECC_Visibility, Params))
			{
				++Covered;
			}
		}
		const bool bClosed = Starts > 0 && Covered * 10 >= Starts * 7;

		FBox Region(ForceInit);
		if (StartBox.IsValid)
		{
			Region = StartBox.ExpandBy(FVector(1200.f, 1200.f, 0.f));
			Region.Min.Z -= 300.f;
			Region.Max.Z += 900.f;
		}

		FBox Bounds(ForceInit);
		int32 MeshCount = 0;
		for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
		{
			FBox Box = It->GetComponentsBoundingBox();
			if (!Box.IsValid)
			{
				continue;
			}
			if (Region.IsValid)
			{
				if (!Box.Intersect(Region))
				{
					continue;
				}
				Box = FBox(Box.Min.ComponentMax(Region.Min), Box.Max.ComponentMin(Region.Max));
			}
			Bounds += Box;
			++MeshCount;
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

		// A closed hall: stop in front of the wall and look from inside. Open levels are seen from outside, from above.
		bool bInside = false;
		if (bClosed)
		{
			FHitResult Hit;
			if (World->LineTraceSingleByChannel(Hit, Center, Location, ECC_Visibility, Params))
			{
				Location = Hit.ImpactPoint - Direction * 60.f;
				bInside = true;
			}
		}

		const FRotator Rotation = (Center - Location).Rotation();
		ACameraActor* NewCamera = World->SpawnActor<ACameraActor>(Location, Rotation);
		if (NewCamera)
		{
			UCameraComponent* CameraComponent = NewCamera->GetCameraComponent();
			CameraComponent->SetFieldOfView(bInside ? 100.f : Fov);
			if (bInside)
			{
				// Dark halls: brighten the picture a little.
				CameraComponent->PostProcessSettings.bOverride_AutoExposureBias = true;
				CameraComponent->PostProcessSettings.AutoExposureBias = 1.2f;
			}
			AutoCamera = NewCamera;
		}
		UE_LOG(LogInstagib, Log, TEXT("THUMB_INFO map=%s starts=%d meshes=%d size=%.0f,%.0f,%.0f inside=%d closed=%d camera=%s"),
			*World->GetMapName(), Starts, MeshCount, Extent.X * 2.f, Extent.Y * 2.f, Extent.Z * 2.f, bInside ? 1 : 0, bClosed ? 1 : 0, *Location.ToCompactString());
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

// ---------------------------------------------------------------- FEEL: movement test and showroom walk

bool UIADevSubsystem::MoveTest(float DeltaTime)
{
	// Scripted run through every kind of movement. Logs "MOVETEST" lines with positions, so that the logs of a
	// listen server and a client can be compared, and so that the effect of each step can be read.
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!World)
	{
		return true;
	}
	APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
	AIAPlayerCharacter* Pawn = PC ? Cast<AIAPlayerCharacter>(PC->GetPawn()) : nullptr;
	if (!Pawn || Pawn->IsDead())
	{
		MoveTestStepTime = 0.f;
		return true;
	}
	UIACharacterMovement* Move = Cast<UIACharacterMovement>(Pawn->GetCharacterMovement());
	if (!Move)
	{
		return true;
	}

	struct FStep { const TCHAR* Name; float Duration; };
	static const FStep Steps[] = {
		{ TEXT("settle"), 2.0f },     { TEXT("jump"), 1.4f },       { TEXT("doublejump"), 1.8f },
		{ TEXT("run"), 1.3f },        { TEXT("dodgeLeft"), 1.3f },  { TEXT("dodgeRight"), 1.3f },
		{ TEXT("dodgeFwd"), 1.3f },   { TEXT("dodgeBack"), 1.3f },  { TEXT("crouch"), 1.2f },
		{ TEXT("crouchwalk"), 1.4f }, { TEXT("slowwalk"), 1.4f },   { TEXT("findwall"), 0.4f },
		{ TEXT("wallrun"), 3.5f },    { TEXT("end"), 3.0f }
	};
	constexpr int32 StepCount = UE_ARRAY_COUNT(Steps);

	if (MoveTestStep < 0)
	{
		MoveTestStep = 0;
		MoveTestStepTime = 0.f;
		UE_LOG(LogInstagib, Log, TEXT("MOVETEST start (net mode %d)"), static_cast<int32>(World->GetNetMode()));
	}

	const bool bFirstFrame = MoveTestStepTime == 0.f;
	MoveTestStepTime += DeltaTime;
	MoveTestLogTimer += DeltaTime;
	const float T = MoveTestStepTime;
	const FVector Forward = Pawn->GetActorForwardVector();

	// One-time actions at the start of a step, or at a moment inside it.
	switch (MoveTestStep)
	{
	case 1: if (bFirstFrame) { Pawn->Jump(); } break;
	case 2:
		if (bFirstFrame) { Pawn->Jump(); }
		if (T > 0.1f && T - DeltaTime <= 0.1f) { Pawn->StopJumping(); }
		if (T > 0.45f && !bMoveTestJumped) { bMoveTestJumped = true; Pawn->Jump(); }
		break;
	case 4: if (bFirstFrame) { Pawn->Dodge(EIADodgeDir::Left); } break;
	case 5: if (bFirstFrame) { Pawn->Dodge(EIADodgeDir::Right); } break;
	case 6: if (bFirstFrame) { Pawn->Dodge(EIADodgeDir::Forward); } break;
	case 7: if (bFirstFrame) { Pawn->Dodge(EIADodgeDir::Back); } break;
	case 8:
		if (bFirstFrame) { Pawn->Crouch(); }
		if (T > 0.8f) { Pawn->UnCrouch(); }
		break;
	case 9: if (bFirstFrame) { Pawn->Crouch(); } break;
	case 10: if (bFirstFrame) { Pawn->UnCrouch(); Move->SetWantsToWalk(true); } break;
	case 11:
		if (bFirstFrame)
		{
			Move->SetWantsToWalk(false);
			// Face the nearest wall.
			float BestDistance = 1.0e9f;
			float BestYaw = Pawn->GetActorRotation().Yaw;
			FCollisionQueryParams Params(SCENE_QUERY_STAT(IAMoveTestWall), false, Pawn);
			for (int32 I = 0; I < 12; ++I)
			{
				const FVector Dir = FRotator(0.f, I * 30.f, 0.f).Vector();
				FHitResult Hit;
				if (World->LineTraceSingleByChannel(Hit, Pawn->GetActorLocation(), Pawn->GetActorLocation() + Dir * 900.f, ECC_WorldStatic, Params)
					&& FMath::Abs(Hit.ImpactNormal.Z) < 0.3f && Hit.Distance < BestDistance)
				{
					BestDistance = Hit.Distance;
					BestYaw = I * 30.f;
				}
			}
			PC->SetControlRotation(FRotator(0.f, BestYaw, 0.f));
			bMoveTestJumped = false;
			bMoveTestDodged = false;
			UE_LOG(LogInstagib, Log, TEXT("MOVETEST wall: nearest %.0f units away at yaw %.0f"), BestDistance, BestYaw);
		}
		break;
	default: break;
	}

	// Steady input while a step runs.
	const bool bWalkInput = MoveTestStep == 3 || MoveTestStep == 9 || MoveTestStep == 10 || MoveTestStep == 12;
	if (bWalkInput)
	{
		Pawn->AddMovementInput(Forward, 1.f);
	}
	if (MoveTestStep == 12)
	{
		// Run at the wall, jump when close, dodge into it while in the air.
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(IAMoveTestWall2), false, Pawn);
		const FVector From = Pawn->GetActorLocation();
		const float Dist = World->LineTraceSingleByChannel(Hit, From, From + Forward * 700.f, ECC_WorldStatic, Params) ? Hit.Distance : 9999.f;
		if (Move->IsMovingOnGround() && Dist < 300.f && !bMoveTestJumped)
		{
			bMoveTestJumped = true;
			Pawn->Jump();
		}
		if (Move->IsFalling() && Dist < 100.f && !bMoveTestDodged)
		{
			bMoveTestDodged = true;
			UE_LOG(LogInstagib, Log, TEXT("MOVETEST wall dodge requested at distance %.0f, speed before %.0f"), Dist, Pawn->GetVelocity().Size2D());
			Pawn->Dodge(EIADodgeDir::Forward);
		}
	}

	if (bFirstFrame || MoveTestLogTimer >= 0.1f)
	{
		MoveTestLogTimer = 0.f;
		const FVector L = Pawn->GetActorLocation();
		const FVector V = Pawn->GetVelocity();
		UE_LOG(LogInstagib, Log, TEXT("MOVETEST %s t=%.2f pos=(%.1f,%.1f,%.1f) vel=(%.0f,%.0f,%.0f) speed2d=%.0f crouched=%d falling=%d dodges=%d"),
			Steps[MoveTestStep].Name, T, L.X, L.Y, L.Z, V.X, V.Y, V.Z, V.Size2D(),
			Pawn->bIsCrouched ? 1 : 0, Move->IsFalling() ? 1 : 0, Move->DodgeCounter);
	}

	if (T >= Steps[MoveTestStep].Duration)
	{
		const FVector L = Pawn->GetActorLocation();
		UE_LOG(LogInstagib, Log, TEXT("MOVETEST_STEP_END %s pos=(%.1f,%.1f,%.1f)"), Steps[MoveTestStep].Name, L.X, L.Y, L.Z);
		if (MoveTestStep == 9) { Pawn->UnCrouch(); }
		MoveTestStepTime = 0.f;
		bMoveTestJumped = false;
		++MoveTestStep;
		if (MoveTestStep >= StepCount)
		{
			UE_LOG(LogInstagib, Log, TEXT("MOVETEST_DONE"));
			if (FParse::Param(FCommandLine::Get(), TEXT("IAMoveTestQuit")))
			{
				FPlatformMisc::RequestExit(false);
			}
			return false;
		}
	}
	return true;
}

bool UIADevSubsystem::ShowroomWalk(float DeltaTime)
{
	// Showroom pawns walk on the spot in different directions (they are put back every now and then).
	ShowroomWalkTime += DeltaTime;
	ShowroomResetTimer += DeltaTime;
	const bool bReset = ShowroomResetTimer > 0.2f;
	if (bReset)
	{
		ShowroomResetTimer = 0.f;
	}

	// The second pawn jumps shortly before the screenshot (-IAShowroomJump), to look at the air pose.
	if (!bMoveTestJumped && ShowroomWalkTime > 5.3f && FParse::Param(FCommandLine::Get(), TEXT("IAShowroomJump")))
	{
		bMoveTestJumped = true;
		if (AIAPlayerCharacter* Jumper = ShowroomPawns.IsValidIndex(1) ? ShowroomPawns[1].Get() : nullptr)
		{
			Jumper->Jump();
		}
	}

	static const FVector2D Dirs[8] = {
		FVector2D(1, 0), FVector2D(-1, 0), FVector2D(0, -1), FVector2D(0, 1),
		FVector2D(1, 1), FVector2D(-1, -1), FVector2D(1, -1), FVector2D(-1, 1) };

	const bool bLogNow = FMath::FloorToInt(ShowroomWalkTime) != FMath::FloorToInt(ShowroomWalkTime - DeltaTime);
	for (int32 Index = 0; Index < ShowroomPawns.Num(); ++Index)
	{
		AIAPlayerCharacter* Pawn = ShowroomPawns[Index].Get();
		if (!Pawn)
		{
			continue;
		}
		if (bLogNow && (Index == 0 || Index == 3))
		{
			const UIAAnimInstance* Anim = Cast<UIAAnimInstance>(Pawn->GetMesh()->GetAnimInstance());
			UE_LOG(LogInstagib, Log, TEXT("SHOWROOM pawn %d z=%.1f mode=%d %s"), Index, Pawn->GetActorLocation().Z,
				static_cast<int32>(Pawn->GetCharacterMovement()->MovementMode.GetValue()), Anim ? *Anim->GetDebugString() : TEXT("no anim instance"));
		}
		const FVector2D D = Dirs[(Index + FMath::FloorToInt(ShowroomWalkTime / 30.f) * 5) % 8].GetSafeNormal();
		Pawn->AddMovementInput(Pawn->GetActorForwardVector(), D.X);
		Pawn->AddMovementInput(Pawn->GetActorRightVector(), D.Y);
		if (bReset && ShowroomHome.IsValidIndex(Index))
		{
			// Back to the spot, but at the height the pawn has now (so that it stays on the floor, or in its jump).
			FVector Home = ShowroomHome[Index];
			Home.Z = Pawn->GetActorLocation().Z;
			Pawn->SetActorLocation(Home, false, nullptr, ETeleportType::TeleportPhysics);
		}
	}
	return true;
}
