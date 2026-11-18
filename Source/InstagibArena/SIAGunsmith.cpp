// Instagib Arena

#include "SIAGunsmith.h"
#include "IAMenuPlayerController.h"
#include "IAMenuStyle.h"
#include "IAProfileSubsystem.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Parse.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SToolTip.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

namespace
{
	const TCHAR* const SlotSection = TEXT("InstagibArena.Gunsmith");
	constexpr float LabelWidth = 132.f;

	/** The quick colours of the free colour rows (sRGB). */
	const FColor Palette[] = {
		FColor(18, 18, 22), FColor(70, 72, 80), FColor(225, 228, 232), FColor(220, 30, 30), FColor(255, 120, 10),
		FColor(255, 210, 40), FColor(40, 200, 70), FColor(30, 200, 230), FColor(40, 80, 230), FColor(150, 50, 220) };

	/** Hue (0..360) and lightness (0 black, 0.5 the pure colour, 1 white) of an sRGB colour, and back. */
	void ToHueLight(const FColor& C, float& Hue, float& Light)
	{
		const FLinearColor Hsv = FLinearColor(C.R / 255.f, C.G / 255.f, C.B / 255.f).LinearRGBToHSV();
		Hue = Hsv.R;
		Light = Hsv.G >= 0.98f ? Hsv.B * 0.5f : 1.f - Hsv.G * 0.5f;
	}

	FColor FromHueLight(float Hue, float Light)
	{
		const float S = Light <= 0.5f ? 1.f : FMath::Clamp(2.f - 2.f * Light, 0.f, 1.f);
		const float V = Light <= 0.5f ? FMath::Clamp(Light * 2.f, 0.f, 1.f) : 1.f;
		return FLinearColor(Hue, S, V).HSVToLinearRGB().ToFColor(false);
	}

	FLinearColor Shown(const FColor& C)
	{
		return FLinearColor::FromSRGBColor(C);
	}
}

void SIAGunsmith::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	OnBack = InArgs._OnBack;

	const UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(Owner.Get());
	Saved = Profile ? Profile->GetLoadout() : FIACosmeticLoadout();
	IALoadout::RemoveLocked(Saved, Profile);
	Working = Saved;
#if !UE_BUILD_SHIPPING
	// Development (screenshots): -IAGunsmithLoad="bs=3,ra=..." starts from that loadout, -IAGunsmithTurn=40 turns the character.
	IALoadout::GetDevOverride(TEXT("IAGunsmithLoad"), Working);
	float DevTurn = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("IAGunsmithTurn="), DevTurn))
	{
		if (AIAMenuPlayerController* MenuPC = Cast<AIAMenuPlayerController>(Owner.Get()))
		{
			MenuPC->SetGunsmithTurn(DevTurn);
		}
	}
#endif

	if (AIAMenuPlayerController* MenuPC = Cast<AIAMenuPlayerController>(Owner.Get()))
	{
		MenuPC->SetGunsmithView(true);
		MenuPC->SetPreviewLoadout(Working);
	}

	TSharedRef<SVerticalBox> Root = SNew(SVerticalBox);
	if (InArgs._ShowTitle)
	{
		Root->AddSlot().AutoHeight() [ Heading(INVTEXT("GUNSMITH")) ];
	}
	Root->AddSlot().FillHeight(1.f) [ ScrollArea(BuildBody()) ];
	Root->AddSlot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f) [ BuildFooter() ];
	ChildSlot [ Root ];
}

SIAGunsmith::~SIAGunsmith()
{
	// Leaving: the camera goes back, the preview shows the saved loadout again (unsaved changes are dropped).
	if (AIAMenuPlayerController* MenuPC = Cast<AIAMenuPlayerController>(Owner.Get()))
	{
		MenuPC->SetGunsmithView(false);
		const UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(MenuPC);
		FIACosmeticLoadout Loadout = Profile ? Profile->GetLoadout() : FIACosmeticLoadout();
		IALoadout::RemoveLocked(Loadout, Profile);
		MenuPC->SetPreviewLoadout(Loadout);
	}
}

