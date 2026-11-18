// Instagib Arena
// The accounting half of UIAProfileSubsystem: per-match collection, anti-farming rules, rank and medals, campaign rewards.
// Rules: docs/REWARDS_DESIGN.md section 11.

#include "IAProfileSubsystem.h"
#include "IACampaignData.h"
#include "IACampaignSubsystem.h"
#include "InstagibArena.h"

void UIAProfileSubsystem::BeginMatch()
{
	Pending = FPending();
}

void UIAProfileSubsystem::RecordKill(float Value, bool bSkilled, float DistanceCm, bool bAirborne)
{
	// Per match: the first 25 counted kills are worth their full value, up to 40 half, then nothing.
	const float Factor = Pending.CountedValue >= 40.f ? 0.f : (Pending.CountedValue >= 25.f ? 0.5f : 1.f);
	++Pending.Raw;
	Pending.CountedValue += Value * Factor;
	Pending.AP += (Value > 0.f ? Value : 0.25f) * Factor;
	if (bSkilled && Factor > 0.f)
	{
		Pending.Air += bAirborne ? 1 : 0;
		Pending.Long += DistanceCm >= 4000.f ? 1 : 0;
	}
}

void UIAProfileSubsystem::ApplyMatch(const FIAMatchSummary& S)
{
	LastGain = FIAMatchGain();
	LastGain.RankBefore = GetRank();
	const int64 ApBefore = GetAP();
	const FPending Got = Pending;
	Pending = FPending();

	const bool bLongEnough = S.DurationSec >= 120.f || S.CampaignMatch >= 0;
	if (!bLongEnough)
	{
		LastGain.Note = TEXT("This match was too short to count towards rewards.");
		LastGain.RankAfter = LastGain.RankBefore;
		UE_LOG(LogInstagib, Log, TEXT("Profile: match too short (%.0f s), not counted"), S.DurationSec);
		return;
	}
	LastGain.bCounted = true;

	const bool bSkilledOpponent = S.bHumanOpponents || S.BotSkill >= 2;
	const bool bValidWin = S.bWon && bSkilledOpponent && (S.Opponents >= 2 || S.BotSkill >= 4 || S.bHumanOpponents);

	AddStat("Matches");
	AddStat("Deaths", S.Deaths);
	AddStat("KillsRaw", Got.Raw);
	// Fractional kills are kept in hundredths.
	const int64 Hundredths = FMath::RoundToInt(Got.CountedValue * 100.f) + GetStat("KillsFrac");
	AddStat("KillsCounted", Hundredths / 100);
	Stats.Add("KillsFrac", Hundredths % 100);
	LastGain.CountedKills = static_cast<int32>(Hundredths / 100);
	AddStat("AirKills", Got.Air);
	AddStat("LongKills", Got.Long);

	float AP = Got.AP;
	if (S.bWon)
	{
		if (bValidWin)
		{
			AddStat("Wins");
			AddStat(FName(*FString::Printf(TEXT("WonMap_%s"), *S.MapName)));
			AP += (S.BotSkill >= 4 || S.bHumanOpponents) ? 40.f : 20.f;
			int32 MapsWon = 0;
			for (const TPair<FName, int64>& Pair : Stats)
			{
				MapsWon += (Pair.Key.ToString().StartsWith(TEXT("WonMap_")) && Pair.Value > 0) ? 1 : 0;
			}
			Stats.Add("MapsWon", MapsWon);
		}
		Stats.Add("LossStreak", 0);
	}
	else
	{
		AddStat("Losses");
		AddStat("LossStreak");
		SetStatMax("MaxLossStreak", GetStat("LossStreak"));
	}
	if (bSkilledOpponent)
	{
		if (S.Deaths == 0 && S.bWon && S.Kills >= 5) { AddStat("Flawless"); }
		const float Accuracy = S.ShotsFired > 0 ? 100.f * S.ShotsHit / S.ShotsFired : 0.f;
		if (S.Kills >= 10 && Accuracy >= 40.f) { AddStat("SharpMatches"); }
		AddStat("Captures", S.Captures);
		AddStat("Guards", S.Returns + S.FlagKills);
		AP += S.Captures * 10.f + (S.Returns + S.FlagKills) * 3.f;
		SetStatMax("BestStreak", S.BestStreak);
	}
	if (S.Wave > 0)   // survival: the waves before the one that ended the run were cleared
	{
		const int32 Cleared = FMath::Max(0, S.bWon ? S.Wave : S.Wave - 1);
		if (bSkilledOpponent) { AddStat("SurvWaves", Cleared); }
		AP += Cleared * 5.f;
		SetStatMax("BestWave", S.Wave);
	}

	AddStat("AP", FMath::RoundToInt(AP));
	EvaluateRewards();
	LastGain.AP = static_cast<int32>(GetAP() - ApBefore);
	LastGain.RankAfter = GetRank();
	NewUnlocks.Reset();
	Save();
	UE_LOG(LogInstagib, Log, TEXT("Profile: match counted, +%d AP (total %lld), rank %d, kills counted %d, %d new rewards, %d new medal tiers"),
		LastGain.AP, GetAP(), LastGain.RankAfter, LastGain.CountedKills, LastGain.NewRewards.Num(), LastGain.NewMedals.Num());
}

