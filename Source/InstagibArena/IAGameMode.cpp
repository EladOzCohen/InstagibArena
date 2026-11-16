// Instagib Arena

#include "IAGameMode.h"
#include "IAPlayerCharacter.h"
#include "IAPlayerController.h"
#include "IAPlayerState.h"
#include "IAHUD.h"
#include "IABotController.h"
#include "IACharacterRoster.h"
#include "IACampaignSubsystem.h"
#include "IAFlag.h"
#include "IAFlagBase.h"
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
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.04f;   // capture the flag: touches are checked 25 times a second
}

void AIAGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
	Super::InitGame(MapName, Options, ErrorMessage);

	const FString ModeOption = UGameplayStatics::ParseOption(Options, TEXT("Mode"));
	if (ModeOption.Equals(TEXT("TDM"), ESearchCase::IgnoreCase) || ModeOption.Equals(TEXT("Team"), ESearchCase::IgnoreCase))
	{
		GameType = EIAGameType::TeamDeathmatch;
	}
	else if (ModeOption.Equals(TEXT("CTF"), ESearchCase::IgnoreCase) || ModeOption.Equals(TEXT("CaptureTheFlag"), ESearchCase::IgnoreCase))
	{
		GameType = EIAGameType::CaptureTheFlag;
	}
	else if (ModeOption.Equals(TEXT("Survival"), ESearchCase::IgnoreCase))
	{
		GameType = EIAGameType::Survival;
	}
	else
	{
		GameType = EIAGameType::FreeForAll;
	}

	ScoreLimit =FMath::Max(0, UGameplayStatics::GetIntOption(Options, TEXT("ScoreLimit"), -1));
	TimeLimitMinutes = FMath::Max(0, UGameplayStatics::GetIntOption(Options, TEXT("TimeLimit"), -1));
	const bool bScoreGiven = UGameplayStatics::HasOption(Options, TEXT("ScoreLimit"));
	const bool bTimeGiven = UGameplayStatics::HasOption(Options, TEXT("TimeLimit"));
	if (GameType == EIAGameType::CaptureTheFlag)
	{
		// Captures: 5 and 15 minutes unless the options say otherwise.
		if (!bScoreGiven) { ScoreLimit = 5; }
		if (!bTimeGiven) { TimeLimitMinutes = 15; }
	}
	else if (GameType == EIAGameType::Survival)
	{
		// ScoreLimit = number of waves; the clock is the time the squad has for all of them.
		if (!bScoreGiven) { ScoreLimit = 5; }
		if (!bTimeGiven) { TimeLimitMinutes = 15; }
	}
	else if (!bScoreGiven && !bTimeGiven)
	{
		ScoreLimit = 25;
	}

	const int32 RequestedBots = UGameplayStatics::GetIntOption(Options, TEXT("Bots"), 4);
	BotCount = RequestedBots <= 0 ? 0 : FMath::Clamp(RequestedBots, 2, 10);
	BotSkill = FMath::Clamp(UGameplayStatics::GetIntOption(Options, TEXT("BotSkill"), 3), 0, 6);

	// Campaign matches name the ladder match (Camp=1..20) and may have a single bot (duel).
	const int32 CampaignOption = UGameplayStatics::GetIntOption(Options, UIACampaignSubsystem::UrlOption, 0);
	CampaignMatch = (CampaignOption > 0 && CampaignOption <= IACampaign::MatchCount) ? CampaignOption - 1 : -1;
	if (CampaignMatch >= 0 && RequestedBots > 0)
	{
		BotCount = FMath::Clamp(RequestedBots, 1, 12);
	}

#if !UE_BUILD_SHIPPING
	// Test helpers: shorter or longer countdown and results screen.
	float DevValue = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("IAWarmup="), DevValue)) { WarmupSeconds = FMath::Max(0.f, DevValue); }
	if (FParse::Value(FCommandLine::Get(), TEXT("IAResults="), DevValue)) { RestartDelay = FMath::Max(1.f, DevValue); }