bool SIAGunsmith::Has(FName Reward) const
{
	if (Reward.IsNone())
	{
		return true;
	}
	const UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(Owner.Get());
	return Profile && Profile->IsUnlocked(Reward);
}

void SIAGunsmith::Changed()
{
	if (AIAMenuPlayerController* MenuPC = Cast<AIAMenuPlayerController>(Owner.Get()))
	{
		MenuPC->SetPreviewLoadout(Working);
	}
}

bool SIAGunsmith::IsDirty() const
{
	return Working.ToString() != Saved.ToString();
}

void SIAGunsmith::Save()
{
	if (UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(Owner.Get()))
	{
		// Rank and title belong to the profile (the Hall of Champions sets them): keep what is stored there.
		FIACosmeticLoadout ToStore = Working;
		ToStore.Rank = Profile->GetLoadout().Rank;
		ToStore.TitleId = Profile->GetLoadout().TitleId;
		IALoadout::RemoveLocked(ToStore, Profile);
		Profile->SetLoadout(ToStore);
		Saved = ToStore;
		Working.Rank = ToStore.Rank;
		Working.TitleId = ToStore.TitleId;
	}
	Status = INVTEXT("Saved. Your rifle looks like this in every match.");
	StatusUntil = FPlatformTime::Seconds() + 4.0;
}

void SIAGunsmith::Reset()
{
	const uint8 Rank = Working.Rank;
	const int32 TitleId = Working.TitleId;
	Working = FIACosmeticLoadout();
	Working.Rank = Rank;
	Working.TitleId = TitleId;
	Changed();
	Status = INVTEXT("Standard look. Press SAVE to keep it.");
	StatusUntil = FPlatformTime::Seconds() + 4.0;
}

void SIAGunsmith::StoreSlot(int32 Slot)
{
	GConfig->SetString(SlotSection, *FString::Printf(TEXT("Slot%d"), Slot), *Working.ToString(), GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
	Status = FText::Format(INVTEXT("Design stored in slot {0}."), FText::AsNumber(Slot));
	StatusUntil = FPlatformTime::Seconds() + 4.0;
}

void SIAGunsmith::LoadSlot(int32 Slot)
{
	FString Text;
	if (!GConfig->GetString(SlotSection, *FString::Printf(TEXT("Slot%d"), Slot), Text, GGameUserSettingsIni) || Text.IsEmpty())
	{
		Status = FText::Format(INVTEXT("Slot {0} is empty."), FText::AsNumber(Slot));
		StatusUntil = FPlatformTime::Seconds() + 4.0;
		return;
	}
	const uint8 Rank = Working.Rank;
	const int32 TitleId = Working.TitleId;
	Working.FromString(Text);
	IALoadout::Clamp(Working);
	IALoadout::RemoveLocked(Working, UIAProfileSubsystem::Get(Owner.Get()));
	Working.Rank = Rank;
	Working.TitleId = TitleId;
	Changed();
	Status = FText::Format(INVTEXT("Design {0} loaded. Press SAVE to wear it."), FText::AsNumber(Slot));
	StatusUntil = FPlatformTime::Seconds() + 4.0;
}

// ---------------------------------------------------------------- pieces

TSharedRef<SWidget> SIAGunsmith::Section(const FText& Title)
{
	return SNew(SBox).Padding(FMargin(0.f, 14.f, 0.f, 6.f))
		[
			SNew(STextBlock)
			.Text(Title)
			.Font(SpacedFont(15, true, 120))
			.ColorAndOpacity(Accent)
		];
}

TSharedRef<SWidget> SIAGunsmith::LockedChip(const FText& Label, FName Reward) const
{
	// Not a button: it cannot be picked. The tooltip and the line under the row say what is still needed.
	return SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(0.075f, 0.08f, 0.10f))
		.Padding(FMargin(14.f, 8.f))
		.ToolTip(TSharedPtr<IToolTip>(MakeTip(FText::Format(INVTEXT("Locked: {0}"), IALoadout::RequirementText(Reward)))))
		[
			SNew(STextBlock)
			.Text(Label)
			.Font(Font(14, true))
			.ColorAndOpacity(FLinearColor(0.36f, 0.38f, 0.44f))
		];
}

