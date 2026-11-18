// Instagib Arena

#include "IAProfileSubsystem.h"
#include "InstagibArena.h"
#include "Engine/GameInstance.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"

namespace
{
	const TCHAR* const Section = TEXT("InstagibArena.Profile");
}

void UIAProfileSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	bUnlockAll = FParse::Param(FCommandLine::Get(), TEXT("IAUnlockAll"));
	Load();

	// Development: -IAProfileSet=Kills:990,Wins:4 sets counters (they are saved like real ones).
	FString Set;
	if (FParse::Value(FCommandLine::Get(), TEXT("IAProfileSet="), Set))
	{
		TArray<FString> Pairs;
		Set.ParseIntoArray(Pairs, TEXT(","));
		for (const FString& Pair : Pairs)
		{
			FString Key, Value;
			if (Pair.Split(TEXT(":"), &Key, &Value))
			{
				Stats.Add(FName(*Key), FCString::Atoi64(*Value));
			}
		}
	}
}

UIAProfileSubsystem* UIAProfileSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	UGameInstance* Instance = World ? World->GetGameInstance() : nullptr;
	return Instance ? Instance->GetSubsystem<UIAProfileSubsystem>() : nullptr;
}

int64 UIAProfileSubsystem::GetStat(FName Stat) const
{
	const int64* Value = Stats.Find(Stat);
	return Value ? *Value : 0;
}

void UIAProfileSubsystem::AddStat(FName Stat, int64 Amount)
{
	Stats.FindOrAdd(Stat) += Amount;
}

void UIAProfileSubsystem::SetStatMax(FName Stat, int64 Value)
{
	int64& Slot = Stats.FindOrAdd(Stat);
	Slot = FMath::Max(Slot, Value);
}

bool UIAProfileSubsystem::IsUnlocked(FName RewardId) const
{
	return bUnlockAll || Unlocked.Contains(RewardId);
}

bool UIAProfileSubsystem::Unlock(FName RewardId)
{
	if (Unlocked.Contains(RewardId))
	{
		return false;
	}
	Unlocked.Add(RewardId);
	NewUnlocks.Add(RewardId);
	UE_LOG(LogInstagib, Log, TEXT("Profile: unlocked %s"), *RewardId.ToString());
	return true;
}

TArray<FName> UIAProfileSubsystem::ConsumeNewUnlocks()
{
	TArray<FName> Result = MoveTemp(NewUnlocks);
	NewUnlocks.Reset();
	return Result;
}

void UIAProfileSubsystem::SetLoadout(const FIACosmeticLoadout& NewLoadout)
{
	Loadout = NewLoadout;
	Save();
}

void UIAProfileSubsystem::Load()
{
	FString Text;
	if (GConfig->GetString(Section, TEXT("Stats"), Text, GGameUserSettingsIni))
	{
		TArray<FString> Pairs;
		Text.ParseIntoArray(Pairs, TEXT(","));
		for (const FString& Pair : Pairs)
		{
			FString Key, Value;
			if (Pair.Split(TEXT(":"), &Key, &Value))
			{
				Stats.Add(FName(*Key), FCString::Atoi64(*Value));
			}
		}
	}
	if (GConfig->GetString(Section, TEXT("Unlocked"), Text, GGameUserSettingsIni))
	{
		TArray<FString> Ids;
		Text.ParseIntoArray(Ids, TEXT(","));
		for (const FString& Id : Ids)
		{
			Unlocked.Add(FName(*Id));
		}
	}
	if (GConfig->GetString(Section, TEXT("Loadout"), Text, GGameUserSettingsIni))
	{
		Loadout.FromString(Text);
	}
}

void UIAProfileSubsystem::Save() const
{
	FString StatText;
	for (const TPair<FName, int64>& Pair : Stats)
	{
		StatText += FString::Printf(TEXT("%s:%lld,"), *Pair.Key.ToString(), Pair.Value);
	}
	FString UnlockText;
	for (const FName& Id : Unlocked)
	{
		UnlockText += Id.ToString() + TEXT(",");
	}
	GConfig->SetString(Section, TEXT("Stats"), *StatText, GGameUserSettingsIni);
	GConfig->SetString(Section, TEXT("Unlocked"), *UnlockText, GGameUserSettingsIni);
	GConfig->SetString(Section, TEXT("Loadout"), *Loadout.ToString(), GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
}
