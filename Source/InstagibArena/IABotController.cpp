// Instagib Arena

#include "IABotController.h"
#include "IAPlayerCharacter.h"
#include "IAPlayerState.h"
#include "IAGameState.h"
#include "IANavGrid.h"
#include "InstagibArena.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"

FIABotSkillParams FIABotSkillParams::ForSkill(EIABotSkill Skill)
{
	// Reaction, aim error, turn rate, fire tolerance, dodges/s, jumps/s, sight range, memory, field of view.
	switch (Skill)
	{
	case EIABotSkill::Rookie:        // almost harmless: slow, misses a lot, hardly moves
		return { 1.40f, 24.0f, 40.f, 14.0f, 0.00f, 0.00f, 2500.f, 1.5f, 90.f };
	case EIABotSkill::Beginner:
		return { 1.00f, 16.0f, 65.f, 10.0f, 0.02f, 0.02f, 3500.f, 2.f, 100.f };
	case EIABotSkill::Casual:
		return { 0.75f, 11.0f, 90.f, 7.0f, 0.04f, 0.04f, 4500.f, 3.f, 110.f };
	case EIABotSkill::Advanced:      // the old "intermediate"
		return { 0.30f, 4.0f, 240.f, 3.5f, 0.20f, 0.15f, 8000.f, 6.f, 130.f };
	case EIABotSkill::Expert:        // the old "expert"
		return { 0.12f, 1.2f, 600.f, 1.5f, 0.50f, 0.30f, 14000.f, 10.f, 160.f };
	case EIABotSkill::Master:        // for professionals: near perfect aim, instant reactions
		return { 0.06f, 0.4f, 900.f, 0.8f, 0.70f, 0.40f, 20000.f, 14.f, 170.f };
	case EIABotSkill::Intermediate:
	default:
		return { 0.48f, 7.0f, 150.f, 5.0f, 0.10f, 0.09f, 6000.f, 4.5f, 120.f };
	}
}

AIABotController::AIABotController()
{
	bWantsPlayerState = true;
	PrimaryActorTick.bCanEverTick = true;
	Params = FIABotSkillParams::ForSkill(Skill);
}

void AIABotController::SetSkill(EIABotSkill NewSkill)
{
	Skill = NewSkill;
	Params = FIABotSkillParams::ForSkill(Skill);
}

void AIABotController::OnUnPossess()
{
	Super::OnUnPossess();
	Target.Reset();
	bTargetVisible = false;
	Path.Reset();
	PathIndex = 0;
}

void AIABotController::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	AIAPlayerCharacter* Me = Cast<AIAPlayerCharacter>(GetPawn());
	if (!Me || Me->IsDead())
	{
		return;
	}

	ThinkAccumulator += DeltaSeconds;
	if (ThinkAccumulator >= 0.1f)
	{
		ThinkAccumulator = 0.f;
		Think();
	}

	UpdateAim(Me, DeltaSeconds);
	UpdateMovement(Me, DeltaSeconds);
	UpdateFire(Me);

	LogAccumulator += DeltaSeconds;
	if (LogAccumulator >= 3.f)
	{
		LogAccumulator = 0.f;
		const AIAPlayerState* PS = GetPlayerState<AIAPlayerState>();
		UE_LOG(LogInstagib, Verbose, TEXT("[bot %s] at %s target=%s visible=%d path=%d/%d kills=%d deaths=%d"),
			PS ? *PS->GetPlayerName() : TEXT("?"), *Me->GetActorLocation().ToCompactString(),
			Target.IsValid() ? *GetNameSafe(Target.Get()) : TEXT("none"), bTargetVisible ? 1 : 0,
			PathIndex, Path.Num(), PS ? PS->Kills : 0, PS ? PS->Deaths : 0);
	}
}

// ---------------------------------------------------------------- perception

bool AIABotController::IsEnemy(const AIAPlayerCharacter* Me, const AIAPlayerCharacter* Other) const
{
	const AIAGameState* GS = GetWorld()->GetGameState<AIAGameState>();
	if (!GS || !GS->IsTeamGame())
	{
		return true;
	}
	const AIAPlayerState* A = Me->GetPlayerState<AIAPlayerState>();
	const AIAPlayerState* B = Other->GetPlayerState<AIAPlayerState>();
	return !A || !B || A->Team != B->Team;
}

