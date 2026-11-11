// Instagib Arena

#include "IAGameMode.h"
#include "IAPlayerCharacter.h"
#include "IAPlayerController.h"
#include "IAPlayerState.h"
#include "IAHUD.h"
#include "IABotController.h"
#include "IACharacterRoster.h"
#include "InstagibArena.h"
#include "Algo/RandomShuffle.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/GameState.h"
#include "GameFramework/PlayerStart.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "TimerManager.h"

AIAGameMode::AIAGameMode()
{
	DefaultPawnClass = AIAPlayerCharacter::StaticClass();
	PlayerControllerClass = AIAPlayerController::StaticClass();
	PlayerStateClass = AIAPlayerState::StaticClass();
	GameStateClass = AIAGameState::StaticClass();
	HUDClass = AIAHUD::StaticClass();
	bDelayedStart = false;
}

void AIAGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
	Super::InitGame(MapName, Options, ErrorMessage);

	const FString ModeOption = UGameplayStatics::ParseOption(Options, TEXT("Mode"));
	GameType = (ModeOption.Equals(TEXT("TDM"), ESearchCase::IgnoreCase) || ModeOption.Equals(TEXT("Team"), ESearchCase::IgnoreCase))
		? EIAGameType::TeamDeathmatch
		: EIAGameType::FreeForAll;

	ScoreLimit = FMath::Max(0, UGameplayStatics::GetIntOption(Options, TEXT("ScoreLimit"), -1));
	TimeLimitMinutes = FMath::Max(0, UGameplayStatics::GetIntOption(Options, TEXT("TimeLimit"), -1));
	const bool bScoreGiven = UGameplayStatics::HasOption(Options, TEXT("ScoreLimit"));
	const bool bTimeGiven = UGameplayStatics::HasOption(Options, TEXT("TimeLimit"));
	if (!bScoreGiven && !bTimeGiven)
	{
		ScoreLimit = 25;
	}

	const int32 RequestedBots = UGameplayStatics::GetIntOption(Options, TEXT("Bots"), 4);
	BotCount = RequestedBots <= 0 ? 0 : FMath::Clamp(RequestedBots, 2, 10);
	BotSkill = FMath::Clamp(UGameplayStatics::GetIntOption(Options, TEXT("BotSkill"), 1), 0, 2);

#if !UE_BUILD_SHIPPING
	// Test helpers: shorter or longer countdown and results screen.
	float DevValue = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("IAWarmup="), DevValue)) { WarmupSeconds = FMath::Max(0.f, DevValue); }
	if (FParse::Value(FCommandLine::Get(), TEXT("IAResults="), DevValue)) { RestartDelay = FMath::Max(1.f, DevValue); }
#endif

	UE_LOG(LogInstagib, Log, TEXT("Match setup: %s, score limit %d, time limit %d min, bots %d, skill %d"),
		GameType == EIAGameType::TeamDeathmatch ? TEXT("TDM") : TEXT("FFA"), ScoreLimit, TimeLimitMinutes, BotCount, BotSkill);
}

void AIAGameMode::InitGameState()
{
	Super::InitGameState();

	if (AIAGameState* GS = GetGameState<AIAGameState>())
	{
		GS->GameType = GameType;
		GS->ScoreLimit = ScoreLimit;
		GS->TimeLimitSeconds = TimeLimitMinutes * 60;
		GS->ClockSeconds = GS->TimeLimitSeconds;
		GS->Phase = EIAMatchPhase::Warmup;
	}
}

// ---------------------------------------------------------------- match flow

void AIAGameMode::HandleMatchHasStarted()
{
	Super::HandleMatchHasStarted();

	if (!bBotsSpawned)
	{
		bBotsSpawned = true;
		SpawnBots();
	}
	BeginWarmup();

#if !UE_BUILD_SHIPPING
	SetupDevHooks();
#endif
}

void AIAGameMode::BeginWarmup()
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS)
	{
		return;
	}

	FTimerManager& Timers = GetWorldTimerManager();
	Timers.ClearTimer(WarmupTimer);
	Timers.ClearTimer(ClockTimer);
	Timers.ClearTimer(RestartTimer);

	GS->Phase = EIAMatchPhase::Warmup;
	GS->bMatchOver = false;
	GS->PhaseEndTime = GetWorld()->GetTimeSeconds() + WarmupSeconds;
	UE_LOG(LogInstagib, Log, TEXT("Match phase: warmup for %.1f s"), WarmupSeconds);

	if (WarmupSeconds <= 0.f)
	{
		StartLive();
		return;
	}
	Timers.SetTimer(WarmupTimer, this, &AIAGameMode::StartLive, WarmupSeconds, false);
}