#endif

	UE_LOG(LogInstagib, Log, TEXT("Match setup: %s, score limit %d, time limit %d min, bots %d, skill %d"),
		GameType == EIAGameType::CaptureTheFlag ? TEXT("CTF") : (GameType == EIAGameType::TeamDeathmatch ? TEXT("TDM") : (GameType == EIAGameType::Survival ? TEXT("Survival") : TEXT("FFA"))),
		ScoreLimit, TimeLimitMinutes, BotCount, BotSkill);
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
	SetupCTF();
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
	ResetFlags();
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

	if (GameType == EIAGameType::Survival)
	{
		StartWave(1);
	}

	// Campaign: the title of the match, in the announcer's voice.
	if (CampaignMatch >= 0)
	{
		const FIACampaignMatch& M = IACampaign::Matches()[CampaignMatch];
		for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
		{
			if (AIAPlayerController* PC = Cast<AIAPlayerController>(It->Get()))
			{
				PC->ClientShowMessage(FString::Printf(TEXT("MATCH %d: %s"), CampaignMatch + 1, *FString(M.Title).ToUpper()), FLinearColor(1.f, 0.78f, 0.25f), 3.f);
			}
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

	if (GameType == EIAGameType::Survival)
	{
		GetWorldTimerManager().ClearTimer(WaveTimer);
		ClearEnemyControllers();
		WaveNumber = 0;
		bWaveActive = false;
		GS->Wave = 0;
		GS->WaveEnemiesLeft = 0;
	}

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

	// Campaign: the squad and the League's draft fight on the player's side, the faction on the other.
	TArray<int32> ScriptedLooks;
	TArray<bool> ScriptedAlly;
	if (CampaignMatch >= 0 && GetGameInstance())
	{
		if (const UIACampaignSubsystem* Camp = GetGameInstance()->GetSubsystem<UIACampaignSubsystem>())
		{
			for (int32 Look : Camp->BuildAllyLooks(CampaignMatch)) { ScriptedLooks.Add(Look); ScriptedAlly.Add(true); }
			for (int32 Look : Camp->BuildEnemyLooks(CampaignMatch)) { ScriptedLooks.Add(Look); ScriptedAlly.Add(false); }
		}
	}

	// Survival: only the allies are here from the start; the enemies come in waves.
	if (GameType == EIAGameType::Survival)
	{
		SurvivalEnemyLooks.Reset();
		int32 EnemyEntries = 0;
		for (int32 I = 0; I < ScriptedLooks.Num(); ++I)
		{
			if (!ScriptedAlly[I]) { SurvivalEnemyLooks.Add(ScriptedLooks[I]); ++EnemyEntries; }
		}
		SurvivalEnemyBase = EnemyEntries > 0 ? EnemyEntries : FMath::Max(1, BotCount);
	}

	for (int32 I = 0; I < BotCount; ++I)
	{
		if (GameType == EIAGameType::Survival && !(ScriptedAlly.IsValidIndex(I) && ScriptedAlly[I]))
		{
			continue;
		}
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
			const bool bScripted = ScriptedLooks.IsValidIndex(I);
			const int32 CharacterIndex = bScripted ? ScriptedLooks[I] : Roster[I % Roster.Num()];
			PS->SetPlayerName(IACharacters::GetLook(CharacterIndex).Name);
			PS->bIsBotPlayer = true;
			PS->SlotId = NextSlotId++;
			PS->CharacterIndex = CharacterIndex;
			AssignTeam(PS);
			if (bScripted && GameType != EIAGameType::FreeForAll)
			{
				PS->Team = ScriptedAlly[I] ? 0 : 1;   // the human takes the red side (the first player in)
			}
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
	if (GameType == EIAGameType::FreeForAll)
	{
		PlayerState->Team = IA_NoTeam;
		return;
	}
	if (GameType == EIAGameType::Survival)
	{
		PlayerState->Team = 0;   // the humans and the allies; the waves are team 1
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

	// A carrier who dies (or falls out of the world) drops the flag where he stood.
	if (GS->IsCTF())
	{
		HandleFlagCarrierDeath(Killer, Victim);
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
		if (GameType == EIAGameType::TeamDeathmatch)
		{
			if (KillerState->Team == 0) { ++GS->RedScore; }
			else if (KillerState->Team == 1) { ++GS->BlueScore; }
		}
	}
	else if (VictimState)
	{
		// Suicide or falling out of the world costs a point.
		--VictimState->Kills;
		if (GameType == EIAGameType::TeamDeathmatch)
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

	if (GameType == EIAGameType::Survival)
	{
		// No respawns during a wave: the squad is revived when the wave is cleared.
		CheckWaveState(Victim);
		return;
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

	if (GameType == EIAGameType::Survival)
	{
		FinishMatch(TEXT("Time is up!"), -1, 1);   // the waves were not all cleared in time
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
	GetWorldTimerManager().ClearTimer(WaveTimer);
	bWaveActive = false;
	if (CampaignMatch < 0)   // a campaign match waits for the player's choice (continue, retry, menu)
	{
		GetWorldTimerManager().SetTimer(RestartTimer, this, &AIAGameMode::StartNewMatch, RestartDelay, false);
	}

	ReportCampaignResult(WinnerPlayerId, WinnerTeam);
}

void AIAGameMode::ReportCampaignResult(int32 WinnerPlayerId, uint8 WinnerTeam)
{
	UGameInstance* Instance = GetGameInstance();
	UIACampaignSubsystem* Camp = (CampaignMatch >= 0 && Instance) ? Instance->GetSubsystem<UIACampaignSubsystem>() : nullptr;
	if (!Camp)
	{
		return;
	}

	// The human of a campaign match is the one player who is not a bot.
	const AIAPlayerState* Human = nullptr;
	if (GameState)
	{
		for (APlayerState* Other : GameState->PlayerArray)
		{
			const AIAPlayerState* State = Cast<AIAPlayerState>(Other);
			if (State && !State->bIsBotPlayer) { Human = State; break; }
		}
	}
	const AIAGameState* GS = GetGameState<AIAGameState>();
	if (!Human || !GS)
	{
		return;
	}

	const bool bTeamGame = GS->IsTeamGame();
	const bool bWon = bTeamGame ? (WinnerTeam == Human->Team) : (WinnerPlayerId == Human->GetPlayerId());

	// Match score of both sides: team score, or the human's kills against the best opponent's.
	int32 Mine = 0;
	int32 Theirs = 0;
	if (bTeamGame)
	{
		Mine = Human->Team == 0 ? GS->RedScore : GS->BlueScore;
		Theirs = Human->Team == 0 ? GS->BlueScore : GS->RedScore;
	}
	else
	{
		Mine = Human->Kills;
		for (APlayerState* Other : GS->PlayerArray)
		{
			if (const AIAPlayerState* State = Cast<AIAPlayerState>(Other))
			{
				if (State != Human) { Theirs = FMath::Max(Theirs, State->Kills); }
			}
		}
	}

	int32 Stars = 0;
	if (bWon)
	{
		Stars = 1;
		if (Mine * 2 >= Theirs * 3) { ++Stars; }   // a clear win: at least 1.5 times the opponent's score
		const FIABonusGoal& Goal = IACampaign::Matches()[CampaignMatch].Bonus;
		bool bBonus = false;
		switch (Goal.Kind)
		{
		case EIABonus::MaxDeaths:     bBonus = Human->Deaths <= Goal.Value; break;
		case EIABonus::MinAccuracy:   bBonus = Human->GetAccuracy() >= Goal.Value; break;
		case EIABonus::MinStreak:     bBonus = Human->BestStreak >= Goal.Value; break;
		case EIABonus::MinKills:      bBonus = Human->Kills >= Goal.Value; break;
		case EIABonus::MinCaptures:   bBonus = Human->Captures >= Goal.Value; break;
		case EIABonus::MaxEnemyScore: bBonus = Theirs <= Goal.Value; break;
		case EIABonus::MinMargin:     bBonus = Mine - Theirs >= Goal.Value; break;
		}
		if (bBonus) { ++Stars; }
	}
	UE_LOG(LogInstagib, Log, TEXT("Campaign: match %d %s (%d : %d), %d stars"), CampaignMatch + 1, bWon ? TEXT("won") : TEXT("lost"), Mine, Theirs, Stars);
	Camp->RecordResult(CampaignMatch, bWon, Stars);
}

// ---------------------------------------------------------------- survival

int32 AIAGameMode::CountAlive(uint8 Team, const AController* Ignore) const
{
	int32 Count = 0;
	for (TActorIterator<AIAPlayerCharacter> It(GetWorld()); It; ++It)
	{
		const AIAPlayerCharacter* Body = *It;
		const AController* C = Body->GetController();
		const AIAPlayerState* State = C ? C->GetPlayerState<AIAPlayerState>() : nullptr;
		if (!State || C == Ignore || Body->IsDead() || Body->IsPendingKillPending() || State->Team != Team)
		{
			continue;
		}
		++Count;
	}
	return Count;
}

void AIAGameMode::ClearEnemyControllers()
{
	TArray<AController*> Enemies;
	for (FConstControllerIterator It = GetWorld()->GetControllerIterator(); It; ++It)
	{
		AController* C = It->Get();
		const AIAPlayerState* State = C ? C->GetPlayerState<AIAPlayerState>() : nullptr;
		if (State && State->bIsBotPlayer && State->Team == 1)
		{
			Enemies.Add(C);
		}
	}
	for (AController* C : Enemies)
	{
		if (APawn* Body = C->GetPawn())
		{
			C->UnPossess();
			Body->Destroy();
		}
		C->Destroy();
	}
}

void AIAGameMode::SpawnWaveBot(int32 Slot, int32 Look)
{
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AIABotController* Bot = GetWorld()->SpawnActor<AIABotController>(AIABotController::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);
	if (!Bot)
	{
		return;
	}
	Bot->SetSkill(static_cast<EIABotSkill>(BotSkill));
	if (AIAPlayerState* PS = Bot->GetPlayerState<AIAPlayerState>())
	{
		PS->SetPlayerName(IACharacters::GetLook(Look).Name);
		PS->bIsBotPlayer = true;
		PS->SlotId = NextSlotId++;
		PS->CharacterIndex = Look;
		PS->Team = 1;
	}
	RestartPlayer(Bot);
	BeginSpawnProtection(Bot->GetPawn());
}

void AIAGameMode::StartWave(int32 Wave)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || GS->Phase != EIAMatchPhase::Live)
	{
		return;
	}

	WaveNumber = Wave;
	bWaveActive = false;
	ClearEnemyControllers();

	// The squad is whole again: everybody who fell gets a body.
	TArray<AController*> Fallen;
	for (FConstControllerIterator It = GetWorld()->GetControllerIterator(); It; ++It)
	{
		AController* C = It->Get();
		const AIAPlayerState* State = C ? C->GetPlayerState<AIAPlayerState>() : nullptr;
		if (State && State->Team == 0 && !C->GetPawn())
		{
			Fallen.Add(C);
		}
	}
	for (AController* C : Fallen)
	{
		RestartPlayer(C);
		BeginSpawnProtection(C->GetPawn());
	}

	// Each wave has one more enemy than the last, at most 10 at a time.
	const int32 Count = FMath::Clamp(SurvivalEnemyBase + (Wave - 1), 1, 10);
	TArray<int32> Looks = SurvivalEnemyLooks;
	if (Looks.IsEmpty())
	{
		for (int32 I = 0; I < IACharacters::LookCount; ++I) { Looks.Add(I); }
		Algo::RandomShuffle(Looks);
	}
	for (int32 I = 0; I < Count; ++I)
	{
		SpawnWaveBot(I, Looks[I % Looks.Num()]);
	}

	bWaveActive = true;
	GS->Wave = Wave;
	GS->WaveEnemiesLeft = Count;
	GS->BlueScore = Count;
	UE_LOG(LogInstagib, Log, TEXT("Survival: wave %d of %d starts with %d enemies"), Wave, ScoreLimit, Count);

	for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
	{
		if (AIAPlayerController* PC = Cast<AIAPlayerController>(It->Get()))
		{
			PC->ClientShowMessage(FString::Printf(TEXT("WAVE %d OF %d"), Wave, FMath::Max(ScoreLimit, Wave)), FLinearColor(1.f, 0.55f, 0.1f), 2.5f);
		}
	}
}

void AIAGameMode::CheckWaveState(AController* JustDied)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || GS->Phase != EIAMatchPhase::Live || !bWaveActive)
	{
		return;
	}

	const int32 EnemiesLeft = CountAlive(1, JustDied);
	GS->WaveEnemiesLeft = EnemiesLeft;
	GS->BlueScore = EnemiesLeft;

	// The whole squad is down: the match is lost.
	if (CountAlive(0, JustDied) <= 0)
	{
		FinishMatch(TEXT("The squad is down!"), -1, 1);
		return;
	}

	if (EnemiesLeft > 0)
	{
		return;
	}

	// Wave cleared.
	bWaveActive = false;
	++GS->RedScore;
	GS->WaveEnemiesLeft = 0;
	UE_LOG(LogInstagib, Log, TEXT("Survival: wave %d cleared (%d of %d)"), WaveNumber, GS->RedScore, ScoreLimit);
	if (WaveNumber >= ScoreLimit)
	{
		FinishMatch(TEXT("Every wave survived!"), -1, 0);
		return;
	}
	for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
	{
		if (AIAPlayerController* PC = Cast<AIAPlayerController>(It->Get()))
		{
			PC->ClientShowMessage(TEXT("WAVE CLEARED"), FLinearColor(0.4f, 1.f, 0.5f), 2.5f);
		}
	}
	const int32 Next = WaveNumber + 1;
	const int32 Generation = MatchGeneration;
	GetWorldTimerManager().SetTimer(WaveTimer, FTimerDelegate::CreateLambda([this, Next, Generation]()
	{
		if (Generation == MatchGeneration) { StartWave(Next); }
	}), 4.f, false);
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

	// Capture the flag: a team spawns at its own tagged starts (and at untagged ones), never next to the enemy flag.
	// Free for all and team deathmatch use every start.
	const bool bCtfSpawn = GS && GS->IsCTF() && MyState && MyState->Team < 2;
	if (bCtfSpawn)
	{
		TArray<APlayerStart*> Usable;
		for (APlayerStart* Start : Starts)
		{
			const uint8 StartTeam = GetStartTeam(Start);
			if (StartTeam == IA_NoTeam || StartTeam == MyState->Team)
			{
				Usable.Add(Start);
			}
		}
		if (!Usable.IsEmpty())
		{
			Starts = Usable;
		}
	}
	const AIAFlagBase* EnemyBase = bCtfSpawn ? Bases[1 - MyState->Team].Get() : nullptr;

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
		if (bCtfSpawn)
		{
			if (GetStartTeam(Start) == MyState->Team) { Score += 25.f; }
			if (EnemyBase && FVector::Dist2D(Start->GetActorLocation(), EnemyBase->GetActorLocation()) < 1100.f)
			{
				Score -= 400.f;   // not next to the flag the team is trying to steal
			}
		}
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

// ---------------------------------------------------------------- capture the flag

uint8 AIAGameMode::GetStartTeam(const APlayerStart* Start) const
{
	if (!Start)
	{
		return IA_NoTeam;
	}
	const FName Tag = Start->PlayerStartTag;
	if (Tag == FName(TEXT("Red"))) { return 0; }
	if (Tag == FName(TEXT("Blue"))) { return 1; }
	if (const uint8* Team = FallbackStartTeam.Find(TWeakObjectPtr<const APlayerStart>(Start)))
	{
		return *Team;
	}
	return IA_NoTeam;
}

void AIAGameMode::SetupCTF()
{
	if (GameType != EIAGameType::CaptureTheFlag || bCtfSetUp)
	{
		return;
	}
	bCtfSetUp = true;

	for (TActorIterator<AIAFlagBase> It(GetWorld()); It; ++It)
	{
		if (It->FlagTeam < 2 && !Bases[It->FlagTeam].IsValid())
		{
			Bases[It->FlagTeam] = *It;
		}
	}
	if (!Bases[0].IsValid() || !Bases[1].IsValid())
	{
		CreateFallbackBases();
	}
	for (int32 Team = 0; Team < 2; ++Team)
	{
		if (Bases[Team].IsValid())
		{
			Flags[Team] = Bases[Team]->SpawnFlag();
		}
	}
	UE_LOG(LogInstagib, Log, TEXT("CTF: setup done on %s: red base %s, blue base %s"), *GetWorld()->GetMapName(),
		Bases[0].IsValid() ? *Bases[0]->GetActorLocation().ToCompactString() : TEXT("none"),
		Bases[1].IsValid() ? *Bases[1]->GetActorLocation().ToCompactString() : TEXT("none"));
}

void AIAGameMode::ResetFlags()
{
	for (int32 Team = 0; Team < 2; ++Team)
	{
		if (AIAFlag* Flag = Flags[Team].Get())
		{
			Flag->ServerReturnHome();
		}
	}
}

bool AIAGameMode::FindFlatSpot(const FVector& Around, float FloorZ, FVector& OutSpot) const
{
	UWorld* World = GetWorld();
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CtfBaseSpot), false);

	// The floor below a point: flat, and at the height of the starts (not the top of a crate or a ledge).
	auto Floor = [&](const FVector& P, FVector& OutFloor) -> bool
	{
		FHitResult Hit;
		if (!World->LineTraceSingleByChannel(Hit, FVector(P.X, P.Y, FloorZ + 120.f), FVector(P.X, P.Y, FloorZ - 250.f), ECC_Visibility, Params))
		{
			return false;
		}
		if (Hit.ImpactNormal.Z < 0.97f || FMath::Abs(Hit.ImpactPoint.Z - FloorZ) > 40.f)
		{
			return false;
		}
		OutFloor = Hit.ImpactPoint;
		return true;
	};

	static const float Rings[] = { 0.f, 150.f, 300.f, 450.f, 600.f, 800.f, 1000.f };
	for (int32 Ring = 0; Ring < UE_ARRAY_COUNT(Rings); ++Ring)
	{
		const int32 Steps = Ring == 0 ? 1 : 12;
		for (int32 Step = 0; Step < Steps; ++Step)
		{
			const float Angle = FMath::DegreesToRadians(Step * 360.f / Steps + Ring * 17.f);
			const FVector P = Around + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.f) * Rings[Ring];
			FVector Centre;
			if (!Floor(P, Centre))
			{
				continue;
			}
			// The whole pad must be flat ...
			bool bFlat = true;
			for (int32 K = 0; K < 8 && bFlat; ++K)
			{
				const float A = K * UE_TWO_PI / 8.f;
				FVector Edge;
				bFlat = Floor(Centre + FVector(FMath::Cos(A), FMath::Sin(A), 0.f) * 200.f, Edge) && FMath::Abs(Edge.Z - Centre.Z) < 25.f;
			}
			// ... and free of walls and props.
			if (bFlat && World->OverlapBlockingTestByChannel(Centre + FVector(0.f, 0.f, 135.f), FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(110.f, 100.f), Params))
			{
				bFlat = false;
			}
			if (bFlat)
			{
				OutSpot = Centre;
				return true;
			}
		}
	}
	return false;
}

