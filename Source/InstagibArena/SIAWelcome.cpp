// Instagib Arena

#include "SIAWelcome.h"
#include "IAMenuStyle.h"
#include "IASettings.h"
#include "SIAControlsPanel.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

void SIAWelcome::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	OnFinished = InArgs._OnFinished;
	NameText = IASettings::GetPlayerName();

	SAssignNew(StepHost, SBox);
	StepHost->SetContent(BuildStep(0));

	TSharedRef<SBorder> Panel = SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(0.02f, 0.024f, 0.035f, 0.98f))
		.Padding(FMargin(48.f, 36.f))
		[
			SNew(SBox).WidthOverride(720.f)
			[
				StepHost.ToSharedRef()
			]
		];
	KeepNavigationInside(Panel.Get());

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.74f))
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		[
			Panel
		]
	];
}

void SIAWelcome::ShowStep(int32 NewStep)
{
	Step = FMath::Clamp(NewStep, 0, 1);
	StepHost->SetContent(BuildStep(Step));
	FocusFirst(StepHost.ToSharedRef());
}

FReply SIAWelcome::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape)
	{
		Click(Owner);
		Finish();
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

void SIAWelcome::Finish()
{
	const FString Name = NameText.TrimStartAndEnd();
	if (!Name.IsEmpty())
	{
		IASettings::SetPlayerName(Name);
	}
	IASettings::SetTutorialDone(true);
	if (OnFinished)
	{
		OnFinished();
	}
}

TSharedRef<SWidget> SIAWelcome::BuildStep(int32 StepIndex)
{
	if (StepIndex == 0)
	{
		return SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight()
			[
				SNew(STextBlock).Text(INVTEXT("WELCOME")).Font(Font(40, true)).ColorAndOpacity(Accent)
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f, 0.f, 0.f)
			[
				SNew(STextBlock).Text(INVTEXT("Instagib Arena: one shot, one kill. Two quick questions, then a short look at the controls."))
				.AutoWrapText(true).Font(Font(17)).ColorAndOpacity(FLinearColor(0.82f, 0.84f, 0.90f))
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f, 0.f, 18.f)
			[
				SNew(SBox).HeightOverride(2.f)
				[
					SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(1.f, 0.42f, 0.f, 0.55f))
				]
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f)
			[
				Row(INVTEXT("Your name"),
					SNew(SBox).WidthOverride(300.f)
					[
						SNew(SEditableTextBox)
						.Text_Lambda([this]() { return FText::FromString(NameText); })
						.HintText(INVTEXT("Player"))
						.Font(Font(18))
						.OnTextChanged_Lambda([this](const FText& Text) { NameText = Text.ToString().Left(16); })
					], 170.f, INVTEXT("Other players see this name. You can change it later in Settings."))
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f)
			[
				Row(INVTEXT("Display"),
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
					[
						Chip(Owner, INVTEXT("Fullscreen"), []() { IASettings::ApplyDisplayMode(true); }, []() { return IASettings::IsFullscreen(); }, 140.f)
					]
					+ SHorizontalBox::Slot().AutoWidth()
					[
						Chip(Owner, INVTEXT("Windowed"), []() { IASettings::ApplyDisplayMode(false); }, []() { return !IASettings::IsFullscreen(); }, 140.f)
					], 170.f)
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
			[
				Note([]() { return INVTEXT("More display options are in Settings, under Video."); })
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 26.f, 0.f, 0.f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)
				[
					PrimaryButton(Owner, INVTEXT("NEXT"), [this]() { ShowStep(1); }, 220.f)
				]
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					Chip(Owner, INVTEXT("SKIP"), [this]() { Finish(); }, nullptr, 110.f, 18)
				]
			];
	}

	auto Tip = [](const TCHAR* Text)
	{
		return SNew(STextBlock).Text(FText::FromString(Text)).AutoWrapText(true).Font(Font(16)).ColorAndOpacity(FLinearColor(0.82f, 0.84f, 0.90f));
	};

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(STextBlock).Text(INVTEXT("THE CONTROLS")).Font(Font(40, true)).ColorAndOpacity(Accent)
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f, 0.f, 16.f)
		[
			SNew(SBox).HeightOverride(2.f)
			[
				SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(FLinearColor(1.f, 0.42f, 0.f, 0.55f))
			]
		]
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(SIAControlsPanel).OwnerController(Owner).ReadOnly(true)
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
		[
			Tip(TEXT("Every hit is a kill, so aim carefully and keep moving. You can change any key in Settings, under Controls."))
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 22.f, 0.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)
			[
				PrimaryButton(Owner, INVTEXT("LET'S PLAY"), [this]() { Finish(); }, 220.f)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				Chip(Owner, INVTEXT("BACK"), [this]() { ShowStep(0); }, nullptr, 110.f, 18)
			]
		];
}