bool AIABotController::CanSee(const AIAPlayerCharacter* Me, const AIAPlayerCharacter* Other) const
{
	FHitResult Hit;
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(BotSight), true, Me);
	const FVector From = Me->GetPawnViewLocation();
	const FVector To = Other->GetActorLocation();
	if (GetWorld()->LineTraceSingleByChannel(Hit, From, To, ECC_Pawn, QueryParams))
	{
		return Hit.GetActor() == Other;
	}
	return true;
}

void AIABotController::FindTarget(AIAPlayerCharacter* Me)
{
	const float Now = GetWorld()->GetTimeSeconds();
	const FVector Eye = Me->GetPawnViewLocation();
	const FVector Forward = GetControlRotation().Vector();
	const float CosHalfFov = FMath::Cos(FMath::DegreesToRadians(Params.FieldOfViewDeg * 0.5f));

	AIAPlayerCharacter* Best = nullptr;
	float BestDistance = Params.SightRange;

	for (TActorIterator<AIAPlayerCharacter> It(GetWorld()); It; ++It)
	{
		AIAPlayerCharacter* Other = *It;
		if (Other == Me || Other->IsDead() || !IsEnemy(Me, Other))
		{
			continue;
		}

		const FVector ToOther = Other->GetActorLocation() - Eye;
		const float Distance = ToOther.Size();
		if (Distance >= BestDistance)
		{
			continue;
		}
		// Enemies close by are noticed even when behind the bot.
		if (Distance > 700.f && FVector::DotProduct(Forward, ToOther / Distance) < CosHalfFov)
		{
			continue;
		}
		if (!CanSee(Me, Other))
		{
			continue;
		}

		Best = Other;
		BestDistance = Distance;
	}

	if (Best)
	{
		if (Target.Get() != Best || !bTargetVisible)
		{
			TargetAcquiredTime = Now; // the reaction time starts over
		}
		Target = Best;
		bTargetVisible = true;
		LastSeenLocation = Best->GetActorLocation();
		LastSeenTime = Now;
	}
	else
	{
		bTargetVisible = false;
		if (Target.IsValid() && (Target->IsDead() || Now - LastSeenTime > Params.MemorySeconds))
		{
			Target.Reset();
		}
	}
}

bool AIABotController::HasGroundAhead(const AIAPlayerCharacter* Me, const FVector& Direction, float Distance) const
{
	const float HalfHeight = Me->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FVector Start = Me->GetActorLocation() + Direction.GetSafeNormal() * Distance;
	const FVector End = Start - FVector(0.f, 0.f, HalfHeight + 220.f);

	FHitResult Hit;
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(BotGround), false, Me);
	return GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Pawn, QueryParams);
}

bool AIABotController::LineOfFireHitsTeammate(const AIAPlayerCharacter* Me) const
{
	const FVector Eye = Me->GetPawnViewLocation();
	const FVector End = Eye + GetControlRotation().Vector() * 20000.f;

	FHitResult Hit;
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(BotFireLine), true, Me);
	if (GetWorld()->LineTraceSingleByChannel(Hit, Eye, End, ECC_Pawn, QueryParams))
	{
		if (const AIAPlayerCharacter* Other = Cast<AIAPlayerCharacter>(Hit.GetActor()))
		{
			return !IsEnemy(Me, Other);
		}
	}
	return false;
}

// ---------------------------------------------------------------- decisions

void AIABotController::Think()
{
	AIAPlayerCharacter* Me = Cast<AIAPlayerCharacter>(GetPawn());
	if (!Me)
	{
		return;
	}

	FindTarget(Me);

	if (bReleaseJump)
	{
		Me->StopJumping();
		bReleaseJump = false;
	}

	if (bTargetVisible && Me->GetCharacterMovement()->IsMovingOnGround())
	{
		// Think() runs ten times a second.
		if (FMath::FRand() < Params.DodgesPerSecond * 0.1f)
		{
			const bool bLeft = FMath::RandBool();
			const FVector Right = Me->GetActorRightVector();
			const FVector Direction = bLeft ? -Right : Right;
			if (HasGroundAhead(Me, Direction, 450.f))
			{
				Me->Dodge(bLeft ? EIADodgeDir::Left : EIADodgeDir::Right);
			}
		}
		else if (FMath::FRand() < Params.JumpsPerSecond * 0.1f)
		{
			Me->Jump();
			bReleaseJump = true;
		}
	}
}

