// Instagib Arena

#include "IACampaignSubsystem.h"
#include "IACharacterRoster.h"
#include "InstagibArena.h"
#include "Misc/ConfigCacheIni.h"

namespace
{
	const TCHAR* const Section = TEXT("InstagibArena.Campaign");

	FString JoinInts(const TArray<int32>& Values)
	{
		FString Out;
		for (int32 V : Values)
		{
			Out += (Out.IsEmpty() ? TEXT("") : TEXT(",")) + FString::FromInt(V);
		}
		return Out;
	}

	TArray<int32> ParseInts(const FString& Text)
	{
		TArray<int32> Out;
		TArray<FString> Parts;
		Text.ParseIntoArray(Parts, TEXT(","));
		for (const FString& P : Parts)
		{
			Out.Add(FCString::Atoi(*P));
		}
		return Out;
	}

	/** Takes Count looks: first the preferred ones, then every other look, skipping the excluded ones. */
	TArray<int32> PickLooks(const TArray<int32>& Preferred, const TSet<int32>& Excluded, int32 Count)
	{
		TArray<int32> Out;
		TSet<int32> Used = Excluded;
		auto Take = [&](int32 Look)
		{
			if (Out.Num() < Count && !Used.Contains(Look))
			{
				Used.Add(Look);
				Out.Add(Look);
			}
		};
		for (int32 Look : Preferred) { Take(Look); }
		for (int32 Look = 0; Look < IACharacters::LookCount; ++Look) { Take(Look); }
		return Out;
	}
}

void UIACampaignSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	StarsPerMatch.Init(0, IACampaign::MatchCount);
	Load();
}

void UIACampaignSubsystem::Load()
{
	bool bValue = false;
	GConfig->GetBool(Section, TEXT("Started"), bValue, GGameUserSettingsIni);
	bStarted = bValue;
	GConfig->GetString(Section, TEXT("Hero"), HeroName, GGameUserSettingsIni);
	GConfig->GetInt(Section, TEXT("HeroLook"), HeroLook, GGameUserSettingsIni);
	GConfig->GetInt(Section, TEXT("Difficulty"), Difficulty, GGameUserSettingsIni);
	GConfig->GetInt(Section, TEXT("Next"), NextMatch, GGameUserSettingsIni);
	GConfig->GetInt(Section, TEXT("Ending"), Ending, GGameUserSettingsIni);
	FString Text;
	GConfig->GetString(Section, TEXT("Stars"), Text, GGameUserSettingsIni);
	StarsPerMatch = ParseInts(Text);
	StarsPerMatch.SetNumZeroed(IACampaign::MatchCount);
	GConfig->GetString(Section, TEXT("Squad"), Text, GGameUserSettingsIni);
	Squad = ParseInts(Text);
	Squad.SetNum(FMath::Min(Squad.Num(), IACampaign::MaxSquadMates));
	NextMatch = FMath::Clamp(NextMatch, 0, IACampaign::MatchCount);
	Difficulty = FMath::Clamp(Difficulty, 0, 2);
	HeroLook = FMath::Clamp(HeroLook, 0, IACharacters::LookCount - 1);
}