void AIAGameMode::StartLive()
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS)
	{
		return;
	}

	GS->Phase = EIAMatchPhase::Live;
	GS->PhaseEndTime = 0.f;
	GetWorldTimerManager().SetTimer(ClockTimer, this, &AIAGameMode::TickClock, 1.f, true);
	UE_LOG(LogInstagib, Log, TEXT("Match phase: live (%d players)"), GS->PlayerArray.Num());

	// Everybody who has no body yet gets one now: this is where the bots enter the arena.
	TArray<AController*> Waiting;
	for (FConstControllerIterator It = GetWorld()->GetControllerIterator(); It; ++It)
	{
		AController* C = It->Get();
		if (C && !C->GetPawn() && C->PlayerState)
		{
			Waiting.Add(C);
		}
	}
	for (AController* C : Waiting)
	{
		RestartPlayer(C);
	}

	// Everybody is protected for a moment when the fight begins (the new bodies already are, see FinishRestartPlayer).
	for (FConstControllerIterator It = GetWorld()->GetControllerIterator(); It; ++It)
	{
		if (const AController* C = It->Get())
		{
			BeginSpawnProtection(C->GetPawn());
		}
	}
}

// ---------------------------------------------------------------- spawn protection

void AIAGameMode::FinishRestartPlayer(AController* NewPlayer, const FRotator& StartRotation)
{
	Super::FinishRestartPlayer(NewPlayer, StartRotation);

	const AIAGameState* GS = GetGameState<AIAGameState>();
	if (NewPlayer && GS && GS->Phase == EIAMatchPhase::Live)
	{
		BeginSpawnProtection(NewPlayer->GetPawn());
	}
}

void AIAGameMode::BeginSpawnProtection(APawn* Pawn)
{
	ACharacter* Body = Cast<ACharacter>(Pawn);
	AIAPlayerState* State = Pawn ? Pawn->GetPlayerState<AIAPlayerState>() : nullptr;
	if (!Body || !State || SpawnProtectSeconds <= 0.f || Protected.Contains(Pawn))
	{
		return;
	}

	// The body keeps its collision (the clients predict movement with it). A shot passes through a protected
	// player because ServerFire ignores bodies whose SpawnProtectEndTime has not passed yet.
	Protected.Add(Pawn, FProtection());
	State->SpawnProtectEndTime = GetWorld()->GetTimeSeconds() + SpawnProtectSeconds;

	TWeakObjectPtr<APawn> WeakPawn(Pawn);
	FTimerHandle Handle;
	GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this, WeakPawn]()
	{
		if (APawn* P = WeakPawn.Get())
		{
			EndSpawnProtection(P);
		}
		else
		{
			Protected.Remove(WeakPawn);
		}
	}), SpawnProtectSeconds, false);
}

void AIAGameMode::EndSpawnProtection(APawn* Pawn)
{
	const FProtection* Saved = Pawn ? Protected.Find(Pawn) : nullptr;
	if (!Saved)
	{
		return;
	}
	if (AIAPlayerState* State = Pawn->GetPlayerState<AIAPlayerState>())
	{
		State->SpawnProtectEndTime = 0.f;
	}
	Protected.Remove(Pawn);
	UE_LOG(LogInstagib, Verbose, TEXT("Spawn protection ended for %s"), *Pawn->GetName());
}