TSharedRef<SWidget> SIAGunsmith::LockNote(TFunction<FText()> Text) const
{
	return SNew(SBox)
		.Padding(FMargin(LabelWidth, 2.f, 0.f, 4.f))
		.Visibility_Lambda([Text]() { return Text().IsEmpty() ? EVisibility::Collapsed : EVisibility::Visible; })
		[
			SNew(STextBlock)
			.Text_Lambda([Text]() { return Text(); })
			.AutoWrapText(true)
			.Font(Font(12))
			.ColorAndOpacity(FLinearColor(0.55f, 0.57f, 0.63f))
		];
}

TSharedRef<SWidget> SIAGunsmith::FieldRow(const FText& Label, EField Field)
{
	TSharedRef<SWrapBox> Options = SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(6.f, 6.f));
	TArray<FName> LockedRewards;
	TArray<FText> LockedNames;
	for (int32 Value = 0; Value < IALoadout::OptionCount(Field); ++Value)
	{
		const FName Reward = IALoadout::RequiredReward(Field, Value);
		const FText Name = IALoadout::OptionName(Field, Value);
		if (Has(Reward))
		{
			Options->AddSlot()
			[
				Chip(Owner, Name, [this, Field, Value]() { IALoadout::SetField(Working, Field, Value); Changed(); },
					[this, Field, Value]() { return IALoadout::GetField(Working, Field) == Value; }, 0.f, 14)
			];
		}
		else
		{
			Options->AddSlot() [ LockedChip(Name, Reward) ];
			LockedRewards.Add(Reward);
			LockedNames.Add(Name);
		}
	}

	// "Needle, Lance, Pulse: 500 kills.  Confetti: 100 matches played."
	FString Note;
	TArray<FName> Seen;
	for (int32 I = 0; I < LockedRewards.Num(); ++I)
	{
		if (Seen.Contains(LockedRewards[I]))
		{
			continue;
		}
		Seen.Add(LockedRewards[I]);
		FString Names;
		for (int32 J = I; J < LockedRewards.Num(); ++J)
		{
			if (LockedRewards[J] == LockedRewards[I])
			{
				Names += (Names.IsEmpty() ? TEXT("") : TEXT(", ")) + LockedNames[J].ToString();
			}
		}
		Note += FString::Printf(TEXT("%s%s: %s."), Note.IsEmpty() ? TEXT("Locked  ") : TEXT("   "), *Names, *IALoadout::RequirementText(LockedRewards[I]).ToString());
	}
	const FText NoteText = FText::FromString(Note);

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 3.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 8.f, 0.f, 0.f)
			[
				SNew(SBox).WidthOverride(LabelWidth)
				[
					SNew(STextBlock).Text(Label).Font(Font(16)).ColorAndOpacity(FLinearColor(0.82f, 0.84f, 0.90f))
				]
			]
			+ SHorizontalBox::Slot().FillWidth(1.f)
			[
				Options
			]
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			LockNote([NoteText]() { return NoteText; })
		];
}

