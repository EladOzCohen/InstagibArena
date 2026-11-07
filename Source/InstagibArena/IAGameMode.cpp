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
#include "Engine/World.h"
#include "GameFramework/GameState.h"
#include "Kismet/GameplayStatics.h"
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
	}
}

void AIAGameMode::HandleMatchHasStarted()
{
	Super::HandleMatchHasStarted();

	GetWorldTimerManager().SetTimer(ClockTimer, this, &AIAGameMode::TickClock, 1.f, true);

	if (!bBotsSpawned)
	{
		bBotsSpawned = true;
		SpawnBots();
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
			PS->CharacterIndex = CharacterIndex;
			AssignTeam(PS);
		}

		RestartPlayer(Bot);
	}
}

void AIAGameMode::PostLogin(APlayerController* NewPlayer)
{
	Super::PostLogin(NewPlayer);

	if (AIAPlayerState* PS = NewPlayer ? NewPlayer->GetPlayerState<AIAPlayerState>() : nullptr)
	{
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
	if (!GS || !IsMatchInProgress())
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

void AIAGameMode::OnPlayerKilled(AController* Killer, AController* Victim)
{
	if (!IsMatchInProgress() || !Victim)
	{
		return;
	}

	AIAGameState* GS = GetGameState<AIAGameState>();
	AIAPlayerState* VictimState = Victim->GetPlayerState<AIAPlayerState>();
	AIAPlayerState* KillerState = Killer ? Killer->GetPlayerState<AIAPlayerState>() : nullptr;

	UE_LOG(LogInstagib, Log, TEXT("%s was fragged by %s"),
		VictimState ? *VictimState->GetPlayerName() : TEXT("?"),
		KillerState ? *KillerState->GetPlayerName() : TEXT("the world"));

	// Tell the humans involved what happened.
	{
		const FString VictimName = VictimState ? VictimState->GetPlayerName() : TEXT("?");
		const FString KillerName = KillerState ? KillerState->GetPlayerName() : TEXT("?");
		if (AIAPlayerController* VictimPC = Cast<AIAPlayerController>(Victim))
		{
			if (Killer && Killer != Victim)
			{
				VictimPC->ClientShowMessage(FString::Printf(TEXT("Fragged by %s"), *KillerName), FLinearColor(1.f, 0.25f, 0.2f), 2.5f);
			}
			else
			{
				VictimPC->ClientShowMessage(TEXT("You died"), FLinearColor(0.8f, 0.8f, 0.85f), 2.f);
			}
		}
		if (AIAPlayerController* KillerPC = Cast<AIAPlayerController>(Killer))
		{
			if (Killer != Victim)
			{
				KillerPC->ClientShowMessage(FString::Printf(TEXT("You fragged %s"), *VictimName), FLinearColor(1.f, 0.85f, 0.2f), 2.f);
			}
		}
	}

	if (VictimState)
	{
		++VictimState->Deaths;
	}

	if (Killer && Killer != Victim && KillerState)
	{
		++KillerState->Kills;
		if (GS && GS->IsTeamGame())
		{
			if (KillerState->Team == 0) { ++GS->RedScore; }
			else if (KillerState->Team == 1) { ++GS->BlueScore; }
		}
	}
	else if (VictimState)
	{
		// Suicide or falling out of the world costs a point.
		--VictimState->Kills;
		if (GS && GS->IsTeamGame())
		{
			if (VictimState->Team == 0) { --GS->RedScore; }
			else if (VictimState->Team == 1) { --GS->BlueScore; }
		}
	}

	CheckScoreLimit();

	if (IsMatchInProgress())
	{
		TWeakObjectPtr<AController> WeakVictim(Victim);
		FTimerHandle RespawnHandle;
		GetWorldTimerManager().SetTimer(RespawnHandle, FTimerDelegate::CreateLambda([this, WeakVictim]()
		{
			if (WeakVictim.IsValid() && IsMatchInProgress() && !WeakVictim->GetPawn())
			{
				RestartPlayer(WeakVictim.Get());
			}
		}), RespawnDelay, false);
	}
}

void AIAGameMode::CheckScoreLimit()
{
	AIAGameState* GS = GetGameState<AIAGameState>();
	if (!GS || ScoreLimit <= 0)
	{
		return;
	}

	if (GS->IsTeamGame())
	{
		if (GS->RedScore >= ScoreLimit) { FinishMatch(TEXT("Red team wins!")); }
		else if (GS->BlueScore >= ScoreLimit) { FinishMatch(TEXT("Blue team wins!")); }
		return;
	}

	for (APlayerState* PS : GS->PlayerArray)
	{
		const AIAPlayerState* State = Cast<AIAPlayerState>(PS);
		if (State && State->Kills >= ScoreLimit)
		{
			FinishMatch(FString::Printf(TEXT("%s wins!"), *State->GetPlayerName()));
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
		if (GS->RedScore > GS->BlueScore) { FinishMatch(TEXT("Red team wins!")); }
		else if (GS->BlueScore > GS->RedScore) { FinishMatch(TEXT("Blue team wins!")); }
		else { FinishMatch(TEXT("Draw!")); }
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
		FinishMatch(TEXT("Draw!"));
	}
	else
	{
		FinishMatch(FString::Printf(TEXT("%s wins!"), *Best->GetPlayerName()));
	}
}

void AIAGameMode::FinishMatch(const FString& WinnerText)
{
	if (!IsMatchInProgress())
	{
		return;
	}

	if (AIAGameState* GS = GetGameState<AIAGameState>())
	{
		GS->bMatchOver = true;
		GS->WinnerText = WinnerText;
	}

	GetWorldTimerManager().ClearTimer(ClockTimer);
	EndMatch();
	GetWorldTimerManager().SetTimer(RestartTimer, this, &AIAGameMode::RestartGame, RestartDelay, false);
}