void AIAGameMode::StartNewMatch()
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || GS->Phase != EIAMatchPhase::Ended)
	{
		return;
	}

	++MatchGeneration;
	bFirstBloodDone = false;
	LastFragsLeft = ScoreLimit;
	TeamLead[0] = TeamLead[1] = 0;

	GS->RedScore = 0;
	GS->BlueScore = 0;
	GS->ClockSeconds = GS->TimeLimitSeconds;
	GS->WinnerText.Empty();
	GS->WinnerPlayerId = -1;
	GS->WinnerTeam = IA_NoTeam;
	for (APlayerState* PS : GS->PlayerArray)
	{
		if (AIAPlayerState* State = Cast<AIAPlayerState>(PS))
		{
			State->ResetMatchStats();
		}
	}

	Protected.Reset();

	// Every body goes, including the ones still lying around from the last fight.
	TArray<AController*> Controllers;
	for (FConstControllerIterator It = GetWorld()->GetControllerIterator(); It; ++It)
	{
		if (AController* C = It->Get())
		{
			Controllers.Add(C);
			if (APawn* Old = C->GetPawn())
			{
				C->UnPossess();
				Old->Destroy();
			}
		}
	}
	for (TActorIterator<AIAPlayerCharacter> It(GetWorld()); It; ++It)
	{
		It->Destroy();
	}

	UE_LOG(LogInstagib, Log, TEXT("New match starts (%d controllers)"), Controllers.Num());
	BeginWarmup();

	// Humans get their body right away (bots wait for the fight).
	for (AController* C : Controllers)
	{
		if (C && !C->GetPawn() && Cast<APlayerController>(C) && C->PlayerState)
		{
			RestartPlayer(C);
		}
	}
}

void AIAGameMode::SpawnBots()
{
	// Bots take the characters that the humans did not pick, in random order.
	TSet<int32> TakenByHumans;
	if (GameState)
	{
		for (APlayerState* Other : GameState->PlayerArray)
		{
			if (const AIAPlayerState* OtherState = Cast<AIAPlayerState>(Other))
			{
				TakenByHumans.Add(OtherState->CharacterIndex);
			}
		}
	}

	TArray<int32> Roster;
	for (int32 I = 0; I < IACharacters::LookCount; ++I)
	{
		if (!TakenByHumans.Contains(I))
		{
			Roster.Add(I);
		}
	}
	Algo::RandomShuffle(Roster);
	if (Roster.IsEmpty())
	{
		Roster.Add(0);
	}

	for (int32 I = 0; I < BotCount; ++I)
	{
		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AIABotController* Bot = GetWorld()->SpawnActor<AIABotController>(AIABotController::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);
		if (!Bot)
		{
			continue;
		}

		Bot->SetSkill(static_cast<EIABotSkill>(BotSkill));

		if (AIAPlayerState* PS = Bot->GetPlayerState<AIAPlayerState>())
		{
			const int32 CharacterIndex = Roster[I % Roster.Num()];
			PS->SetPlayerName(IACharacters::GetLook(CharacterIndex).Name);
			PS->bIsBotPlayer = true;
			PS->SlotId = NextSlotId++;
			PS->CharacterIndex = CharacterIndex;
			AssignTeam(PS);
		}
		// The body comes when the countdown ends (StartLive).
	}
}

void AIAGameMode::PostLogin(APlayerController* NewPlayer)
{
	Super::PostLogin(NewPlayer);

	if (AIAPlayerState* PS = NewPlayer ? NewPlayer->GetPlayerState<AIAPlayerState>() : nullptr)
	{
		PS->SlotId = NextSlotId++;
		AssignTeam(PS);
		UE_LOG(LogInstagib, Log, TEXT("Player joined: %s (character %d, team %d), %d players in the match"),
			*PS->GetPlayerName(), PS->CharacterIndex, static_cast<int32>(PS->Team), GameState ? GameState->PlayerArray.Num() : 0);
	}
}

FString AIAGameMode::InitNewPlayer(APlayerController* NewPlayerController, const FUniqueNetIdRepl& UniqueId, const FString& Options, const FString& Portal)
{
	const FString Result = Super::InitNewPlayer(NewPlayerController, UniqueId, Options, Portal);

	// The character a player picked in the menu travels in the URL as ?Char=0..4.
	if (AIAPlayerState* PS = NewPlayerController ? NewPlayerController->GetPlayerState<AIAPlayerState>() : nullptr)
	{
		PS->CharacterIndex = FMath::Clamp(UGameplayStatics::GetIntOption(Options, TEXT("Char"), 0), 0, IACharacters::LookCount - 1);
	}
	return Result;
}

