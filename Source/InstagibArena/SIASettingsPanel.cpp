// Instagib Arena

#include "SIASettingsPanel.h"
#include "IAAudioSubsystem.h"
#include "IAMenuStyle.h"
#include "IASettings.h"
#include "GameFramework/PlayerController.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

void SIASettingsPanel::Construct(const FArguments& InArgs)
{
	const TWeakObjectPtr<APlayerController> Owner = InArgs._OwnerController;

	// Volumes move in steps of ten percent.
	auto VolumeText = [Owner](bool bMusic)
	{
		const UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(Owner.Get());
		const float Volume = Audio ? (bMusic ? Audio->GetMusicVolume() : Audio->GetSfxVolume()) : 0.f;
		return FText::Format(INVTEXT("{0}%"), FText::AsNumber(FMath::RoundToInt(Volume * 100.f)));
	};
	auto StepVolume = [Owner](bool bMusic, float Delta)
	{
		if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(Owner.Get()))
		{
			const float Current = bMusic ? Audio->GetMusicVolume() : Audio->GetSfxVolume();
			const float Next = FMath::RoundToFloat(Current * 10.f + Delta) / 10.f;
			if (bMusic) { Audio->SetMusicVolume(Next); } else { Audio->SetSfxVolume(Next); }
		}
	};

	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);

	if (InArgs._ShowPlayerName)
	{
		Rows->AddSlot().AutoHeight().Padding(0.f, 7.f)
		[
			IAMenu::Row(INVTEXT("Player name"),
				SNew(SBox).WidthOverride(260.f)
				[
					SNew(SEditableTextBox)
					.Text_Lambda([]() { return FText::FromString(IASettings::GetPlayerName()); })
					.HintText(INVTEXT("Player"))
					.Font(IAMenu::Font(16))
					.OnTextCommitted_Lambda([](const FText& NewText, ETextCommit::Type) { IASettings::SetPlayerName(NewText.ToString()); })
				])
		];
	}

	Rows->AddSlot().AutoHeight().Padding(0.f, 7.f)
	[
		IAMenu::Row(INVTEXT("Music volume"),
			IAMenu::Stepper(Owner, [=]() { return VolumeText(true); }, [=]() { StepVolume(true, -1.f); }, [=]() { StepVolume(true, 1.f); }))
	];
	Rows->AddSlot().AutoHeight().Padding(0.f, 7.f)
	[
		IAMenu::Row(INVTEXT("Effects volume"),
			IAMenu::Stepper(Owner, [=]() { return VolumeText(false); }, [=]() { StepVolume(false, -1.f); }, [=]() { StepVolume(false, 1.f); }))
	];
	Rows->AddSlot().AutoHeight().Padding(0.f, 7.f)
	[
		IAMenu::Row(INVTEXT("Mouse sensitivity"),
			IAMenu::Stepper(Owner,
				[]() { return FText::Format(INVTEXT("{0}%"), FText::AsNumber(FMath::RoundToInt(IASettings::GetMouseSensitivity() * 100.f))); },
				[]() { IASettings::SetMouseSensitivity(FMath::RoundToFloat(IASettings::GetMouseSensitivity() * 10.f - 1.f) / 10.f); },
				[]() { IASettings::SetMouseSensitivity(FMath::RoundToFloat(IASettings::GetMouseSensitivity() * 10.f + 1.f) / 10.f); }))
	];
	Rows->AddSlot().AutoHeight().Padding(0.f, 7.f)
	[
		IAMenu::Row(INVTEXT("Field of view"),
			IAMenu::Stepper(Owner,
				[]() { return FText::Format(INVTEXT("{0}°"), FText::AsNumber(FMath::RoundToInt(IASettings::GetFieldOfView()))); },
				[]() { IASettings::SetFieldOfView(IASettings::GetFieldOfView() - 5.f); },
				[]() { IASettings::SetFieldOfView(IASettings::GetFieldOfView() + 5.f); }))
	];
	Rows->AddSlot().AutoHeight().Padding(0.f, 7.f)
	[
		IAMenu::Row(INVTEXT("Display"),
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
			[
				IAMenu::Chip(Owner, INVTEXT("Fullscreen"), []() { IASettings::ApplyDisplayMode(true); }, []() { return IASettings::IsFullscreen(); }, 130.f)
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				IAMenu::Chip(Owner, INVTEXT("Windowed"), []() { IASettings::ApplyDisplayMode(false); }, []() { return !IASettings::IsFullscreen(); }, 130.f)
			])
	];
	Rows->AddSlot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
	[
		IAMenu::Note([]() { return INVTEXT("Changes are saved automatically."); })
	];

	ChildSlot
	[
		Rows
	];
}
