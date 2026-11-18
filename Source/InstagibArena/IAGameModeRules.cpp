// Instagib Arena
//
// AIAGameMode: the game options that rewards unlock (docs/REWARDS_DESIGN.md 5.5, 5.6), kept apart from the match flow.
//   Mut=lowgrav,slowfinish,hardcore,endless,bigheads   custom game mutators (R1, R2, R3, R4, R6)
//   Variant=dusk|night                                 time of day of the map (M1, applied by IAMapVariant on every machine)
//   Heat=1..5                                          campaign Apex+ (R5), see IARules::HeatRules
// Every option is checked against the unlocks of this machine's profile (the host decides for a listen server).

#include "IAGameMode.h"
#include "IABotController.h"
#include "IACampaignSubsystem.h"
#include "IAPlayerState.h"
#include "IAProfileSubsystem.h"
#include "InstagibArena.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

void AIAGameMode::ReadRewardOptions(const FString& Options)
{
	const UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(this);
	auto Unlocked = [Profile](const FName Id) { return Profile && Profile->IsUnlocked(Id); };

	// Mutators: custom games only (the campaign has its own rules).
	Mutators = 0;
	if (CampaignMatch < 0)
	{
		const uint8 Wanted = IARules::ParseMutators(UGameplayStatics::ParseOption(Options, TEXT("Mut")));
		for (const FIARuleInfo& Rule : IARules::Mutators)
		{
			if (IARules::Has(Wanted, Rule.Flag))
			{
				if (Unlocked(Rule.RewardId)) { Mutators |= static_cast<uint8>(Rule.Flag); }
				else { UE_LOG(LogInstagib, Warning, TEXT("Rules: %s is not unlocked (%s), ignored"), Rule.Name, Rule.RewardId); }
			}
		}
	}
	if (HasMutator(EIAMutator::Endless))
	{
		// Endless Survival replaces the game type: waves until the squad is down, no clock.
		GameType = EIAGameType::Survival;
		ScoreLimit = 0;
		TimeLimitMinutes = 0;
	}

	// Time of day.
	MapVariant = 0;
	const int32 Variant = IARules::ParseVariant(UGameplayStatics::ParseOption(Options, TEXT("Variant")));
	const FString MapName = IARules::MapShortName(GetWorld() ? GetWorld()->GetMapName() : FString());
	if (Variant > 0)
	{
		if (!IARules::MapHasVariants(MapName)) { UE_LOG(LogInstagib, Log, TEXT("Rules: %s has no times of day"), *MapName); }
		else if (!Unlocked(IARules::VariantUnlockId(MapName, Variant))) { UE_LOG(LogInstagib, Warning, TEXT("Rules: %s is not unlocked, day it is"), *IARules::VariantUnlockId(MapName, Variant).ToString()); }
		else { MapVariant = static_cast<uint8>(Variant); }
	}

	// Campaign Heat.
	HeatLevel = 0;
	if (CampaignMatch >= 0)
	{
		const int32 Wanted = FMath::Clamp(UGameplayStatics::GetIntOption(Options, IARules::HeatUrlOption, 0), 0, IARules::MaxHeat);
		const UIACampaignSubsystem* Camp = GetGameInstance() ? GetGameInstance()->GetSubsystem<UIACampaignSubsystem>() : nullptr;
		if (Wanted > 0 && Camp && Camp->IsHeatAvailable())
		{
			HeatLevel = Wanted;
			if (IARules::HeatRules(HeatLevel).bTimePressure)
			{
				TimeLimitMinutes = IARules::HeatTimeLimit(TimeLimitMinutes);
			}
		}
	}

	if (Mutators != 0 || MapVariant != 0 || HeatLevel != 0)
	{
		UE_LOG(LogInstagib, Log, TEXT("Rules: mutators [%s], time of day %s, heat %d"),
			*IARules::MutatorsToString(Mutators), IARules::VariantNames[MapVariant], HeatLevel);
	}
}

float AIAGameMode::SpawnProtectFor(const APawn* Pawn) const
{
	const bool bHuman = Pawn && Cast<APlayerController>(Pawn->GetController());
	return SpawnProtectSeconds * (bHuman ? IARules::HeatRules(HeatLevel).PlayerProtectScale : 1.f);
}