void AIAGameMode::AssignTeam(AIAPlayerState* PlayerState)
{
	if (GameType != EIAGameType::TeamDeathmatch)
	{
		PlayerState->Team = IA_NoTeam;
		return;
	}

	int32 Red = 0;
	int32 Blue = 0;
	if (const AGameStateBase* GS = GameState)
	{
		for (APlayerState* Other : GS->PlayerArray)
		{
			const AIAPlayerState* OtherState = Cast<AIAPlayerState>(Other);
			if (!OtherState || OtherState == PlayerState)
			{
				continue;
			}
			if (OtherState->Team == 0) { ++Red; }
			else if (OtherState->Team == 1) { ++Blue; }
		}
	}
	PlayerState->Team = (Red <= Blue) ? 0 : 1;
}

void AIAGameMode::TickClock()
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || GS->Phase != EIAMatchPhase::Live)
	{
		return;
	}

	if (GS->TimeLimitSeconds > 0)
	{
		GS->ClockSeconds = FMath::Max(0, GS->ClockSeconds - 1);
		if (GS->ClockSeconds == 0)
		{
			DetermineWinnerByScore();
		}
	}
	else
	{
		++GS->ClockSeconds;
	}
}

// ---------------------------------------------------------------- kills

void AIAGameMode::ScheduleRespawn(AController* Victim, float Delay)
{
	TWeakObjectPtr<AController> WeakVictim(Victim);
	const int32 Generation = MatchGeneration;
	FTimerHandle RespawnHandle;
	GetWorldTimerManager().SetTimer(RespawnHandle, FTimerDelegate::CreateLambda([this, WeakVictim, Generation]()
	{
		const AIAGameState* GS = GetGameState<AIAGameState>();
		if (!WeakVictim.IsValid() || !GS || Generation != MatchGeneration || WeakVictim->GetPawn())
		{
			return;
		}
		if (GS->Phase == EIAMatchPhase::Ended)
		{
			return;
		}
		// Bots wait in the countdown like everybody else; they come in when the fight starts (StartLive).
		if (GS->Phase == EIAMatchPhase::Warmup && !Cast<APlayerController>(WeakVictim.Get()))
		{
			return;
		}
		RestartPlayer(WeakVictim.Get());
	}), FMath::Max(0.05f, Delay), false);
}

void AIAGameMode::OnPlayerKilled(AController* Killer, AController* Victim)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!Victim || !GS)
	{
		return;
	}

	// Falling into the void in the countdown costs nothing; after the match nothing counts at all.
	if (GS->Phase != EIAMatchPhase::Live)
	{
		if (GS->Phase == EIAMatchPhase::Warmup)
		{
			ScheduleRespawn(Victim, 1.f);
		}
		return;
	}

	AIAPlayerState* VictimState = Victim->GetPlayerState<AIAPlayerState>();
	AIAPlayerState* KillerState = Killer ? Killer->GetPlayerState<AIAPlayerState>() : nullptr;
	const bool bRealKill = Killer && Killer != Victim && KillerState;
	const float Now = GetWorld()->GetTimeSeconds();

	UE_LOG(LogInstagib, Log, TEXT("%s was fragged by %s"),
		VictimState ? *VictimState->GetPlayerName() : TEXT("?"),
		KillerState ? *KillerState->GetPlayerName() : TEXT("the world"));
	if (APawn* VictimPawn = Victim->GetPawn())
	{
		if (const ACharacter* VictimBody = Cast<ACharacter>(VictimPawn); VictimBody && Protected.Contains(VictimPawn))
		{
			UE_LOG(LogInstagib, Verbose, TEXT("%s was fragged while protected (a fall or a kill volume ignores protection)"), *VictimBody->GetName());
		}
	}

	// Tell the victim who did it and where from (death camera and killer panel).
	if (AIAPlayerController* VictimPC = Cast<AIAPlayerController>(Victim))
	{
		const APawn* VictimPawn = Victim->GetPawn();
		const APawn* KillerPawn = bRealKill ? Killer->GetPawn() : nullptr;
		const FVector VictimLocation = VictimPawn ? VictimPawn->GetPawnViewLocation() : FVector::ZeroVector;
		VictimPC->ClientYouDied(bRealKill ? KillerState : nullptr, const_cast<APawn*>(KillerPawn),
			KillerPawn ? KillerPawn->GetActorLocation() : FVector::ZeroVector, VictimLocation, Victim->GetControlRotation(), RespawnDelay);
	}
	if (bRealKill)
	{
		if (AIAPlayerController* KillerPC = Cast<AIAPlayerController>(Killer))
		{
			KillerPC->ClientShowMessage(FString::Printf(TEXT("You fragged %s"), VictimState ? *VictimState->GetPlayerName() : TEXT("?")),
				FLinearColor(1.f, 0.85f, 0.2f), 1.5f);
		}
	}

	// Score.
	if (VictimState)
	{
		++VictimState->Deaths;
		VictimState->RegisterDeath();
	}

	int32 MultiKillCount = 0;
	if (bRealKill)
	{
		++KillerState->Kills;
		MultiKillCount = KillerState->RegisterKill(Now, MultiKillWindow);
		if (GS->IsTeamGame())
		{
			if (KillerState->Team == 0) { ++GS->RedScore; }
			else if (KillerState->Team == 1) { ++GS->BlueScore; }
		}
	}
	else if (VictimState)
	{
		// Suicide or falling out of the world costs a point.
		--VictimState->Kills;
		if (GS->IsTeamGame())
		{
			if (VictimState->Team == 0) { --GS->RedScore; }
			else if (VictimState->Team == 1) { --GS->BlueScore; }
		}
	}

	const int32 VictimId = VictimState ? VictimState->SlotId : -1;
	GS->MulticastKillFeed(bRealKill ? KillerState->SlotId : (Killer == Victim ? VictimId : -1), VictimId);
	if (bRealKill)
	{
		AnnounceKillMedals(KillerState, MultiKillCount);
	}

	CheckScoreLimit();

	if (GS->Phase == EIAMatchPhase::Live)
	{
		UpdateLeadStates();
		CheckFragsLeft();
		ScheduleRespawn(Victim, RespawnDelay);
	}
}

