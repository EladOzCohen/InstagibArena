// Instagib Arena

#include "IALoadoutRules.h"
#include "IAProfileSubsystem.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace IALoadout
{
	int32 OptionCount(EField Field)
	{
		switch (Field)
		{
		case EField::BeamStyle:        return 5;
		case EField::RifleFinish:      return 5;
		case EField::Barrel:           return 5;
		case EField::Stock:            return 4;
		case EField::Fins:             return 3;
		case EField::Charm:            return 4;
		case EField::RifleLivery:      return 7;
		case EField::KillEffect:       return 7;
		case EField::CharacterVariant: return 4;
		default:                       return 1;
		}
	}

	FText OptionName(EField Field, int32 Value)
	{
		static const TCHAR* const Beam[] = { TEXT("Standard"), TEXT("Needle"), TEXT("Lance"), TEXT("Pulse"), TEXT("Confetti") };
		static const TCHAR* const Finish[] = { TEXT("Standard"), TEXT("Matt"), TEXT("Steel"), TEXT("Brass"), TEXT("Gold") };
		static const TCHAR* const Barrel[] = { TEXT("Standard"), TEXT("Short"), TEXT("Long"), TEXT("Twin"), TEXT("Pennant") };
		static const TCHAR* const Stock[] = { TEXT("Standard"), TEXT("Skeleton"), TEXT("Heavy"), TEXT("Marksman") };
		static const TCHAR* const Fins[] = { TEXT("None"), TEXT("Plain"), TEXT("Ion") };
		static const TCHAR* const Charm[] = { TEXT("None"), TEXT("Tiny hat"), TEXT("Rubber duck"), TEXT("Tiny cow") };
		static const TCHAR* const Livery[] = { TEXT("None"), TEXT("Rustborn"), TEXT("Legion"), TEXT("Syndicate"), TEXT("Void Corps"), TEXT("Hollow Court"), TEXT("Obsidian") };
		static const TCHAR* const Kill[] = { TEXT("Standard"), TEXT("Ash"), TEXT("Gold Shatter"), TEXT("Frost"), TEXT("Glitch"), TEXT("Ember"), TEXT("Poof") };
		static const TCHAR* const Variant[] = { TEXT("Standard"), TEXT("Veteran"), TEXT("Elite"), TEXT("Obsidian") };

		const TCHAR* const* Names = nullptr;
		switch (Field)
		{
		case EField::BeamStyle:        Names = Beam; break;
		case EField::RifleFinish:      Names = Finish; break;
		case EField::Barrel:           Names = Barrel; break;
		case EField::Stock:            Names = Stock; break;
		case EField::Fins:             Names = Fins; break;
		case EField::Charm:            Names = Charm; break;
		case EField::RifleLivery:      Names = Livery; break;
		case EField::KillEffect:       Names = Kill; break;
		case EField::CharacterVariant: Names = Variant; break;
		default: break;
		}
		if (!Names || Value < 0 || Value >= OptionCount(Field))
		{
			return FText::GetEmpty();
		}
		return FText::FromString(Names[Value]);
	}

	FName RequiredReward(EField Field, int32 Value)
	{
		if (Value <= 0)
		{
			return NAME_None;
		}
		switch (Field)
		{
		case EField::BeamStyle:        return Value == 4 ? FName(TEXT("G12")) : FName(TEXT("G3"));
		case EField::RifleFinish:      return Value == 4 ? RewardGold : FName(TEXT("G2"));
		case EField::Barrel:           return Value == 4 ? FName(TEXT("G9")) : FName(TEXT("G5"));
		case EField::Stock:            return FName(TEXT("G5"));
		case EField::Fins:             return Value == 2 ? FName(TEXT("G10")) : FName(TEXT("G5"));
		case EField::Charm:            return FName(TEXT("G11"));
		case EField::RifleLivery:      return Value == 6 ? FName(TEXT("R5")) : FName(TEXT("G8"));
		case EField::KillEffect:       return FName(*FString::Printf(TEXT("K%d"), Value));
		case EField::CharacterVariant: return Value == 1 ? FName(TEXT("C6")) : (Value == 2 ? FName(TEXT("C7")) : FName(TEXT("R5")));
		default:                       return NAME_None;
		}
	}

	FText RequirementText(FName RewardId)
	{
		static const TMap<FName, const TCHAR*> Texts = {
			{ TEXT("G1"),  TEXT("100 kills") },
			{ TEXT("G2"),  TEXT("250 kills") },
			{ TEXT("G3"),  TEXT("500 kills") },
			{ TEXT("G4"),  TEXT("1,000 kills") },
			{ TEXT("G5"),  TEXT("2,500 kills") },
			{ TEXT("G6"),  TEXT("5,000 kills") },
			{ TEXT("G7"),  TEXT("10,000 kills") },
			{ TEXT("G8"),  TEXT("Finish a campaign chapter") },
			{ TEXT("G9"),  TEXT("Flagbearer Silver medal") },
			{ TEXT("G10"), TEXT("Skybound Silver medal") },
			{ TEXT("G11"), TEXT("100 matches and 100 deaths") },
			{ TEXT("G12"), TEXT("100 matches played") },
			{ TEXT("K1"),  TEXT("Slayer Bronze medal") },
			{ TEXT("K2"),  TEXT("Slayer Gold medal") },
			{ TEXT("K3"),  TEXT("10 wins on Glacier") },
			{ TEXT("K4"),  TEXT("Skybound Gold medal") },
			{ TEXT("K5"),  TEXT("Longshot Silver medal") },
			{ TEXT("K6"),  TEXT("50 matches without a win") },
			{ TEXT("C6"),  TEXT("Finish a campaign chapter") },
			{ TEXT("C7"),  TEXT("3 stars in every match of a chapter") },
			{ TEXT("R5"),  TEXT("Finish the campaign (Apex+)") },
		};
		if (const TCHAR* const* Found = Texts.Find(RewardId))
		{
			return FText::FromString(*Found);
		}
		return FText::FromString(RewardId.ToString());
	}

	int32 GetField(const FIACosmeticLoadout& L, EField Field)
	{
		switch (Field)
		{
		case EField::BeamStyle:        return L.BeamStyle;
		case EField::RifleFinish:      return L.RifleFinish;
		case EField::Barrel:           return L.Barrel;
		case EField::Stock:            return L.Stock;
		case EField::Fins:             return L.Fins;
		case EField::Charm:            return L.Charm;
		case EField::RifleLivery:      return L.RifleLivery;
		case EField::KillEffect:       return L.KillEffect;
		case EField::CharacterVariant: return L.CharacterVariant;
		default:                       return 0;
		}
	}

	void SetField(FIACosmeticLoadout& L, EField Field, int32 Value)
	{
		const uint8 V = static_cast<uint8>(FMath::Clamp(Value, 0, OptionCount(Field) - 1));
		switch (Field)
		{
		case EField::BeamStyle:        L.BeamStyle = V; break;
		case EField::RifleFinish:      L.RifleFinish = V; break;
		case EField::Barrel:           L.Barrel = V; break;
		case EField::Stock:            L.Stock = V; break;
		case EField::Fins:             L.Fins = V; break;
		case EField::Charm:            L.Charm = V; break;
		case EField::RifleLivery:      L.RifleLivery = V; break;
		case EField::KillEffect:       L.KillEffect = V; break;
		case EField::CharacterVariant: L.CharacterVariant = V; break;
		default: break;
		}
	}

	const TArray<FColor>& BeamPresets()
	{
		static const TArray<FColor> Presets = {
			FColor(255, 40, 40),     // red
			FColor(255, 140, 20),    // orange
			FColor(255, 235, 60),    // yellow
			FColor(60, 255, 90),     // green
			FColor(40, 210, 255),    // cyan
			FColor(190, 70, 255),    // violet
		};
		return Presets;
	}

	FColor GoldBeam()
	{
		return FColor(255, 196, 70);
	}

	void Clamp(FIACosmeticLoadout& L)
	{
		for (int32 F = 0; F < static_cast<int32>(EField::Count); ++F)
		{
			SetField(L, static_cast<EField>(F), GetField(L, static_cast<EField>(F)));
		}
		L.BeamColor.A = 255;
		L.RifleBody.A = 255;
		L.RifleAccent.A = 255;
		L.RifleCore.A = 255;
		L.KillCounterValue = FMath::Clamp(L.KillCounterValue, 0, 9999999);
		L.Rank = FMath::Min<uint8>(L.Rank, 6);
	}

	void RemoveLocked(FIACosmeticLoadout& L, const UIAProfileSubsystem* Profile)
	{
		auto Has = [Profile](FName Id) { return Id.IsNone() || (Profile && Profile->IsUnlocked(Id)); };
		for (int32 F = 0; F < static_cast<int32>(EField::Count); ++F)
		{
			const EField Field = static_cast<EField>(F);
			if (!Has(RequiredReward(Field, GetField(L, Field))))
			{
				SetField(L, Field, 0);
			}
		}
		if (L.bCustomBeamColor && !Has(L.BeamColor == GoldBeam() ? RewardGold : RewardBeamColor))
		{
			L.bCustomBeamColor = false;
		}
		if (L.bCustomRifle && !Has(RewardCustomRifle))
		{
			L.bCustomRifle = false;
		}
		if (L.bKillCounter && !Has(RewardKillCounter))
		{
			L.bKillCounter = false;
		}
	}

	int32 LifetimeKills(const UIAProfileSubsystem* Profile)
	{
		return Profile ? static_cast<int32>(FMath::Clamp<int64>(Profile->GetStat(TEXT("Kills")), 0, 9999999)) : 0;
	}

	FIACosmeticLoadout MakeBotLoadout(int32 Seed)
	{
		FRandomStream Random(Seed * 7919 + 17);
		FIACosmeticLoadout L;
		if (Random.FRand() < 0.25f)
		{
			return L;   // a quarter of the bots look standard
		}
		// Each bot gets about two things; the kill effects are the most common, so they are seen in bot matches.
		if (Random.FRand() < 0.6f) { L.KillEffect = static_cast<uint8>(Random.RandRange(1, 5)); }
		if (Random.FRand() < 0.04f) { L.KillEffect = 6; }   // Poof stays a rare joke
		if (Random.FRand() < 0.35f) { L.BeamStyle = static_cast<uint8>(Random.RandRange(1, 3)); }
		if (Random.FRand() < 0.3f) { L.RifleFinish = static_cast<uint8>(Random.RandRange(1, 3)); }
		if (Random.FRand() < 0.25f) { L.Barrel = static_cast<uint8>(Random.RandRange(1, 3)); }
		if (Random.FRand() < 0.15f) { L.Fins = static_cast<uint8>(Random.RandRange(1, 2)); }
		if (Random.FRand() < 0.15f) { L.RifleLivery = static_cast<uint8>(Random.RandRange(1, 5)); }
		if (Random.FRand() < 0.2f) { L.CharacterVariant = static_cast<uint8>(Random.RandRange(1, 2)); }
		if (Random.FRand() < 0.05f) { L.Charm = static_cast<uint8>(Random.RandRange(1, 3)); }
		if (Random.FRand() < 0.1f)
		{
			L.bCustomBeamColor = true;
			L.BeamColor = BeamPresets()[Random.RandRange(0, BeamPresets().Num() - 1)];
		}
		return L;
	}

	bool GetDevOverride(const TCHAR* Param, FIACosmeticLoadout& OutLoadout)
	{
#if !UE_BUILD_SHIPPING
		FString Text;
		if (FParse::Value(FCommandLine::Get(), *FString::Printf(TEXT("%s="), Param), Text, /*bShouldStopOnSeparator*/ false))
		{
			OutLoadout.FromString(Text);
			FString KvText;
			if (Text.Split(TEXT("kv="), nullptr, &KvText))
			{
				OutLoadout.KillCounterValue = FCString::Atoi(*KvText);
			}
			Clamp(OutLoadout);
			return true;
		}
#endif
		return false;
	}

	FString Describe(const FIACosmeticLoadout& L)
	{
		return FString::Printf(TEXT("%s,kv=%d"), *L.ToString(), L.KillCounterValue);
	}
}