bool AIAGameMode::IsHeatEnemy(const AController* C) const
{
	const AIAPlayerState* State = C ? C->GetPlayerState<AIAPlayerState>() : nullptr;
	if (CampaignMatch < 0 || !State || !State->bIsBotPlayer)
	{
		return false;
	}
	return GameType == EIAGameType::FreeForAll || State->Team == 1;
}

float AIAGameMode::RespawnDelayFor(const AController* Victim) const
{
	return RespawnDelay * (IsHeatEnemy(Victim) ? IARules::HeatRules(HeatLevel).EnemyRespawnScale : 1.f);
}

void AIAGameMode::ApplyHeatToBot(AIABotController* Bot, int32 BaseSkill) const
{
	if (!Bot || HeatLevel <= 0 || !IsHeatEnemy(Bot))
	{
		return;
	}
	const IARules::FHeatRules Rules = IARules::HeatRules(HeatLevel);
	Bot->SetSkill(static_cast<EIABotSkill>(FMath::Clamp(BaseSkill + Rules.EnemySkillBonus, 0, 6)));
	Bot->SetCoordinated(Rules.bCoordinated);
}

int32 AIAGameMode::WaveBotSkill() const
{
	const int32 Ramp = HasMutator(EIAMutator::Endless) ? FMath::Max(0, WaveNumber - 1) / 5 : 0;
	return FMath::Clamp(BotSkill + Ramp, 0, 6);
}

void AIAGameMode::RecordSurvivalWave(int32 WavesCleared) const
{
	if (!HasMutator(EIAMutator::Endless) || WavesCleared <= 0)
	{
		return;
	}
	if (UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(this))
	{
		Profile->SetStatMax(FName(TEXT("BestWave")), WavesCleared);
		Profile->Save();
		UE_LOG(LogInstagib, Log, TEXT("Rules: endless survival, %d waves cleared (best %lld)"), WavesCleared, Profile->GetStat(FName(TEXT("BestWave"))));
	}
}

void AIAGameMode::RecordHeatCleared() const
{
	if (HeatLevel <= 0 || CampaignMatch < 0)
	{
		return;
	}
	if (UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(this))
	{
		Profile->SetStatMax(FName(TEXT("HeatCleared")), HeatLevel);
		Profile->Save();
	}
	if (UIACampaignSubsystem* Camp = GetGameInstance() ? GetGameInstance()->GetSubsystem<UIACampaignSubsystem>() : nullptr)
	{
		Camp->RecordHeatCleared(CampaignMatch, HeatLevel);
	}
	UE_LOG(LogInstagib, Log, TEXT("Campaign: match %d cleared at heat %d"), CampaignMatch + 1, HeatLevel);
}

// ---------------------------------------------------------------- Slow Finish (R2)

bool AIAGameMode::BeginSlowFinish(const FString& WinnerText, int32 WinnerPlayerId, uint8 WinnerTeam)
{
	if (!HasMutator(EIAMutator::SlowFinish) || !bKillContext || bSlowFinishPending)
	{
		return false;
	}
	bSlowFinishPending = true;
	PendingWinnerText = WinnerText;
	PendingWinnerId = WinnerPlayerId;
	PendingWinnerTeam = WinnerTeam;
	// The world settings replicate the dilation, so every machine sees the same slow motion.
	UGameplayStatics::SetGlobalTimeDilation(this, IARules::SlowFinishDilation);
	GetWorldTimerManager().SetTimer(SlowFinishTimer, this, &AIAGameMode::EndSlowFinish,
		IARules::SlowFinishSeconds * IARules::SlowFinishDilation, false);   // timers run in game time
	UE_LOG(LogInstagib, Log, TEXT("Rules: slow finish (%s)"), *WinnerText);
	return true;
}

void AIAGameMode::StopSlowFinish()
{
	GetWorldTimerManager().ClearTimer(SlowFinishTimer);
	if (bSlowFinishPending || !FMath::IsNearlyEqual(UGameplayStatics::GetGlobalTimeDilation(this), 1.f))
	{
		UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
	}
	bSlowFinishPending = false;
}

void AIAGameMode::EndSlowFinish()
{
	const bool bWasPending = bSlowFinishPending;
	StopSlowFinish();
	if (bWasPending)
	{
		FinishMatch(PendingWinnerText, PendingWinnerId, PendingWinnerTeam);
	}
}