void AIAGameMode::AnnounceKillMedals(AIAPlayerState* Killer, int32 MultiKillCount)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || !Killer)
	{
		return;
	}
	const int32 Id = Killer->SlotId;

	if (!bFirstBloodDone)
	{
		bFirstBloodDone = true;
		GS->MulticastAnnounce(EIAAnnounce::FirstBlood, Id, 0);
	}

	if (MultiKillCount >= 2)
	{
		const EIAAnnounce Kind = MultiKillCount == 2 ? EIAAnnounce::DoubleKill
			: MultiKillCount == 3 ? EIAAnnounce::MultiKill
			: MultiKillCount == 4 ? EIAAnnounce::UltraKill : EIAAnnounce::MonsterKill;
		GS->MulticastAnnounce(Kind, Id, MultiKillCount);
	}

	switch (Killer->Streak)
	{
	case 5:  GS->MulticastAnnounce(EIAAnnounce::KillingSpree, Id, 5); break;
	case 10: GS->MulticastAnnounce(EIAAnnounce::Rampage, Id, 10); break;
	case 15: GS->MulticastAnnounce(EIAAnnounce::Dominating, Id, 15); break;
	case 20: GS->MulticastAnnounce(EIAAnnounce::Unstoppable, Id, 20); break;
	case 25: GS->MulticastAnnounce(EIAAnnounce::GodLike, Id, 25); break;
	default: break;
	}
}

void AIAGameMode::UpdateLeadStates()
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS)
	{
		return;
	}

	// Compares the old and the new state: 0 = behind, 1 = tied for the lead, 2 = leading alone.
	auto Transition = [GS](uint8 Old, uint8 New, int32 Subject, int32 Param)
	{
		if (New == Old)
		{
			return;
		}
		if (New == 2) { GS->MulticastAnnounce(EIAAnnounce::TookLead, Subject, Param); }
		else if (New == 1) { GS->MulticastAnnounce(EIAAnnounce::TiedLead, Subject, Param); }
		else { GS->MulticastAnnounce(EIAAnnounce::LostLead, Subject, Param); }
	};

	if (GS->IsTeamGame())
	{
		const int32 Scores[2] = { GS->RedScore, GS->BlueScore };
		for (int32 T = 0; T < 2; ++T)
		{
			const int32 Mine = Scores[T];
			const int32 Other = Scores[1 - T];
			const uint8 New = (Mine > 0 && Mine > Other) ? 2 : ((Mine > 0 && Mine == Other) ? 1 : 0);
			Transition(TeamLead[T], New, -1, T);
			TeamLead[T] = New;
		}
		return;
	}

	int32 Max = 0;
	int32 AtMax = 0;
	for (APlayerState* PS : GS->PlayerArray)
	{
		if (const AIAPlayerState* State = Cast<AIAPlayerState>(PS))
		{
			if (State->Kills > Max) { Max = State->Kills; AtMax = 1; }
			else if (State->Kills == Max && Max > 0) { ++AtMax; }
		}
	}
	for (APlayerState* PS : GS->PlayerArray)
	{
		AIAPlayerState* State = Cast<AIAPlayerState>(PS);
		if (!State)
		{
			continue;
		}
		const uint8 New = (Max > 0 && State->Kills == Max) ? (AtMax == 1 ? 2 : 1) : 0;
		if (!State->bIsBotPlayer)
		{
			Transition(State->LeadState, New, State->SlotId, 0);
		}
		State->LeadState = New;
	}
}

