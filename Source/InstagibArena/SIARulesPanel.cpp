// Instagib Arena

#include "SIARulesPanel.h"
#include "IACampaignSubsystem.h"
#include "IAMapList.h"
#include "IAMenuStyle.h"
#include "IAProfileSubsystem.h"
#include "IARuleData.h"
#include "InstagibArena.h"
#include "Engine/GameInstance.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Parse.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"

using namespace IAMenu;

namespace
{
	const TCHAR* const Section = TEXT("InstagibArena.Rules");

	/** What the player picked last time (some of it may be locked now or not exist on the selected map). */
	struct FPick
	{
		uint8 Mutators = 0;
		int32 Variant = 0;
		bool bLoaded = false;
	};

	FPick& Pick()
	{
		static FPick P;
		if (!P.bLoaded)
		{
			P.bLoaded = true;
			FString Text;
			if (GConfig->GetString(Section, TEXT("Mutators"), Text, GGameUserSettingsIni)) { P.Mutators = IARules::ParseMutators(Text); }
			GConfig->GetInt(Section, TEXT("Variant"), P.Variant, GGameUserSettingsIni);
#if !UE_BUILD_SHIPPING
			FString Dev;
			if (FParse::Value(FCommandLine::Get(), TEXT("IARulesPick="), Dev, /*bShouldStopOnSeparator*/ false))
			{
				FString Muts, Var;
				if (!Dev.Split(TEXT(";"), &Muts, &Var)) { Muts = Dev; }
				P.Mutators = IARules::ParseMutators(Muts);
				P.Variant = FCString::Atoi(*Var);
			}
#endif
			P.Variant = FMath::Clamp(P.Variant, 0, IARules::VariantCount - 1);
		}
		return P;
	}

	void SavePick()
	{
		const FPick& P = Pick();
		GConfig->SetString(Section, TEXT("Mutators"), *IARules::MutatorsToString(P.Mutators), GGameUserSettingsIni);
		GConfig->SetInt(Section, TEXT("Variant"), P.Variant, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	const UIAProfileSubsystem* Profile(const TWeakObjectPtr<APlayerController>& Owner)
	{
		return UIAProfileSubsystem::Get(Owner.Get());
	}

	bool IsUnlocked(const TWeakObjectPtr<APlayerController>& Owner, FName Id)
	{
		const UIAProfileSubsystem* P = Profile(Owner);
		return P && P->IsUnlocked(Id);
	}

	FString MapShort(int32 MapIndex)
	{
		return IARules::MapShortName(IAMaps::List[FMath::Clamp(MapIndex, 0, IAMaps::Count - 1)].AssetPath);
	}

	bool VariantUsable(const TWeakObjectPtr<APlayerController>& Owner, int32 MapIndex, int32 Variant)
	{
		if (Variant == 0) { return true; }
		const FString Map = MapShort(MapIndex);
		return IARules::MapHasVariants(Map) && IsUnlocked(Owner, IARules::VariantUnlockId(Map, Variant));
	}

	/** The variant that will really be played on this map. */
	int32 EffectiveVariant(const TWeakObjectPtr<APlayerController>& Owner, int32 MapIndex)
	{
		const int32 V = Pick().Variant;
		return VariantUsable(Owner, MapIndex, V) ? V : 0;
	}

	uint8 EffectiveMutators(const TWeakObjectPtr<APlayerController>& Owner)
	{
		uint8 Bits = 0;
		for (const FIARuleInfo& Rule : IARules::Mutators)
		{
			if (IARules::Has(Pick().Mutators, Rule.Flag) && IsUnlocked(Owner, Rule.RewardId))
			{
				Bits |= static_cast<uint8>(Rule.Flag);
			}
		}
		return Bits;
	}

	/** A chip that is dimmed and does nothing while locked; the tooltip says what it does or what unlocks it. */
	TSharedRef<SWidget> GatedChip(const TWeakObjectPtr<APlayerController>& Owner, const FText& Label, TFunction<bool()> IsOpen,
		TFunction<void()> OnClick, TFunction<bool()> IsSelected, TFunction<FText()> Tip, float Width)
	{
		return SNew(SBox)
			.Padding(FMargin(0.f, 0.f, 8.f, 6.f))
			.IsEnabled_Lambda([IsOpen]() { return IsOpen(); })
			.ToolTipText_Lambda([Tip]() { return Tip(); })
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("NoBorder"))
				.Padding(0.f)
				.ColorAndOpacity_Lambda([IsOpen]() { return IsOpen() ? FLinearColor::White : FLinearColor(1.f, 1.f, 1.f, 0.38f); })
				[
					ChipDyn(Owner,
						[Label, IsOpen]() { return IsOpen() ? Label : FText::Format(INVTEXT("{0}  (locked)"), Label); },
						[OnClick, IsOpen]() { if (IsOpen()) { OnClick(); } },
						IsSelected, Width, 14)
				]
			];
	}