void UIAProfileSubsystem::EvaluateRewards()
{
	// Counter rewards.
	for (const IAReward::FReward& R : IAReward::All())
	{
		if (!R.Stat.IsEmpty() && !Unlocked.Contains(R.Id) && GetStat(*R.Stat) >= R.Threshold)
		{
			if (Unlock(R.Id)) { LastGain.NewRewards.Add(R.Id); }
		}
	}
	// Medal tiers: a new tier gives apex points.
	const TArray<IAReward::FMedal>& Medals = IAReward::Medals();
	int32 Golds = 0;
	for (int32 I = 0; I < Medals.Num(); ++I)
	{
		const int64 Value = GetStat(Medals[I].Stat);
		int32 Tier = 0;
		for (int32 T = 0; T < 5; ++T) { Tier += Value >= Medals[I].Tier[T] ? 1 : 0; }
		const FName Key(*FString::Printf(TEXT("MedalTier_%d"), I));
		const int32 Known = static_cast<int32>(GetStat(Key));
		for (int32 T = Known; T < Tier; ++T)
		{
			Stats.FindOrAdd("AP") += IAReward::TierPoints[T];
			LastGain.NewMedals.Add(FString::Printf(TEXT("%s: %s"), Medals[I].Name, IAReward::TierNames[T]));
		}
		Stats.Add(Key, Tier);
		Golds += Tier >= 4 ? 1 : 0;
	}
	if (Golds >= Medals.Num() && Unlock("T11")) { LastGain.NewRewards.Add("T11"); }
	Loadout.Rank = static_cast<uint8>(GetRank());
}

int32 UIAProfileSubsystem::GetRank() const
{
	const TArray<IAReward::FRank>& Ranks = IAReward::Ranks();
	int32 Rank = 0;
	for (int32 I = 0; I < Ranks.Num(); ++I)
	{
		Rank = GetAP() >= Ranks[I].Points ? I : Rank;
	}
	return Rank;
}

int32 UIAProfileSubsystem::GetMedalTier(int32 MedalIndex) const
{
	return static_cast<int32>(GetStat(FName(*FString::Printf(TEXT("MedalTier_%d"), MedalIndex))));
}

float UIAProfileSubsystem::GetProgress(const IAReward::FReward& Reward) const
{
	if (Unlocked.Contains(Reward.Id) || bUnlockAll)
	{
		return 1.f;
	}
	if (Reward.Stat.IsEmpty() || Reward.Threshold <= 0)
	{
		return 0.f;
	}
	return FMath::Clamp(static_cast<float>(GetStat(*Reward.Stat)) / static_cast<float>(Reward.Threshold), 0.f, 1.f);
}

bool UIAProfileSubsystem::IsLookUnlocked(int32 Look) const
{
	return Look < 37 || IsUnlocked(IAReward::LookId(Look));
}

void UIAProfileSubsystem::OnCampaignChanged(const UIACampaignSubsystem& Camp)
{
	if (!Camp.HasCampaign())
	{
		return;
	}
	auto Grant = [this](FName Id)
	{
		if (Unlock(Id)) { LastGain.NewRewards.Add(Id); }
	};
	Grant("T1");

	// Stars are worth 15 apex points each, once.
	const int64 Stars = Camp.GetTotalStars();
	const int64 Paid = GetStat("StarsPaid");
	if (Stars > Paid)
	{
		AddStat("AP", (Stars - Paid) * 15);
		Stats.Add("StarsPaid", Stars);
	}
	SetStatMax("Stars", Stars);

	// Chapters: finished when all four matches are won; elite when every match has three stars.
	const TArray<FIACampaignMatch>& Matches = IACampaign::Matches();
	for (int32 Chapter = 0; Chapter < IACampaign::ChapterCount; ++Chapter)
	{
		bool bAllWon = true, bAllThree = true;
		int32 Count = 0;
		for (int32 I = 0; I < Matches.Num(); ++I)
		{
			if (Matches[I].Chapter != Chapter) { continue; }
			++Count;
			bAllWon = bAllWon && Camp.GetStars(I) >= 1;
			bAllThree = bAllThree && Camp.GetStars(I) >= 3;
		}
		if (Count > 0 && bAllWon)
		{
			const int32 N = Chapter + 1;
			Grant(FName(*FString::Printf(TEXT("G8_%d"), N)));
			Grant(FName(*FString::Printf(TEXT("C6_%d"), N)));
			Grant(FName(*FString::Printf(TEXT("A2_%d"), N)));
			Grant(FName(*FString::Printf(TEXT("T%d"), N + 1)));
			if (bAllThree) { Grant(FName(*FString::Printf(TEXT("C7_%d"), N))); }
		}
	}
	// The Obsidian Crown: one member joins your roster for every match won in chapter 4.
	{
		int32 Member = 0;
		for (int32 I = 0; I < Matches.Num(); ++I)
		{
			if (Matches[I].Chapter == 3 && Camp.GetStars(I) >= 1)
			{
				Grant(IAReward::LookId(37 + FMath::Min(Member, 3)));
				++Member;
			}
		}
	}
	if (Camp.IsComplete())
	{
		Grant("L41"); Grant("L43"); Grant("A3"); Grant("R5");
		if (Camp.GetDifficulty() >= 2) { Grant("L42"); Grant("M2"); }
	}
	if (Camp.GetEnding() == 1) { Grant("C3"); }
	if (Camp.GetEnding() == 2) { Grant("C4"); }
	EvaluateRewards();
	NewUnlocks.Reset();
	Save();
}

void UIAProfileSubsystem::ResetProfile()
{
	Stats.Reset();
	Unlocked.Reset();
	NewUnlocks.Reset();
	Loadout = FIACosmeticLoadout();
	LastGain = FIAMatchGain();
	Pending = FPending();
	Save();
}