void AIAGameMode::CheckFragsLeft()
{
	const AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || ScoreLimit < 3)
	{
		return;
	}

	int32 Top = 0;
	if (GS->IsTeamGame())
	{
		Top = FMath::Max(GS->RedScore, GS->BlueScore);
	}
	else
	{
		for (APlayerState* PS : GS->PlayerArray)
		{
			if (const AIAPlayerState* State = Cast<AIAPlayerState>(PS))
			{
				Top = FMath::Max(Top, State->Kills);
			}
		}
	}

	const int32 Left = ScoreLimit - Top;
	const bool bWorthAnnouncing = Left == 1 || (Left <= 3 && ScoreLimit >= 8);
	if (Left >= 1 && Left < LastFragsLeft && bWorthAnnouncing)
	{
		const_cast<AIAGameState*>(GS)->MulticastAnnounce(EIAAnnounce::FragsLeft, -1, Left);
	}
	LastFragsLeft = Left;
}

// ---------------------------------------------------------------- end of the match

void AIAGameMode::CheckScoreLimit()
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || ScoreLimit <= 0)
	{
		return;
	}

	if (GS->IsTeamGame())
	{
		if (GS->RedScore >= ScoreLimit) { FinishMatch(TEXT("Red team wins!"), -1, 0); }
		else if (GS->BlueScore >= ScoreLimit) { FinishMatch(TEXT("Blue team wins!"), -1, 1); }
		return;
	}

	for (APlayerState* PS : GS->PlayerArray)
	{
		const AIAPlayerState* State = Cast<AIAPlayerState>(PS);
		if (State && State->Kills >= ScoreLimit)
		{
			FinishMatch(FString::Printf(TEXT("%s wins!"), *State->GetPlayerName()), State->SlotId, IA_NoTeam);
			return;
		}
	}
}

void AIAGameMode::DetermineWinnerByScore()
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS)
	{
		return;
	}

	if (GS->IsTeamGame())
	{
		if (GS->RedScore > GS->BlueScore) { FinishMatch(TEXT("Red team wins!"), -1, 0); }
		else if (GS->BlueScore > GS->RedScore) { FinishMatch(TEXT("Blue team wins!"), -1, 1); }
		else { FinishMatch(TEXT("Draw!"), -1, IA_NoTeam); }
		return;
	}

	const AIAPlayerState* Best = nullptr;
	bool bTie = false;
	for (APlayerState* PS : GS->PlayerArray)
	{
		const AIAPlayerState* State = Cast<AIAPlayerState>(PS);
		if (!State)
		{
			continue;
		}
		if (!Best || State->Kills > Best->Kills)
		{
			Best = State;
			bTie = false;
		}
		else if (State->Kills == Best->Kills)
		{
			bTie = true;
		}
	}

	if (!Best || bTie)
	{
		FinishMatch(TEXT("Draw!"), -1, IA_NoTeam);
	}
	else
	{
		FinishMatch(FString::Printf(TEXT("%s wins!"), *Best->GetPlayerName()), Best->SlotId, IA_NoTeam);
	}
}