TSharedRef<SWidget> SIAGunsmith::BeamColorRow()
{
	TSharedRef<SWrapBox> Options = SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(4.f, 6.f));
	Options->AddSlot()
	[
		Chip(Owner, INVTEXT("Character"), [this]() { Working.bCustomBeamColor = false; Changed(); }, [this]() { return !Working.bCustomBeamColor; }, 0.f, 14)
	];
	TArray<FColor> Colors = IALoadout::BeamPresets();
	Colors.Add(IALoadout::GoldBeam());
	for (int32 I = 0; I < Colors.Num(); ++I)
	{
		const FColor Color = Colors[I];
		const FName Reward = I < IALoadout::BeamPresets().Num() ? IALoadout::RewardBeamColor : IALoadout::RewardGold;
		if (Has(Reward))
		{
			Options->AddSlot().VAlign(VAlign_Center)
			[
				Swatch(Owner, Shown(Color), [this, Color]() { Working.bCustomBeamColor = true; Working.BeamColor = Color; Changed(); },
					[this, Color]() { return Working.bCustomBeamColor && Working.BeamColor == Color; })
			];
		}
		else
		{
			Options->AddSlot().VAlign(VAlign_Center)
			[
				SNew(SBox).WidthOverride(40.f).HeightOverride(32.f).Padding(FMargin(3.f))
				.ToolTip(TSharedPtr<IToolTip>(MakeTip(FText::Format(INVTEXT("Locked: {0}"), IALoadout::RequirementText(Reward)))))
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(FLinearColor(Shown(Color).R * 0.18f, Shown(Color).G * 0.18f, Shown(Color).B * 0.18f))
				]
			];
		}
	}
	const bool bHasColors = Has(IALoadout::RewardBeamColor);
	const bool bHasGold = Has(IALoadout::RewardGold);
	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 3.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 8.f, 0.f, 0.f)
			[
				SNew(SBox).WidthOverride(LabelWidth)
				[
					SNew(STextBlock).Text(INVTEXT("Colour")).Font(Font(16)).ColorAndOpacity(FLinearColor(0.82f, 0.84f, 0.90f))
				]
			]
			+ SHorizontalBox::Slot().FillWidth(1.f) [ Options ]
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			LockNote([bHasColors, bHasGold]()
			{
				FString Text;
				if (!bHasColors) { Text = FString::Printf(TEXT("Locked  Six colours: %s."), *IALoadout::RequirementText(IALoadout::RewardBeamColor).ToString()); }
				if (!bHasGold) { Text += FString::Printf(TEXT("%sGold: %s."), Text.IsEmpty() ? TEXT("Locked  ") : TEXT("   "), *IALoadout::RequirementText(IALoadout::RewardGold).ToString()); }
				return FText::FromString(Text + TEXT("   In team games the beam keeps the team colour."));
			})
		];
}

TSharedRef<SWidget> SIAGunsmith::ColorRow(const FText& Label, FColor FIACosmeticLoadout::* Member)
{
	TSharedRef<SHorizontalBox> Quick = SNew(SHorizontalBox);
	for (const FColor& Color : Palette)
	{
		Quick->AddSlot().AutoWidth()
		[
			Swatch(Owner, Shown(Color), [this, Member, Color]() { Working.*Member = Color; Changed(); },
				[this, Member, Color]() { return Working.*Member == Color; })
		];
	}
	auto GetHue = [this, Member]() { float H, L; ToHueLight(Working.*Member, H, L); return H; };
	auto GetLight = [this, Member]() { float H, L; ToHueLight(Working.*Member, H, L); return L; };

	return SNew(SVerticalBox)
		.Visibility_Lambda([this]() { return Working.bCustomRifle ? EVisibility::Visible : EVisibility::Collapsed; })
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 3.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SBox).WidthOverride(LabelWidth - 44.f)
				[
					SNew(STextBlock).Text(Label).Font(Font(16)).ColorAndOpacity(FLinearColor(0.82f, 0.84f, 0.90f))
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 10.f, 0.f)
			[
				// The current colour, large.
				SNew(SBox).WidthOverride(34.f).HeightOverride(34.f)
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor_Lambda([this, Member]() -> FSlateColor { return Shown(Working.*Member); })
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center) [ Quick ]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(LabelWidth, 0.f, 0.f, 6.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 6.f, 0.f)
			[
				SNew(STextBlock).Text(INVTEXT("Hue")).Font(Font(13)).ColorAndOpacity(TextDim)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				Slider(Owner, 0.f, 355.f, 5.f, GetHue,
					[this, Member, GetLight](float Hue) { Working.*Member = FromHueLight(Hue, GetLight()); Changed(); },
					[](float) { return FText::GetEmpty(); }, 150.f)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(4.f, 0.f, 6.f, 0.f)
			[
				SNew(STextBlock).Text(INVTEXT("Light")).Font(Font(13)).ColorAndOpacity(TextDim)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				Slider(Owner, 0.05f, 0.95f, 0.05f, GetLight,
					[this, Member, GetHue](float Light) { Working.*Member = FromHueLight(GetHue(), Light); Changed(); },
					[](float) { return FText::GetEmpty(); }, 150.f)
			]
		];
}