void AIAGameMode::SpawnBaseActor(uint8 Team, const FVector& Location, bool bFallback)
{
	const FTransform Transform(FRotator::ZeroRotator, Location);
	AIAFlagBase* Base = GetWorld()->SpawnActorDeferred<AIAFlagBase>(AIAFlagBase::StaticClass(), Transform, nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
	if (Base)
	{
		Base->FlagTeam = Team;
		Base->bFallback = bFallback;
		Base->FinishSpawning(Transform);
		Bases[Team] = Base;
	}
}

void AIAGameMode::CreateFallbackBases()
{
	UWorld* World = GetWorld();
	TArray<APlayerStart*> Starts;
	for (TActorIterator<APlayerStart> It(World); It; ++It)
	{
		Starts.Add(*It);
	}
	UE_LOG(LogInstagib, Log, TEXT("CTF: FALLBACK BASES on %s (red base %s, blue base %s on the map), %d player starts"), *World->GetMapName(),
		Bases[0].IsValid() ? TEXT("placed") : TEXT("missing"), Bases[1].IsValid() ? TEXT("placed") : TEXT("missing"), Starts.Num());

	// Two groups of starts: by their tags when the map has both, else the two farthest apart.
	TArray<APlayerStart*> Group[2];
	for (APlayerStart* Start : Starts)
	{
		const uint8 Team = GetStartTeam(Start);
		if (Team < 2) { Group[Team].Add(Start); }
	}
	if (Group[0].IsEmpty() || Group[1].IsEmpty())
	{
		Group[0].Reset();
		Group[1].Reset();
		if (Starts.Num() >= 2)
		{
			float BestDistance = -1.f;
			int32 A = 0, B = 1;
			for (int32 I = 0; I < Starts.Num(); ++I)
			{
				for (int32 J = I + 1; J < Starts.Num(); ++J)
				{
					const float D = FVector::Dist2D(Starts[I]->GetActorLocation(), Starts[J]->GetActorLocation())
						+ 0.25f * FMath::Abs(Starts[I]->GetActorLocation().Z - Starts[J]->GetActorLocation().Z);
					if (D > BestDistance) { BestDistance = D; A = I; B = J; }
				}
			}
			for (APlayerStart* Start : Starts)
			{
				const float ToA = FVector::Dist2D(Start->GetActorLocation(), Starts[A]->GetActorLocation());
				const float ToB = FVector::Dist2D(Start->GetActorLocation(), Starts[B]->GetActorLocation());
				const uint8 Team = ToA <= ToB ? 0 : 1;
				Group[Team].Add(Start);
				FallbackStartTeam.Add(TWeakObjectPtr<const APlayerStart>(Start), Team);
			}
		}
		else if (Starts.Num() == 1)
		{
			Group[0].Add(Starts[0]);
			Group[1].Add(Starts[0]);
		}
	}

	for (int32 Team = 0; Team < 2; ++Team)
	{
		if (Bases[Team].IsValid())
		{
			continue;
		}
		FVector Anchor = Team == 0 ? FVector(-1500.f, 0.f, 100.f) : FVector(1500.f, 0.f, 100.f);
		if (!Group[Team].IsEmpty())
		{
			FVector Centroid = FVector::ZeroVector;
			for (const APlayerStart* Start : Group[Team]) { Centroid += Start->GetActorLocation(); }
			Centroid /= Group[Team].Num();
			float Nearest = FLT_MAX;
			for (const APlayerStart* Start : Group[Team])
			{
				const float D = FVector::Dist(Start->GetActorLocation(), Centroid);
				if (D < Nearest) { Nearest = D; Anchor = Start->GetActorLocation(); }
			}
			if (Group[0].Num() == 1 && Group[1].Num() == 1 && Group[0][0] == Group[1][0] && Team == 1)
			{
				Anchor += FVector(1500.f, 0.f, 0.f);   // one start on the whole map: the second base goes next to it
			}
		}

		// The floor under the start, then the closest flat free spot around it.
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(CtfBaseFloor), false);
		float FloorZ = Anchor.Z - 90.f;
		if (World->LineTraceSingleByChannel(Hit, Anchor + FVector(0.f, 0.f, 50.f), Anchor - FVector(0.f, 0.f, 700.f), ECC_Visibility, Params))
		{
			FloorZ = Hit.ImpactPoint.Z;
		}
		FVector Spot(Anchor.X, Anchor.Y, FloorZ);
		const bool bFlat = FindFlatSpot(FVector(Anchor.X, Anchor.Y, FloorZ), FloorZ, Spot);
		UE_LOG(LogInstagib, Log, TEXT("CTF: fallback %s base at %s (%s, %d starts in the group)"), Team == 0 ? TEXT("red") : TEXT("blue"),
			*Spot.ToCompactString(), bFlat ? TEXT("flat spot") : TEXT("no flat spot, using the floor under the start"), Group[Team].Num());
		SpawnBaseActor(static_cast<uint8>(Team), Spot, true);
	}
}