// ---------------------------------------------------------------- aim and fire

void AIABotController::UpdateAim(AIAPlayerCharacter* Me, float DeltaSeconds)
{
	const float Now = GetWorld()->GetTimeSeconds();
	const FRotator Current = GetControlRotation();
	FRotator Desired = Current;
	float TurnRate = Params.TurnRate;

	if (Target.IsValid() && bTargetVisible)
	{
		if (Now >= NextAimRollTime)
		{
			const float E = Params.AimErrorDegrees;
			AimOffset = FRotator(FMath::FRandRange(-E, E) * 0.6f, FMath::FRandRange(-E, E), 0.f);
			NextAimRollTime = Now + 0.3f;
		}
		Desired = (Target->GetActorLocation() - Me->GetPawnViewLocation()).Rotation();
		Desired.Pitch += AimOffset.Pitch;
		Desired.Yaw += AimOffset.Yaw;
	}
	else
	{
		TurnRate = FMath::Max(TurnRate, 220.f);
		FVector Velocity = Me->GetVelocity();
		Velocity.Z = 0.f;
		if (Target.IsValid())
		{
			Desired = (LastSeenLocation - Me->GetPawnViewLocation()).Rotation();
		}
		else if (Velocity.SizeSquared() > 2500.f)
		{
			Desired = Velocity.Rotation();
			Desired.Pitch = 0.f;
		}
	}

	FRotator NewRotation = FMath::RInterpConstantTo(Current, Desired, DeltaSeconds, TurnRate);
	NewRotation.Roll = 0.f;
	SetControlRotation(NewRotation);
	Me->FaceRotation(NewRotation, DeltaSeconds);
}

void AIABotController::UpdateFire(AIAPlayerCharacter* Me)
{
	if (!Target.IsValid() || !bTargetVisible)
	{
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();
	if (Now - TargetAcquiredTime < Params.ReactionTime)
	{
		return;
	}

	const FVector ToTarget = (Target->GetActorLocation() - Me->GetPawnViewLocation()).GetSafeNormal();
	const float Dot = FVector::DotProduct(GetControlRotation().Vector(), ToTarget);
	const float AngleDeg = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(Dot, -1.f, 1.f)));
	if (AngleDeg > Params.FireToleranceDeg)
	{
		return;
	}

	if (LineOfFireHitsTeammate(Me))
	{
		return;
	}

	Me->TryFire();
}

// ---------------------------------------------------------------- movement

void AIABotController::RepathTo(const FVector& Goal, const FVector& From)
{
	PathGoal = Goal;
	PathIndex = 0;
	NextRepathTime = GetWorld()->GetTimeSeconds() + 1.0f;

	Path.Reset();
	const UIANavGrid* Grid = GetWorld()->GetSubsystem<UIANavGrid>();
	if (!Grid || !Grid->IsReady())
	{
		Path.Add(Goal); // no navigation data at all: walk straight at the goal
	}
	else if (!Grid->FindPath(From, Goal, Path))
	{
		Path.Reset(); // unreachable (for example on another roof): stay put and try again later
	}
}