void AIAGameMode::FinishMatch(const FString& WinnerText, int32 WinnerPlayerId, uint8 WinnerTeam)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || GS->Phase != EIAMatchPhase::Live)
	{
		return;
	}

	GS->WinnerText = WinnerText;
	GS->WinnerPlayerId = WinnerPlayerId;
	GS->WinnerTeam = WinnerTeam;
	GS->bMatchOver = true;
	GS->Phase = EIAMatchPhase::Ended;
	GS->PhaseEndTime = GetWorld()->GetTimeSeconds() + RestartDelay;
	UE_LOG(LogInstagib, Log, TEXT("Match phase: ended (%s), next match in %.0f s"), *WinnerText, RestartDelay);

	GetWorldTimerManager().ClearTimer(ClockTimer);
	GetWorldTimerManager().SetTimer(RestartTimer, this, &AIAGameMode::StartNewMatch, RestartDelay, false);
}

// ---------------------------------------------------------------- smart spawning

AActor* AIAGameMode::ChoosePlayerStart_Implementation(AController* Player)
{
	UWorld* World = GetWorld();
	TArray<APlayerStart*> Starts;
	for (TActorIterator<APlayerStart> It(World); It; ++It)
	{
		Starts.Add(*It);
	}
	if (Starts.IsEmpty())
	{
		return Super::ChoosePlayerStart_Implementation(Player);
	}

	const AIAGameState* GS = GetGameState<AIAGameState>();
	const AIAPlayerState* MyState = Player ? Player->GetPlayerState<AIAPlayerState>() : nullptr;
	const bool bTeamGame = GS && GS->IsTeamGame();

	// Everybody alive who could shoot the arrival (team mates are no danger).
	TArray<const AIAPlayerCharacter*> Threats;
	for (TActorIterator<AIAPlayerCharacter> It(World); It; ++It)
	{
		const AIAPlayerCharacter* Other = *It;
		if (Other->IsDead() || (Player && Other->GetController() == Player) || Other->IsPendingKillPending())
		{
			continue;
		}
		const AIAPlayerState* OtherState = Other->GetPlayerState<AIAPlayerState>();
		if (bTeamGame && MyState && OtherState && OtherState->Team == MyState->Team)
		{
			continue;
		}
		Threats.Add(Other);
	}

	const float Now = World->GetTimeSeconds();
	APlayerStart* Best = nullptr;
	float BestScore = -FLT_MAX;
	for (APlayerStart* Start : Starts)
	{
		const FVector Eye = Start->GetActorLocation() + FVector(0.f, 0.f, 70.f);
		float Score = FMath::FRandRange(0.f, 10.f);
		float MinDistance = FLT_MAX;
		for (const AIAPlayerCharacter* Other : Threats)
		{
			const FVector OtherLocation = Other->GetActorLocation();
			const float Distance = FVector::Dist(Start->GetActorLocation(), OtherLocation);
			MinDistance = FMath::Min(MinDistance, Distance);
			if (Distance < 4000.f)
			{
				FCollisionQueryParams Params(SCENE_QUERY_STAT(SpawnSight), false);
				Params.AddIgnoredActor(Other);
				if (!World->LineTraceTestByChannel(Eye, OtherLocation, ECC_Visibility, Params))
				{
					Score -= 20.f + 40.f * (1.f - Distance / 4000.f);   // it would be shot in the back at once
				}
			}
		}
		Score += FMath::Min(MinDistance, 3000.f) * 0.02f;
		if (MinDistance < 220.f)
		{
			Score -= 500.f;   // somebody stands on it
		}
		if (const float* LastUse = StartLastUse.Find(Start))
		{
			if (Now - *LastUse < 3.f)
			{
				Score -= 60.f;
			}
		}
		if (Score > BestScore)
		{
			BestScore = Score;
			Best = Start;
		}
	}

	if (Best)
	{
		StartLastUse.Add(Best, Now);
		UE_LOG(LogInstagib, Log, TEXT("Spawn for %s: %s (score %.1f, %d enemies alive, of %d spawn points)"),
			MyState ? *MyState->GetPlayerName() : TEXT("?"), *Best->GetName(), BestScore, Threats.Num(), Starts.Num());
	}
	return Best;
}

// ---------------------------------------------------------------- developer helpers