	TSharedRef<SWidget> Indented(TSharedRef<SWidget> Content)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth() [ SNew(SBox).WidthOverride(170.f) ]
			+ SHorizontalBox::Slot().FillWidth(1.f) [ Content ];
	}
}

TSharedRef<SWidget> IARulesUI::BuildCustomRows(const TWeakObjectPtr<APlayerController>& Owner, TFunction<int32()> GetMapIndex)
{
	// ---- RULES: one toggle per mutator
	TSharedRef<SWrapBox> RuleChips = SNew(SWrapBox).PreferredSize(480.f).UseAllottedSize(false);
	for (const FIARuleInfo& Rule : IARules::Mutators)
	{
		const FName Id(Rule.RewardId);
		const EIAMutator Flag = Rule.Flag;
		const FText Description = FText::FromString(Rule.Description);
		const FText Requirement = FText::Format(INVTEXT("Locked. Unlock: {0}."), FText::FromString(Rule.Requirement));
		auto IsOpen = [Owner, Id]() { return IsUnlocked(Owner, Id); };
		RuleChips->AddSlot()
		[
			GatedChip(Owner, FText::FromString(Rule.Name), IsOpen,
				[Flag]() { Pick().Mutators ^= static_cast<uint8>(Flag); SavePick(); },
				[Flag, IsOpen]() { return IsOpen() && IARules::Has(Pick().Mutators, Flag); },
				[IsOpen, Description, Requirement]() { return IsOpen() ? Description : Requirement; }, 0.f)
		];
	}

	// ---- TIME: day, dusk, night of the selected map
	TSharedRef<SHorizontalBox> TimeChips = SNew(SHorizontalBox);
	for (int32 V = 0; V < IARules::VariantCount; ++V)
	{
		auto IsOpen = [Owner, GetMapIndex, V]() { return VariantUsable(Owner, GetMapIndex(), V); };
		TimeChips->AddSlot().AutoWidth()
		[
			GatedChip(Owner, FText::FromString(IARules::VariantNames[V]), IsOpen,
				[V]() { Pick().Variant = V; SavePick(); },
				[Owner, GetMapIndex, V]() { return EffectiveVariant(Owner, GetMapIndex()) == V; },
				[GetMapIndex, V]()
				{
					if (V == 0) { return INVTEXT("The map as it was built."); }
					if (!IARules::MapHasVariants(MapShort(GetMapIndex()))) { return INVTEXT("This map has one time of day."); }
					return FText::Format(INVTEXT("{0}. Unlock: {1}."), FText::FromString(IARules::VariantNames[V]), FText::FromString(IARules::VariantRequirements[V]));
				}, 96.f)
		];
	}

	// A line under the rows: what is on, what is still locked.
	auto Summary = [Owner, GetMapIndex]()
	{
		FString On;
		FString Locked;
		const uint8 Active = EffectiveMutators(Owner);
		for (const FIARuleInfo& Rule : IARules::Mutators)
		{
			if (IARules::Has(Active, Rule.Flag)) { On += (On.IsEmpty() ? TEXT("") : TEXT(" ")) + FString(Rule.Description); }
			else if (!IsUnlocked(Owner, Rule.RewardId)) { Locked += (Locked.IsEmpty() ? TEXT("") : TEXT(", ")) + FString::Printf(TEXT("%s (%s)"), Rule.Name, Rule.Requirement); }
		}
		const FString Map = MapShort(GetMapIndex());
		if (IARules::MapHasVariants(Map))
		{
			for (int32 V = 1; V < IARules::VariantCount; ++V)
			{
				if (!IsUnlocked(Owner, IARules::VariantUnlockId(Map, V)))
				{
					Locked += (Locked.IsEmpty() ? TEXT("") : TEXT(", ")) + FString::Printf(TEXT("%s (%s)"), IARules::VariantNames[V], IARules::VariantRequirements[V]);
				}
			}
		}
		FString Text = On;
		if (!Locked.IsEmpty()) { Text += (Text.IsEmpty() ? TEXT("") : TEXT("\n")) + FString(TEXT("Locked: ")) + Locked; }
		return FText::FromString(Text);
	};

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f, 0.f, 0.f)
		[
			Row(INVTEXT("Rules"), RuleChips, 170.f, INVTEXT("Extra rules for this match. Earned in the Hall of Champions; they change the fun, not the power."))
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 2.f, 0.f, 0.f)
		[
			Row(INVTEXT("Time of day"), TimeChips, 170.f, INVTEXT("The same map in another light. Dusk and Night are earned by winning on the map."))
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 6.f)
		[
			Indented(Note(Summary))
		];
}

