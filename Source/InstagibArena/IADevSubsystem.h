// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "IADevSubsystem.generated.h"

/**
 * Developer helper, active only in non-shipping builds.
 *
 * Launching the game with  -IAShotDelay=20  takes a screenshot after 20 seconds
 * and then quits. It exists so that a build can be checked from the command line
 * without anyone watching the screen. Screenshots land in Saved/IAShots.
 *
 * Optional  -IAShotCam=X,Y,Z,Pitch,Yaw  looks through a camera placed there,
 * which gives an overview of a map instead of the player's view.
 * Optional  -IAShotName=name  sets the file name (default shot_00).
 * Optional  -IAShowroom=X,Y,Z,Yaw  lines up the five characters there before the shot.
 * Optional  -IAFire  makes the local player fire a moment before the screenshot.
 * Optional  -IAImpact=X,Y,Z  plays three impact bursts there, plus a hit marker and a message.
 *
 * Multiplayer test helpers (need no screenshot option):
 *   -IAReport        logs what this machine sees every 4 seconds
 *   -IAWalk          walks and turns the local player
 *   -IAFireEvery=2   fires the local player's rifle every 2 seconds
 */
UCLASS()
class INSTAGIBARENA_API UIADevSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	bool ImpactDemo(float DeltaTime);
	bool Report(float DeltaTime);
	bool Walk(float DeltaTime);
	bool AutoFire(float DeltaTime);
	bool FireRifle(float DeltaTime);
	bool SpawnShowroom(float DeltaTime);
	bool PlaceCamera(float DeltaTime);
	bool TakeScreenshot(float DeltaTime);

	FTSTicker::FDelegateHandle PauseHandle;
	FTSTicker::FDelegateHandle ImpactHandle;
	FVector ImpactLocation = FVector::ZeroVector;
	FTSTicker::FDelegateHandle ReportHandle;
	FTSTicker::FDelegateHandle WalkHandle;
	FTSTicker::FDelegateHandle AutoFireHandle;
	FTSTicker::FDelegateHandle FireHandle;
	FTSTicker::FDelegateHandle ShowroomHandle;
	FTSTicker::FDelegateHandle CameraHandle;
	FTSTicker::FDelegateHandle ShotHandle;
	FTSTicker::FDelegateHandle QuitHandle;

	TWeakObjectPtr<class ACameraActor> Camera;
	FVector ShowroomLocation = FVector::ZeroVector;
	float ShowroomYaw = 0.f;
	FVector CameraLocation = FVector::ZeroVector;
	FRotator CameraRotation = FRotator::ZeroRotator;
	FString ShotName = TEXT("shot_00");

	// ---- FEEL: scripted movement test (-IAMoveTest) and showroom walk (-IAShowroomWalk)
	bool MoveTest(float DeltaTime);
	bool ShowroomWalk(float DeltaTime);

	FTSTicker::FDelegateHandle MoveTestHandle;
	FTSTicker::FDelegateHandle ShowroomWalkHandle;
	int32 MoveTestStep = -1;
	float MoveTestStepTime = 0.f;
	float MoveTestLogTimer = 0.f;
	float MoveTestYaw = 0.f;
	bool bMoveTestJumped = false;
	bool bMoveTestDodged = false;
	TArray<TWeakObjectPtr<class AIAPlayerCharacter>> ShowroomPawns;
	// Frame time statistics for the report lines (hitch check with many bots).
	FTSTicker::FDelegateHandle FrameStatHandle;
	float FrameTimeMax = 0.f;
	float FrameTimeSum = 0.f;
	int32 FrameTimeCount = 0;
	int32 FrameHitches = 0;

	TArray<FVector> ShowroomHome;
	float ShowroomWalkTime = 0.f;
	float ShowroomResetTimer = 0.f;
};