#if !UE_BUILD_SHIPPING
void AIAGameMode::SetupDevHooks()
{
	// -IAFakeKills=S: S seconds after the fight starts the first human scores five kills in a row (medal and feed test).
	// -IAKillMe=S:    S seconds after the fight starts a bot kills the first human (death camera test).
	float FakeKillsAt = 0.f;
	float KillMeAt = 0.f;
	const bool bFake = FParse::Value(FCommandLine::Get(), TEXT("IAFakeKills="), FakeKillsAt);
	const bool bKillMe = FParse::Value(FCommandLine::Get(), TEXT("IAKillMe="), KillMeAt);
	const bool bProbe = FParse::Param(FCommandLine::Get(), TEXT("IAProtProbe"));
	if (!bFake && !bKillMe && !bProbe)
	{
		return;
	}

	const float StartDelay = WarmupSeconds + 1.f;
	if (bProbe)
	{
		// -IAProtProbe: 3 s into the fight, shoots the same line at the first human with and without spawn protection.
		FTimerHandle Handle;
		GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this]()
		{
			APawn* Target = nullptr;
			for (FConstControllerIterator It = GetWorld()->GetControllerIterator(); It; ++It)
			{
				if (APlayerController* PC = Cast<APlayerController>(It->Get()))
				{
					if (PC->GetPawn()) { Target = PC->GetPawn(); }
				}
			}
			if (!Target)
			{
				UE_LOG(LogInstagib, Log, TEXT("PROTECTION PROBE: no human body to test"));
				return;
			}
			EndSpawnProtection(Target);
			const FVector Center = Target->GetActorLocation();
			auto Hits = [&](const FVector& From)
			{
				FHitResult Hit;
				FCollisionQueryParams Params(SCENE_QUERY_STAT(ProtectionProbe), true);
				return GetWorld()->LineTraceSingleByChannel(Hit, From, Center, ECC_Pawn, Params) && Hit.GetActor() == Target;
			};
			FVector From = FVector::ZeroVector;
			bool bOpen = false;
			for (int32 I = 0; I < 8 && !bOpen; ++I)
			{
				From = Center + FRotator(0.f, I * 45.f, 0.f).Vector() * 250.f;
				bOpen = Hits(From);
			}
			if (!bOpen)
			{
				UE_LOG(LogInstagib, Log, TEXT("PROTECTION PROBE: no clear line to the body, inconclusive"));
				return;
			}
			BeginSpawnProtection(Target);
			const bool bDuring = Hits(From);
			EndSpawnProtection(Target);
			const bool bAfter = Hits(From);
			UE_LOG(LogInstagib, Log, TEXT("PROTECTION PROBE: unprotected hit=1, protected hit=%d, after protection hit=%d"), bDuring ? 1 : 0, bAfter ? 1 : 0);
		}), StartDelay + 3.f, false);
	}
	if (bFake)
	{
		for (int32 I = 0; I < 5; ++I)
		{
			FTimerHandle Handle;
			GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this]()
			{
				AController* Human = nullptr;
				AController* Bot = nullptr;
				for (FConstControllerIterator It = GetWorld()->GetControllerIterator(); It; ++It)
				{
					if (Cast<APlayerController>(It->Get()) && !Human) { Human = It->Get(); }
					if (Cast<AIABotController>(It->Get())) { Bot = It->Get(); }
				}
				if (Human && Bot)
				{
					OnPlayerKilled(Human, Bot);
				}
			}), StartDelay + FakeKillsAt + I * 0.7f, false);
		}
	}
	if (bKillMe)
	{
		FTimerHandle Handle;
		GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this]()
		{
			// The last human in the list: a remote client when there is one, else the local player.
			APlayerController* Target = nullptr;
			AIABotController* Shooter = nullptr;
			for (FConstControllerIterator It = GetWorld()->GetControllerIterator(); It; ++It)
			{
				APlayerController* PC = Cast<APlayerController>(It->Get());
				if (PC && PC->GetPawn()) { Target = PC; }
				AIABotController* Bot = Cast<AIABotController>(It->Get());
				if (Bot && Bot->GetPawn()) { Shooter = Bot; }
			}
			if (Target && Shooter)
			{
				UGameplayStatics::ApplyDamage(Target->GetPawn(), 1000.f, Shooter, Shooter->GetPawn(), UDamageType::StaticClass());
			}
		}), StartDelay + KillMeAt, false);
	}
}
#endif