TSharedRef<SWidget> SIAGunsmith::SlotsRow()
{
	if (!Has(IALoadout::RewardCustomRifle))
	{
		return LockNote([]() { return FText::Format(INVTEXT("Locked  Two saved designs: {0}."), IALoadout::RequirementText(IALoadout::RewardCustomRifle)); });
	}
	TSharedRef<SWrapBox> Buttons = SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(6.f, 6.f));
	for (int32 Slot = 1; Slot <= 2; ++Slot)
	{
		Buttons->AddSlot() [ Chip(Owner, FText::Format(INVTEXT("LOAD {0}"), FText::AsNumber(Slot)), [this, Slot]() { LoadSlot(Slot); }, nullptr, 0.f, 14) ];
		Buttons->AddSlot() [ Chip(Owner, FText::Format(INVTEXT("STORE {0}"), FText::AsNumber(Slot)), [this, Slot]() { StoreSlot(Slot); }, nullptr, 0.f, 14) ];
	}
	return Row(INVTEXT("Designs"), Buttons, LabelWidth);
}

// ---------------------------------------------------------------- the screen

TSharedRef<SWidget> SIAGunsmith::BuildBody()
{
	const UIAProfileSubsystem* Profile = UIAProfileSubsystem::Get(Owner.Get());
	const int32 Kills = IALoadout::LifetimeKills(Profile);
	const bool bFree = Has(IALoadout::RewardCustomRifle);
	const bool bCounter = Has(IALoadout::RewardKillCounter);

	TSharedRef<SVerticalBox> Body = SNew(SVerticalBox);
	Body->AddSlot().AutoHeight()
	[
		Note([Kills]() { return FText::Format(INVTEXT("Looks only: every rifle fires and hits the same.  Lifetime kills: {0}"), FText::AsNumber(Kills)); })
	];

	Body->AddSlot().AutoHeight() [ Section(INVTEXT("BEAM")) ];
	Body->AddSlot().AutoHeight() [ BeamColorRow() ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Style"), EField::BeamStyle) ];

	Body->AddSlot().AutoHeight() [ Section(INVTEXT("RIFLE")) ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Finish"), EField::RifleFinish) ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Livery"), EField::RifleLivery) ];
	if (bFree)
	{
		Body->AddSlot().AutoHeight().Padding(0.f, 3.f)
		[
			Row(INVTEXT("Free colours"), Toggle(Owner, [this]() { return Working.bCustomRifle; }, [this](bool bOn) { Working.bCustomRifle = bOn; Changed(); }), LabelWidth)
		];
		Body->AddSlot().AutoHeight() [ ColorRow(INVTEXT("Body"), &FIACosmeticLoadout::RifleBody) ];
		Body->AddSlot().AutoHeight() [ ColorRow(INVTEXT("Trim"), &FIACosmeticLoadout::RifleAccent) ];
		Body->AddSlot().AutoHeight() [ ColorRow(INVTEXT("Core"), &FIACosmeticLoadout::RifleCore) ];
	}
	else
	{
		Body->AddSlot().AutoHeight().Padding(0.f, 3.f)
		[
			Row(INVTEXT("Free colours"), LockedChip(INVTEXT("OFF"), IALoadout::RewardCustomRifle), LabelWidth)
		];
		Body->AddSlot().AutoHeight()
		[
			LockNote([]() { return FText::Format(INVTEXT("Locked  Free colours for body, trim and core: {0}."), IALoadout::RequirementText(IALoadout::RewardCustomRifle)); })
		];
	}

	Body->AddSlot().AutoHeight() [ Section(INVTEXT("PARTS")) ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Barrel"), EField::Barrel) ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Stock"), EField::Stock) ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Fins"), EField::Fins) ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Charm"), EField::Charm) ];
	if (bCounter)
	{
		Body->AddSlot().AutoHeight().Padding(0.f, 3.f)
		[
			Row(INVTEXT("Kill counter"), Toggle(Owner, [this]() { return Working.bKillCounter; }, [this](bool bOn) { Working.bKillCounter = bOn; Changed(); }), LabelWidth)
		];
	}
	else
	{
		Body->AddSlot().AutoHeight().Padding(0.f, 3.f)
		[
			Row(INVTEXT("Kill counter"), LockedChip(INVTEXT("OFF"), IALoadout::RewardKillCounter), LabelWidth)
		];
		Body->AddSlot().AutoHeight()
		[
			LockNote([]() { return FText::Format(INVTEXT("Locked  A ring and a display with your lifetime kills: {0}."), IALoadout::RequirementText(IALoadout::RewardKillCounter)); })
		];
	}

	Body->AddSlot().AutoHeight() [ Section(INVTEXT("KILLS")) ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Kill effect"), EField::KillEffect) ];
	Body->AddSlot().AutoHeight()
	[
		LockNote([]() { return INVTEXT("Shown on the players you frag."); })
	];

	Body->AddSlot().AutoHeight() [ Section(INVTEXT("CHARACTER")) ];
	Body->AddSlot().AutoHeight() [ FieldRow(INVTEXT("Livery"), EField::CharacterVariant) ];

	Body->AddSlot().AutoHeight() [ Section(INVTEXT("VIEW")) ];
	Body->AddSlot().AutoHeight().Padding(0.f, 3.f)
	[
		Row(INVTEXT("Turn"), Slider(Owner, -180.f, 180.f, 15.f,
			[this]() { const AIAMenuPlayerController* PC = Cast<AIAMenuPlayerController>(Owner.Get()); return PC ? PC->GetGunsmithTurn() : 0.f; },
			[this](float Degrees) { if (AIAMenuPlayerController* PC = Cast<AIAMenuPlayerController>(Owner.Get())) { PC->SetGunsmithTurn(Degrees); } },
			[](float Degrees) { return FText::Format(INVTEXT("{0}°"), FText::AsNumber(FMath::RoundToInt(Degrees))); }, 200.f), LabelWidth)
	];

	Body->AddSlot().AutoHeight() [ Section(INVTEXT("SAVED DESIGNS")) ];
	Body->AddSlot().AutoHeight() [ SlotsRow() ];
	return Body;
}