void AIAGameMode::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (GameType == EIAGameType::CaptureTheFlag)
	{
		TickFlags();
	}
}

void AIAGameMode::TickFlags()
{
	const AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || GS->Phase != EIAMatchPhase::Live)
	{
		return;
	}
	UWorld* World = GetWorld();

	TArray<AIAPlayerCharacter*> Players;
	for (TActorIterator<AIAPlayerCharacter> It(World); It; ++It)
	{
		AIAPlayerCharacter* P = *It;
		const AIAPlayerState* PS = P->GetPlayerState<AIAPlayerState>();
		if (!P->IsDead() && !P->IsPendingKillPending() && PS && PS->Team < 2)
		{
			Players.Add(P);
		}
	}

	auto Touches = [this](const AActor* Pawn, const FVector& Where)
	{
		const FVector D = Pawn->GetActorLocation() - Where;
		return FVector2D(D.X, D.Y).SizeSquared() <= FMath::Square(FlagTouchRadius) && D.Z > -90.f && D.Z < 260.f;
	};

	for (int32 Team = 0; Team < 2; ++Team)
	{
		AIAFlag* Flag = Flags[Team].Get();
		if (!Flag)
		{
			continue;
		}

		if (Flag->GetFlagState() == EIAFlagState::Carried)
		{
			AIAPlayerCharacter* Carrier = Cast<AIAPlayerCharacter>(Flag->GetCarrier());
			AIAPlayerState* CarrierState = Carrier ? Carrier->GetPlayerState<AIAPlayerState>() : nullptr;
			if (!Carrier || Carrier->IsDead() || Carrier->IsPendingKillPending() || !CarrierState)
			{
#if !UE_BUILD_SHIPPING
				if (bDevDemoCarrier && Carrier && !Carrier->IsDead())
				{
					continue;   // the screenshot dummy carries the flag without a player
				}
#endif
				// The carrier vanished without dying through the game (disconnect, level change): drop it where he was.
				UE_LOG(LogInstagib, Log, TEXT("CTF: the carrier of the %s flag is gone"), Team == 0 ? TEXT("red") : TEXT("blue"));
				DropFlag(Flag, Flag->GetLastCarrierLocation(), nullptr);
				continue;
			}

			// A bot that cannot get anywhere with the flag must not hold up the game.
			if (CarrierState->bIsBotPlayer && Flag->GetCarriedSeconds() > 110.f)
			{
				UE_LOG(LogInstagib, Warning, TEXT("CTF: BOT CARRY TIMEOUT: %s held the %s flag for %.0f s, the flag goes home"),
					*CarrierState->GetPlayerName(), Team == 0 ? TEXT("red") : TEXT("blue"), Flag->GetCarriedSeconds());
				ReturnFlag(Flag, nullptr);
				continue;
			}

			// Capture: touch the own base while the own flag is at home.
			const uint8 CarrierTeam = CarrierState->Team;
			AIAFlag* OwnFlag = CarrierTeam < 2 ? Flags[CarrierTeam].Get() : nullptr;
			const AIAFlagBase* OwnBase = CarrierTeam < 2 ? Bases[CarrierTeam].Get() : nullptr;
			if (OwnFlag && OwnFlag->IsHome() && OwnBase)
			{
				const FVector D = Carrier->GetActorLocation() - OwnBase->GetActorLocation();
				if (FVector2D(D.X, D.Y).SizeSquared() <= FMath::Square(OwnBase->CaptureRadius) && D.Z > -90.f && D.Z < 300.f)
				{
					CaptureFlag(Flag, Carrier);
				}
			}
			continue;
		}

		// At home or on the ground.
		if (Flag->GetFlagState() == EIAFlagState::Dropped && Flag->GetDropSecondsLeft() <= 0.f)
		{
			UE_LOG(LogInstagib, Log, TEXT("CTF: the dropped %s flag returns by itself"), Team == 0 ? TEXT("red") : TEXT("blue"));
			ReturnFlag(Flag, nullptr);
			continue;
		}
		for (AIAPlayerCharacter* P : Players)
		{
			if (!Touches(P, Flag->GetRestLocation()))
			{
				continue;
			}
			AIAPlayerState* PS = P->GetPlayerState<AIAPlayerState>();
			if (PS->Team == Team)
			{
				if (Flag->GetFlagState() == EIAFlagState::Dropped)
				{
					ReturnFlag(Flag, PS);
					break;
				}
			}
			else
			{
				PickUpFlag(Flag, P);
				break;
			}
		}
	}
}