FString IARulesUI::UrlOptions(const TWeakObjectPtr<APlayerController>& Owner, int32 MapIndex)
{
	FString Out;
	const uint8 Bits = EffectiveMutators(Owner);
	if (Bits != 0)
	{
		Out += TEXT("?Mut=") + IARules::MutatorsToString(Bits);
	}
	const int32 Variant = EffectiveVariant(Owner, MapIndex);
	if (Variant != 0)
	{
		Out += FString::Printf(TEXT("?Variant=%s"), IARules::VariantKeys[Variant]);
	}
	return Out;
}

// ---------------------------------------------------------------- campaign Heat

namespace
{
	UIACampaignSubsystem* Camp(const TWeakObjectPtr<APlayerController>& Owner)
	{
		const APlayerController* PC = Owner.Get();
		UGameInstance* Instance = PC ? PC->GetGameInstance() : nullptr;
		return Instance ? Instance->GetSubsystem<UIACampaignSubsystem>() : nullptr;
	}

	/** "Enemy skill +1. One more enemy ..." for Heat 1..Level. */
	FString HeatRulesText(int32 Level)
	{
		FString Text;
		for (int32 I = 0; I < FMath::Min(Level, IARules::MaxHeat); ++I)
		{
			Text += (Text.IsEmpty() ? TEXT("") : TEXT(". ")) + FString(IARules::HeatSteps[I].Rule);
		}
		return Text.IsEmpty() ? Text : Text + TEXT(".");
	}

	const FLinearColor HeatColor(1.f, 0.42f, 0.18f);
}

TSharedRef<SWidget> IARulesUI::BuildHeatSelector(const TWeakObjectPtr<APlayerController>& Owner)
{
	const UIACampaignSubsystem* C = Camp(Owner);
	if (!C || !C->HasCampaign())
	{
		return SNullWidget::NullWidget;
	}
	if (!C->IsHeatAvailable())
	{
		return Note([]() { return INVTEXT("Apex+ Heat: finish the campaign to play it again with harder rules."); });
	}

	TSharedRef<SHorizontalBox> Chips = SNew(SHorizontalBox);
	for (int32 Level = 0; Level <= IARules::MaxHeat; ++Level)
	{
		Chips->AddSlot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
		[
			Chip(Owner, Level == 0 ? INVTEXT("OFF") : FText::AsNumber(Level),
				[Owner, Level]() { if (UIACampaignSubsystem* S = Camp(Owner)) { S->SetHeatLevel(Level); } },
				[Owner, Level]() { const UIACampaignSubsystem* S = Camp(Owner); return S && S->GetHeatLevel() == Level; }, 54.f, 15)
		];
	}
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 4.f)
		[
			Row(INVTEXT("Apex+ Heat"), Chips, 170.f, INVTEXT("Play the ladder again with harder rules. Each level adds a rule to the ones below it."))
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			Note([Owner]()
			{
				const UIACampaignSubsystem* S = Camp(Owner);
				const int32 Level = S ? S->GetHeatLevel() : 0;
				if (Level == 0) { return INVTEXT("Heat off: the normal campaign."); }
				return FText::Format(INVTEXT("HEAT {0} - {1}: {2}"), Level, FText::FromString(IARules::HeatSteps[Level - 1].Name), FText::FromString(HeatRulesText(Level)));
			}, []() { return HeatColor; })
		];
}

TSharedRef<SWidget> IARulesUI::BuildHeatBriefing(const TWeakObjectPtr<APlayerController>& Owner, int32 MatchIndex)
{
	const UIACampaignSubsystem* C = Camp(Owner);
	const int32 Level = C ? C->GetHeatLevel() : 0;
	const int32 Best = C ? C->GetBestHeat(MatchIndex) : 0;
	if (Level == 0 && Best == 0)
	{
		return SNullWidget::NullWidget;
	}
	FString Text;
	if (Level > 0)
	{
		Text = FString::Printf(TEXT("HEAT %d active: %s"), Level, *HeatRulesText(Level));
	}
	if (Best > 0)
	{
		Text += (Text.IsEmpty() ? TEXT("") : TEXT("  ")) + FString::Printf(TEXT("Best cleared here: Heat %d."), Best);
	}
	return SNew(STextBlock)
		.Text(FText::FromString(Text))
		.Font(Font(15, true))
		.ColorAndOpacity(HeatColor)
		.AutoWrapText(true);
}