TSharedRef<SWidget> SIAGunsmith::BuildFooter()
{
	TSharedRef<SHorizontalBox> Footer = SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)
		[
			PrimaryButton(Owner, INVTEXT("SAVE"), [this]() { Save(); }, 160.f)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 12.f, 0.f)
		[
			Chip(Owner, INVTEXT("RESET"), [this]() { Reset(); }, nullptr, 110.f, 18)
		];
	if (OnBack)
	{
		Footer->AddSlot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 16.f, 0.f)
		[
			Chip(Owner, INVTEXT("BACK"), [this]() { if (OnBack) { OnBack(); } }, nullptr, 110.f, 18)
		];
	}
	Footer->AddSlot().FillWidth(1.f).VAlign(VAlign_Center)
	[
		SNew(STextBlock)
		.AutoWrapText(true)
		.Font(Font(13))
		.Text_Lambda([this]()
		{
			if (FPlatformTime::Seconds() < StatusUntil)
			{
				return Status;
			}
			return IsDirty() ? INVTEXT("Not saved yet.") : FText::GetEmpty();
		})
		.ColorAndOpacity_Lambda([this]() -> FSlateColor { return FPlatformTime::Seconds() < StatusUntil ? FLinearColor(0.6f, 0.9f, 0.6f) : TextDim; })
	];
	return Footer;
}