void AIAGameMode::PickUpFlag(AIAFlag* Flag, AIAPlayerCharacter* Taker)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	AIAPlayerState* PS = Taker ? Taker->GetPlayerState<AIAPlayerState>() : nullptr;
	if (!Flag || !GS || !PS)
	{
		return;
	}
	Flag->ServerPickUp(Taker);
	GS->MulticastFlagEvent(EIAFlagEvent::Taken, PS->SlotId, Flag->GetFlagTeam());
	UE_LOG(LogInstagib, Log, TEXT("CTF: %s took the %s flag"), *PS->GetPlayerName(), Flag->GetFlagTeam() == 0 ? TEXT("red") : TEXT("blue"));
}

void AIAGameMode::DropFlag(AIAFlag* Flag, const FVector& Where, AIAPlayerState* ExCarrier)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!Flag || !GS)
	{
		return;
	}
	const bool bDropped = Flag->ServerDrop(Where, FlagReturnSeconds);
	GS->MulticastFlagEvent(bDropped ? EIAFlagEvent::Dropped : EIAFlagEvent::Returned, bDropped && ExCarrier ? ExCarrier->SlotId : -1, Flag->GetFlagTeam());
	UE_LOG(LogInstagib, Log, TEXT("CTF: the %s flag was %s%s%s"), Flag->GetFlagTeam() == 0 ? TEXT("red") : TEXT("blue"),
		bDropped ? TEXT("dropped at ") : TEXT("sent home (no safe floor at "), *Where.ToCompactString(), bDropped ? TEXT("") : TEXT(")"));
}

