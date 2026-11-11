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
 *
 * Movement and animation helpers (FEEL):
 *   -IAMoveTest [-IAMoveTestQuit]  the local player runs a script (jump, double jump, dodges, crouch, walk, wall dodge)
 *                    and logs MOVETEST lines with positions; use it with a listen server + client and p.NetShowCorrections 1
 *   -IAShowroomWalk  the showroom characters walk on the spot in different directions with different view pitch
 *   -IAShowroomJump / -IAShowroomCrouch   one of them jumps / crouches
 *   -IARifleOffset=x,y,z,pitch,yaw,roll[,scale]   rifle in the hand (bone space of hand_r), without a rebuild
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

	// ---- MENUS block: -IAShotAuto makes a map thumbnail (see Tools/make_thumbnails.ps1).
	//   -IAShotAuto -IAShotDelay=14 -IAShotName=Thumb_DM-Foundry  looks at the whole level from outside (or from
	//   inside a corner for closed maps), hides the HUD and the player, takes the picture without UI and logs a THUMB_INFO line.
	bool AutoShotCamera(float DeltaTime);
	FTSTicker::FDelegateHandle AutoShotHandle;
	TWeakObjectPtr<class ACameraActor> AutoCamera;
	bool bAutoShot = false;
};