void UIACampaignSubsystem::Save() const
{
	GConfig->SetBool(Section, TEXT("Started"), bStarted, GGameUserSettingsIni);
	GConfig->SetString(Section, TEXT("Hero"), *HeroName, GGameUserSettingsIni);
	GConfig->SetInt(Section, TEXT("HeroLook"), HeroLook, GGameUserSettingsIni);
	GConfig->SetInt(Section, TEXT("Difficulty"), Difficulty, GGameUserSettingsIni);
	GConfig->SetInt(Section, TEXT("Next"), NextMatch, GGameUserSettingsIni);
	GConfig->SetInt(Section, TEXT("Ending"), Ending, GGameUserSettingsIni);
	GConfig->SetString(Section, TEXT("Stars"), *JoinInts(StarsPerMatch), GGameUserSettingsIni);
	GConfig->SetString(Section, TEXT("Squad"), *JoinInts(Squad), GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
}

void UIACampaignSubsystem::StartNewCampaign(const FString& InHeroName, int32 InHeroLook, int32 InDifficulty)
{
	bStarted = true;
	HeroName = InHeroName.IsEmpty() ? TEXT("Wildcard") : InHeroName;
	HeroLook = FMath::Clamp(InHeroLook, 0, IACharacters::LookCount - 1);
	Difficulty = FMath::Clamp(InDifficulty, 0, 2);
	NextMatch = 0;
	Ending = 0;
	StarsPerMatch.Init(0, IACampaign::MatchCount);
	Squad.Reset();
	Save();
}

void UIACampaignSubsystem::ResetCampaign()
{
	bStarted = false;
	NextMatch = 0;
	Ending = 0;
	StarsPerMatch.Init(0, IACampaign::MatchCount);
	Squad.Reset();
	Save();
}

int32 UIACampaignSubsystem::GetStars(int32 Index) const
{
	return StarsPerMatch.IsValidIndex(Index) ? StarsPerMatch[Index] : 0;
}

int32 UIACampaignSubsystem::GetTotalStars() const
{
	int32 Total = 0;
	for (int32 S : StarsPerMatch) { Total += S; }
	return Total;
}

int32 UIACampaignSubsystem::GetEffectiveSkill(int32 MatchIndex) const
{
	const TArray<FIACampaignMatch>& Matches = IACampaign::Matches();
	if (!Matches.IsValidIndex(MatchIndex))
	{
		return 3;
	}
	return FMath::Clamp(Matches[MatchIndex].BotSkill + (Difficulty - 1), 0, 6);
}

void UIACampaignSubsystem::SetEnding(int32 Value)
{
	Ending = FMath::Clamp(Value, 0, 2);
	Save();
}

FString UIACampaignSubsystem::MapPath(const TCHAR* ShortName)
{
	return FString::Printf(TEXT("/Game/Maps/DM-%s"), ShortName);
}

TArray<int32> UIACampaignSubsystem::BuildAllyLooks(int32 MatchIndex) const
{
	const TArray<FIACampaignMatch>& Matches = IACampaign::Matches();
	if (!Matches.IsValidIndex(MatchIndex) || Matches[MatchIndex].AllyCount <= 0)
	{
		return {};
	}
	const FIACampaignMatch& M = Matches[MatchIndex];
	TSet<int32> Excluded;
	Excluded.Add(HeroLook);
	for (int32 Look : IACampaign::Factions()[M.Faction].Looks) { Excluded.Add(Look); }

	TArray<int32> Allies;
	for (int32 Look : Squad)
	{
		if (Allies.Num() < M.AllyCount) { Allies.Add(Look); }
	}
	// The League's draft fills the rest: looks that are not the hero, not the squad, not the enemy faction.
	for (int32 Look : Allies) { Excluded.Add(Look); }
	Allies.Append(PickLooks({ 5, 13, 12, 8, 3, 11 }, Excluded, M.AllyCount - Allies.Num()));
	return Allies;
}

TArray<int32> UIACampaignSubsystem::BuildEnemyLooks(int32 MatchIndex) const
{
	const TArray<FIACampaignMatch>& Matches = IACampaign::Matches();
	if (!Matches.IsValidIndex(MatchIndex))
	{
		return {};
	}
	const FIACampaignMatch& M = Matches[MatchIndex];
	TSet<int32> Excluded;
	Excluded.Add(HeroLook);
	for (int32 Look : Squad) { Excluded.Add(Look); }
	for (int32 Look : BuildAllyLooks(MatchIndex)) { Excluded.Add(Look); }
	return PickLooks(IACampaign::Factions()[M.Faction].Looks, Excluded, M.EnemyCount);
}

FString UIACampaignSubsystem::BuildTravelOptions(int32 MatchIndex) const
{
	const TArray<FIACampaignMatch>& Matches = IACampaign::Matches();
	if (!Matches.IsValidIndex(MatchIndex))
	{
		return FString();
	}
	const FIACampaignMatch& M = Matches[MatchIndex];

	const TCHAR* Mode = TEXT("FFA");
	int32 Bots = M.EnemyCount;
	switch (M.Mode)
	{
	case EIACampaignMode::Duel:            Mode = TEXT("FFA"); break;
	case EIACampaignMode::FreeForAll:      Mode = TEXT("FFA"); break;
	case EIACampaignMode::TeamDeathmatch:  Mode = TEXT("TDM"); Bots = M.EnemyCount + M.AllyCount; break;
	case EIACampaignMode::CaptureTheFlag:  Mode = TEXT("CTF"); Bots = M.EnemyCount + M.AllyCount; break;
	case EIACampaignMode::Survival:        Mode = TEXT("Survival"); Bots = M.EnemyCount + M.AllyCount; break;
	}
	return FString::Printf(TEXT("Mode=%s?ScoreLimit=%d?TimeLimit=%d?Bots=%d?BotSkill=%d?Char=%d?%s=%d"),
		Mode, M.Limit, M.TimeLimitMinutes, Bots, GetEffectiveSkill(MatchIndex), HeroLook, UrlOption, MatchIndex + 1);
}

void UIACampaignSubsystem::RecordResult(int32 MatchIndex, bool bWon, int32 Stars)
{
	const TArray<FIACampaignMatch>& Matches = IACampaign::Matches();
	if (!bStarted || !Matches.IsValidIndex(MatchIndex))
	{
		return;
	}
	if (!bWon)
	{
		UE_LOG(LogInstagib, Log, TEXT("Campaign: match %d lost"), MatchIndex + 1);
		return;
	}

	StarsPerMatch.SetNumZeroed(IACampaign::MatchCount);
	StarsPerMatch[MatchIndex] = FMath::Max(StarsPerMatch[MatchIndex], FMath::Clamp(Stars, 1, 3));
	if (MatchIndex >= NextMatch)
	{
		NextMatch = FMath::Min(MatchIndex + 1, IACampaign::MatchCount);
	}

	const int32 Recruit = Matches[MatchIndex].RecruitLook;
	if (Recruit >= 0 && !Squad.Contains(Recruit) && Squad.Num() < IACampaign::MaxSquadMates)
	{
		Squad.Add(Recruit);
		UE_LOG(LogInstagib, Log, TEXT("Campaign: look %d joined the squad"), Recruit);
	}
	UE_LOG(LogInstagib, Log, TEXT("Campaign: match %d won with %d stars, next match %d"), MatchIndex + 1, Stars, NextMatch + 1);
	Save();
}