void AIAGameMode::ReturnFlag(AIAFlag* Flag, AIAPlayerState* Returner)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!Flag || !GS)
	{
		return;
	}
	Flag->ServerReturnHome();
	if (Returner)
	{
		++Returner->Returns;
	}
	GS->MulticastFlagEvent(EIAFlagEvent::Returned, Returner ? Returner->SlotId : -1, Flag->GetFlagTeam());
	UE_LOG(LogInstagib, Log, TEXT("CTF: the %s flag is home again%s%s"), Flag->GetFlagTeam() == 0 ? TEXT("red") : TEXT("blue"),
		Returner ? TEXT(", returned by ") : TEXT(""), Returner ? *Returner->GetPlayerName() : TEXT(""));
}

void AIAGameMode::CaptureFlag(AIAFlag* Flag, AIAPlayerCharacter* Carrier)
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	AIAPlayerState* PS = Carrier ? Carrier->GetPlayerState<AIAPlayerState>() : nullptr;
	if (!Flag || !GS || !PS || PS->Team > 1)
	{
		return;
	}
	if (PS->Team == 0) { ++GS->RedScore; } else { ++GS->BlueScore; }
	++PS->Captures;
	Flag->ServerReturnHome();
	GS->MulticastFlagEvent(EIAFlagEvent::Captured, PS->SlotId, Flag->GetFlagTeam());
	UE_LOG(LogInstagib, Log, TEXT("CTF: %s CAPTURED the %s flag (red %d : blue %d)"), *PS->GetPlayerName(),
		Flag->GetFlagTeam() == 0 ? TEXT("red") : TEXT("blue"), GS->RedScore, GS->BlueScore);

	CheckScoreLimit();
	if (GS->Phase == EIAMatchPhase::Live)
	{
		UpdateLeadStates();
		CheckFragsLeft();
	}
}