void AIABotController::FollowPath(AIAPlayerCharacter* Me, float DeltaSeconds)
{
	if (PathIndex >= Path.Num())
	{
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();
	const FVector Location = Me->GetActorLocation();
	const float HalfHeight = Me->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FVector Feet = Location - FVector(0.f, 0.f, HalfHeight);

	while (PathIndex < Path.Num())
	{
		const FVector Delta = Path[PathIndex] - Feet;
		if (FVector2D(Delta.X, Delta.Y).Size() < 70.f && FMath::Abs(Delta.Z) < 120.f)
		{
			++PathIndex;
		}
		else
		{
			break;
		}
	}
	if (PathIndex >= Path.Num())
	{
		return;
	}

	const FVector Delta = Path[PathIndex] - Feet;
	const FVector Direction = FVector(Delta.X, Delta.Y, 0.f).GetSafeNormal();
	Me->AddMovementInput(Direction, 1.f);

	const bool bGrounded = Me->GetCharacterMovement()->IsMovingOnGround();
	if (bGrounded && Delta.Z > 50.f && FVector2D(Delta.X, Delta.Y).Size() < 220.f)
	{
		Me->Jump();
		bReleaseJump = true;
	}

	// Fell off a ledge: the path is on a different level now.
	if (bGrounded && FMath::Abs(Delta.Z) > 250.f)
	{
		Path.Reset();
		NextRepathTime = 0.f;
		return;
	}

	// Stuck detection.
	if (Now - StuckCheckTime > 1.5f)
	{
		if (FVector::Dist(Location, StuckCheckLocation) < 60.f)
		{
			Path.Reset();
			NextRepathTime = 0.f;
			Me->Jump();
			bReleaseJump = true;
		}
		StuckCheckLocation = Location;
		StuckCheckTime = Now;
	}
}

void AIABotController::UpdateMovement(AIAPlayerCharacter* Me, float DeltaSeconds)
{
	const float Now = GetWorld()->GetTimeSeconds();
	const FVector Location = Me->GetActorLocation();
	const float HalfHeight = Me->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const FVector Feet = Location - FVector(0.f, 0.f, HalfHeight);

	// Combat: strafe around the enemy once close enough.
	if (Target.IsValid() && bTargetVisible)
	{
		const FVector ToTarget = Target->GetActorLocation() - Location;
		const float Distance = ToTarget.Size();

		if (Distance > 1800.f)
		{
			if (Path.IsEmpty() || (Now >= NextRepathTime))
			{
				RepathTo(Target->GetActorLocation() - FVector(0.f, 0.f, HalfHeight), Feet);
			}
			FollowPath(Me, DeltaSeconds);
			return;
		}

		if (Now >= NextStrafeFlipTime)
		{
			StrafeDirection = FMath::RandBool() ? 1.f : -1.f;
			NextStrafeFlipTime = Now + FMath::FRandRange(0.7f, 2.0f);
		}

		FVector Strafe = Me->GetActorRightVector() * StrafeDirection;
		if (!HasGroundAhead(Me, Strafe))
		{
			StrafeDirection = -StrafeDirection;
			Strafe = -Strafe;
			NextStrafeFlipTime = Now + 1.f;
			if (!HasGroundAhead(Me, Strafe))
			{
				Strafe = FVector::ZeroVector;
			}
		}
		Me->AddMovementInput(Strafe, 1.f);

		// Keep a comfortable distance.
		const FVector Flat = FVector(ToTarget.X, ToTarget.Y, 0.f).GetSafeNormal();
		if (Distance < 500.f && HasGroundAhead(Me, -Flat))
		{
			Me->AddMovementInput(-Flat, 0.6f);
		}
		else if (Distance > 1200.f)
		{
			Me->AddMovementInput(Flat, 0.4f);
		}
		return;
	}

	// Lost sight: go to the last known position, then give up.
	if (Target.IsValid())
	{
		if (Path.IsEmpty() || FVector::Dist2D(PathGoal, LastSeenLocation) > 200.f)
		{
			RepathTo(LastSeenLocation - FVector(0.f, 0.f, HalfHeight), Feet);
		}
		FollowPath(Me, DeltaSeconds);
		if (PathIndex >= Path.Num())
		{
			Target.Reset();
		}
		return;
	}

	// Nothing to do: roam to a random spot.
	if (PathIndex >= Path.Num() || Path.IsEmpty())
	{
		if (Now >= NextRepathTime)
		{
			FVector Goal;
			const UIANavGrid* Grid = GetWorld()->GetSubsystem<UIANavGrid>();
			if (Grid && Grid->GetRandomLocation(Feet, 1000.f, Goal))
			{
				RepathTo(Goal, Feet);
			}
			else
			{
				NextRepathTime = Now + 1.f;
			}
		}
		return;
	}
	FollowPath(Me, DeltaSeconds);
}