void AIAGameMode::HandleFlagCarrierDeath(AController* Killer, AController* Victim)
{
	APawn* VictimPawn = Victim ? Victim->GetPawn() : nullptr;
	AIAFlag* Flag = AIAFlag::FindCarriedBy(GetWorld(), VictimPawn);
	if (!Flag)
	{
		return;
	}
	AIAPlayerState* VictimState = Victim->GetPlayerState<AIAPlayerState>();
	AIAPlayerState* KillerState = Killer ? Killer->GetPlayerState<AIAPlayerState>() : nullptr;
	if (KillerState && Killer != Victim && VictimState && KillerState->Team != VictimState->Team)
	{
		++KillerState->FlagKills;
	}
	DropFlag(Flag, VictimPawn->GetActorLocation(), VictimState);
}

void AIAGameMode::Logout(AController* Exiting)
{
	if (GameType == EIAGameType::CaptureTheFlag && Exiting)
	{
		if (APawn* Pawn = Exiting->GetPawn())
		{
			if (AIAFlag* Flag = AIAFlag::FindCarriedBy(GetWorld(), Pawn))
			{
				DropFlag(Flag, Pawn->GetActorLocation(), Exiting->GetPlayerState<AIAPlayerState>());
			}
		}
	}
	Super::Logout(Exiting);
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

	// -IACtfForce=S[,T]: S seconds after the fight starts the first human (else the first bot) of team T (default red = 0)
	// takes the enemy flag. -IACtfDrop=S: S seconds after the fight starts every carried flag is dropped where its carrier stands.
	// -IACtfCapture=S: S seconds after the fight starts the carrier (if any) is moved to his base: instant capture test.
	FString ForceText;
	const bool bForce = FParse::Value(FCommandLine::Get(), TEXT("IACtfForce="), ForceText, /*bShouldStopOnSeparator*/ false) && IsCTF();
	float CtfDropAt = 0.f;
	const bool bCtfDrop = FParse::Value(FCommandLine::Get(), TEXT("IACtfDrop="), CtfDropAt) && IsCTF();
	float CtfCaptureAt = 0.f;
	const bool bCtfCapture = FParse::Value(FCommandLine::Get(), TEXT("IACtfCapture="), CtfCaptureAt) && IsCTF();
	// -IACtfCarryDemo=dx,dy,yaw: a body without a player (like the showroom ones) stands dx,dy from the red base and carries the
	// red flag for ever, for screenshots of the carried flag (the match goes on around it).
	FString DemoText;
	const bool bCarryDemo = FParse::Value(FCommandLine::Get(), TEXT("IACtfCarryDemo="), DemoText, /*bShouldStopOnSeparator*/ false) && IsCTF();
	if (!bFake && !bKillMe && !bProbe && !bForce && !bCtfDrop && !bCtfCapture && !bCarryDemo)
	{
		return;
	}

	const float StartDelay = WarmupSeconds + 1.f;
	if (bCarryDemo)
	{
		TArray<FString> Parts;
		DemoText.ParseIntoArray(Parts, TEXT(","));
		const FVector Offset(Parts.Num() > 0 ? FCString::Atof(*Parts[0]) : 400.f, Parts.Num() > 1 ? FCString::Atof(*Parts[1]) : 0.f, 0.f);
		const float Yaw = Parts.Num() > 2 ? FCString::Atof(*Parts[2]) : 0.f;
		FTimerHandle Handle;
		GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this, Offset, Yaw]()
		{
			const AIAFlagBase* Base = Bases[0].Get();
			AIAFlag* Flag = Flags[0].Get();
			if (!Base || !Flag)
			{
				return;
			}
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			AIAPlayerCharacter* Body = GetWorld()->SpawnActor<AIAPlayerCharacter>(AIAPlayerCharacter::StaticClass(),
				Base->GetActorLocation() + Offset + FVector(0.f, 0.f, 100.f), FRotator(0.f, Yaw, 0.f), Params);
			if (Body)
			{
				Body->SetForcedLook(3, 1);
				Flag->ServerPickUp(Body);
				bDevDemoCarrier = true;
			}
		}), StartDelay + 0.5f, false);
	}
	if (bForce)
	{
		TArray<FString> Parts;
		ForceText.ParseIntoArray(Parts, TEXT(","));
		const float At = Parts.Num() > 0 ? FCString::Atof(*Parts[0]) : 3.f;
		const int32 Team = Parts.Num() > 1 ? FMath::Clamp(FCString::Atoi(*Parts[1]), 0, 1) : 0;
		FTimerHandle Handle;
		GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this, Team]()
		{
			AIAPlayerCharacter* Pick = nullptr;
			for (TActorIterator<AIAPlayerCharacter> It(GetWorld()); It; ++It)
			{
				const AIAPlayerState* PS = It->GetPlayerState<AIAPlayerState>();
				if (It->IsDead() || !PS || PS->Team != Team) { continue; }
				if (!Pick || (Pick->GetPlayerState<AIAPlayerState>()->bIsBotPlayer && !PS->bIsBotPlayer)) { Pick = *It; }
			}
			AIAFlag* Enemy = Flags[1 - Team].Get();
			if (Pick && Enemy && Enemy->IsHome())
			{
				PickUpFlag(Enemy, Pick);
			}
		}), StartDelay + At, false);
	}
	if (bCtfDrop)
	{
		FTimerHandle Handle;
		GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this]()
		{
			for (int32 Team = 0; Team < 2; ++Team)
			{
				AIAFlag* Flag = Flags[Team].Get();
				if (Flag && Flag->GetFlagState() == EIAFlagState::Carried && Flag->GetCarrier())
				{
					DropFlag(Flag, Flag->GetCarrier()->GetActorLocation(), Flag->GetCarrier()->GetPlayerState<AIAPlayerState>());
				}
			}
		}), StartDelay + CtfDropAt, false);
	}
	if (bCtfCapture)
	{
		FTimerHandle Handle;
		GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this]()
		{
			for (int32 Team = 0; Team < 2; ++Team)
			{
				AIAFlag* Flag = Flags[Team].Get();
				AIAPlayerCharacter* Carrier = Flag ? Cast<AIAPlayerCharacter>(Flag->GetCarrier()) : nullptr;
				const AIAPlayerState* PS = Carrier ? Carrier->GetPlayerState<AIAPlayerState>() : nullptr;
				if (PS && PS->Team < 2 && Bases[PS->Team].IsValid())
				{
					Carrier->SetActorLocation(Bases[PS->Team]->GetActorLocation() + FVector(0.f, 0.f, 100.f), false, nullptr, ETeleportType::TeleportPhysics);
				}
			}
		}), StartDelay + CtfCaptureAt, false);
	}
	if (!bFake && !bKillMe && !bProbe)
	{
		return;
	}

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
