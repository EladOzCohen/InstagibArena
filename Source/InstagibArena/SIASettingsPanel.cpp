// Instagib Arena

#include "SIASettingsPanel.h"
#include "IAAudioSubsystem.h"
#include "IAInputConfig.h"
#include "IAMenuStyle.h"
#include "IASettings.h"
#include "InstagibArena.h"
#include "SIAControlsPanel.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/Text/STextBlock.h"

using namespace IAMenu;

namespace
{
	/** The crosshair as the HUD draws it, on a dark plate, at twice the size so that the choices are easy to compare. */
	class SIACrosshairPreview : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SIACrosshairPreview) {}
		SLATE_END_ARGS()

		void Construct(const FArguments&) {}

		virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(220.f, 120.f); }

		virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
			FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override
		{
			const FSlateBrush* White = FCoreStyle::Get().GetBrush("WhiteBrush");
			const FLinearColor Tint = InWidgetStyle.GetColorAndOpacityTint();
			const FVector2f Size = AllottedGeometry.GetLocalSize();

			auto Box = [&](float X, float Y, float W, float H, const FLinearColor& Color, int32 Layer)
			{
				FSlateDrawElement::MakeBox(OutDrawElements, Layer,
					AllottedGeometry.ToPaintGeometry(FVector2f(W, H), FSlateLayoutTransform(FVector2f(X, Y))),
					White, ESlateDrawEffect::None, Color * Tint);
			};

			// A plate with a darker lower half, like a floor under a horizon.
			Box(0.f, 0.f, Size.X, Size.Y * 0.55f, FLinearColor(0.16f, 0.19f, 0.26f), LayerId);
			Box(0.f, Size.Y * 0.55f, Size.X, Size.Y * 0.45f, FLinearColor(0.09f, 0.10f, 0.13f), LayerId);

			const float Zoom = 2.f * IASettings::GetCrosshairScale();
			const FLinearColor Color = IASettings::GetCrosshairColor();
			const FVector2f Center(Size.X * 0.5f, Size.Y * 0.5f);
			const int32 Style = IASettings::GetCrosshairStyle();
			const int32 Layer = LayerId + 1;
			const float Thick = FMath::Max(2.f, 1.5f * Zoom);

			auto Cross = [&]()
			{
				const float Gap = 4.f * Zoom;
				const float Len = 8.f * Zoom;
				Box(Center.X - Gap - Len, Center.Y - Thick * 0.5f, Len, Thick, Color, Layer);
				Box(Center.X + Gap, Center.Y - Thick * 0.5f, Len, Thick, Color, Layer);
				Box(Center.X - Thick * 0.5f, Center.Y - Gap - Len, Thick, Len, Color, Layer);
				Box(Center.X - Thick * 0.5f, Center.Y + Gap, Thick, Len, Color, Layer);
			};
			auto Dot = [&]()
			{
				const float Side = FMath::Max(3.f, 2.f * Zoom);
				Box(Center.X - Side * 0.5f, Center.Y - Side * 0.5f, Side, Side, Color, Layer);
			};

			switch (Style)
			{
			case 0: Cross(); break;
			case 1: Dot(); break;
			case 2:
			{
				TArray<FVector2f> Points;
				const float Radius = 8.f * Zoom;
				for (int32 Index = 0; Index <= 40; ++Index)
				{
					const float Angle = Index * UE_TWO_PI / 40.f;
					Points.Add(Center + FVector2f(FMath::Cos(Angle), FMath::Sin(Angle)) * Radius);
				}
				FSlateDrawElement::MakeLines(OutDrawElements, Layer, AllottedGeometry.ToPaintGeometry(), Points,
					ESlateDrawEffect::None, Color * Tint, true, Thick * 0.8f);
				break;
			}
			default: Cross(); Dot(); break;
			}
			return Layer + 1;
		}
	};

	TSharedRef<SWidget> SectionLabel(const FString& Title)
	{
		return SNew(STextBlock)
			.Text(FText::FromString(Title))
			.Font(Font(14, true))
			.ColorAndOpacity(FLinearColor(0.62f, 0.64f, 0.70f));
	}

	const TCHAR* const CrosshairStyleNames[] = { TEXT("Cross"), TEXT("Dot"), TEXT("Circle"), TEXT("Cross + dot") };
}

// ---------------------------------------------------------------- construction

void SIASettingsPanel::Construct(const FArguments& InArgs)
{
	Owner = InArgs._OwnerController;
	Modal = InArgs._Modal;
	ActiveTab = FMath::Clamp(InArgs._InitialTab, 0, 3);

	BuildResolutionList();
	SyncPendingVideo();

	ControlsPanel = SNew(SIAControlsPanel).OwnerController(Owner).Modal(Modal).InMatch(InArgs._InMatch);

	SAssignNew(Tabs, SWidgetSwitcher)
		.WidgetIndex_Lambda([this]() { return ActiveTab; })
		+ SWidgetSwitcher::Slot() [ BuildGameplayTab(InArgs) ]
		+ SWidgetSwitcher::Slot() [ BuildVideoTab() ]
		+ SWidgetSwitcher::Slot() [ BuildAudioTab() ]
		+ SWidgetSwitcher::Slot() [ ControlsPanel.ToSharedRef() ];

	static const TCHAR* const TabNames[] = { TEXT("GAMEPLAY"), TEXT("VIDEO"), TEXT("AUDIO"), TEXT("CONTROLS") };
	TSharedRef<SHorizontalBox> TabBar = SNew(SHorizontalBox);
	for (int32 Index = 0; Index < 4; ++Index)
	{
		TabBar->AddSlot().AutoWidth().Padding(0.f, 0.f, 8.f, 0.f)
		[
			Chip(Owner, FText::FromString(TabNames[Index]), [this, Index]() { SetTab(Index); },
				[this, Index]() { return ActiveTab == Index; }, 130.f, 16)
		];
	}

	ChildSlot
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 14.f)
		[
			TabBar
		]
		+ SVerticalBox::Slot().FillHeight(1.f)
		[
			ScrollArea(Tabs.ToSharedRef())
		]
	];
}

void SIASettingsPanel::SetTab(int32 Tab)
{
	ActiveTab = FMath::Clamp(Tab, 0, 3);
}

FReply SIASettingsPanel::OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent)
{
	// Page Up and Page Down move between the tabs.
	if (InKeyEvent.GetKey() == EKeys::PageDown || InKeyEvent.GetKey() == EKeys::PageUp)
	{
		SetTab((ActiveTab + (InKeyEvent.GetKey() == EKeys::PageDown ? 1 : 3)) % 4);
		Click(Owner);
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

// ---------------------------------------------------------------- gameplay

TSharedRef<SWidget> SIASettingsPanel::BuildGameplayTab(const FArguments& Args)
{
	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
	auto Add = [&Rows](TSharedRef<SWidget> Widget, float Top = 7.f, float Bottom = 7.f)
	{
		Rows->AddSlot().AutoHeight().Padding(0.f, Top, 0.f, Bottom)[ Widget ];
	};

	if (Args._ShowPlayerName)
	{
		Add(Row(INVTEXT("Player name"),
			SNew(SBox).WidthOverride(260.f)
			[
				SNew(SEditableTextBox)
				.Text_Lambda([]() { return FText::FromString(IASettings::GetPlayerName()); })
				.HintText(INVTEXT("Player"))
				.Font(Font(16))
				.OnTextCommitted_Lambda([](const FText& NewText, ETextCommit::Type) { IASettings::SetPlayerName(NewText.ToString()); })
			], 220.f, INVTEXT("Shown to other players. Up to 16 letters, digits, dashes and underscores count.")));
	}

	Add(Row(INVTEXT("Mouse sensitivity"),
		Slider(Owner, 10.f, 300.f, 5.f,
			[]() { return IASettings::GetMouseSensitivity() * 100.f; },
			[](float Value) { IASettings::SetMouseSensitivity(Value / 100.f); },
			[](float Value) { return FText::Format(INVTEXT("{0}%"), FText::AsNumber(FMath::RoundToInt(Value))); }),
		220.f, INVTEXT("How fast the view turns with the mouse. 100% is the default.")));

	Add(Row(INVTEXT("Field of view"),
		Slider(Owner, 70.f, 110.f, 1.f,
			[]() { return IASettings::GetFieldOfView(); },
			[](float Value) { IASettings::SetFieldOfView(Value); },
			[](float Value) { return FText::Format(INVTEXT("{0}°"), FText::AsNumber(FMath::RoundToInt(Value))); }),
		220.f, INVTEXT("How wide the view is. A wider view shows more of the arena but makes targets smaller.")));

	Add(SectionLabel("CROSSHAIR"), 14.f, 4.f);

	{
		TSharedRef<SHorizontalBox> Styles = SNew(SHorizontalBox);
		for (int32 Index = 0; Index < IASettings::CrosshairStyleCount; ++Index)
		{
			Styles->AddSlot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
			[
				Chip(Owner, FText::FromString(CrosshairStyleNames[Index]), [Index]() { IASettings::SetCrosshairStyle(Index); },
					[Index]() { return IASettings::GetCrosshairStyle() == Index; }, 96.f, 15)
			];
		}
		Add(Row(INVTEXT("Style"), Styles, 220.f));
	}
	{
		TSharedRef<SHorizontalBox> Colors = SNew(SHorizontalBox);
		static const FLinearColor Palette[IASettings::CrosshairColorCount] = {
			FLinearColor(1.0f, 1.0f, 1.0f), FLinearColor(0.25f, 1.0f, 0.3f), FLinearColor(0.2f, 0.9f, 1.0f),
			FLinearColor(1.0f, 0.9f, 0.2f), FLinearColor(1.0f, 0.5f, 0.1f), FLinearColor(1.0f, 0.2f, 0.2f) };
		for (int32 Index = 0; Index < IASettings::CrosshairColorCount; ++Index)
		{
			Colors->AddSlot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
			[
				Swatch(Owner, Palette[Index], [Index]() { IASettings::SetCrosshairColorIndex(Index); },
					[Index]() { return IASettings::GetCrosshairColorIndex() == Index; })
			];
		}
		Add(Row(INVTEXT("Colour"), Colors, 220.f));
	}
	Add(Row(INVTEXT("Size"),
		Slider(Owner, 50.f, 200.f, 10.f,
			[]() { return IASettings::GetCrosshairScale() * 100.f; },
			[](float Value) { IASettings::SetCrosshairScale(Value / 100.f); },
			[](float Value) { return FText::Format(INVTEXT("{0}%"), FText::AsNumber(FMath::RoundToInt(Value))); }),
		220.f));
	Add(Row(INVTEXT("Preview"),
		SNew(SBox).WidthOverride(220.f).HeightOverride(120.f)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.35f, 0.37f, 0.44f))
			.Padding(FMargin(2.f))
			[
				SNew(SIACrosshairPreview)
			]
		], 220.f, INVTEXT("This is how the crosshair looks in a match (shown at twice the size).")));

	Add(SectionLabel("CAMERA"), 14.f, 4.f);
	Add(Row(INVTEXT("Camera bob"),
		Toggle(Owner, []() { return IASettings::IsCameraBobEnabled(); }, [](bool bValue) { IASettings::SetCameraBobEnabled(bValue); }),
		220.f, INVTEXT("The view sways a little while you run.")));
	Add(Row(INVTEXT("View roll"),
		Toggle(Owner, []() { return IASettings::IsViewRollEnabled(); }, [](bool bValue) { IASettings::SetViewRollEnabled(bValue); }),
		220.f, INVTEXT("The view tilts when you strafe or dodge.")));
	Add(Row(INVTEXT("Reduced motion"),
		Toggle(Owner, []() { return IASettings::IsReducedMotion(); }, [](bool bValue) { IASettings::SetReducedMotion(bValue); }),
		220.f, INVTEXT("Turns off all camera movement (bob, roll and similar effects). Helps if fast motion makes you dizzy.")));

	if (Args._OnResetTutorial)
	{
		Add(SectionLabel("WELCOME SCREEN"), 14.f, 4.f);
		const TFunction<void()> OnReset = Args._OnResetTutorial;
		Add(Row(INVTEXT("Tutorial"),
			Chip(Owner, INVTEXT("RESET TUTORIAL"), [OnReset]() { OnReset(); }, nullptr, 0.f, 15),
			220.f, INVTEXT("Shows the welcome screen and the controls tour again.")));
	}

	Add(Note([]() { return INVTEXT("Changes are saved automatically."); }), 12.f, 0.f);
	return Rows;
}

// ---------------------------------------------------------------- video

void SIASettingsPanel::BuildResolutionList()
{
	Resolutions.Reset();
	UKismetSystemLibrary::GetSupportedFullscreenResolutions(Resolutions);

	const UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	const FIntPoint Desktop = Settings ? Settings->GetDesktopResolution() : FIntPoint(1920, 1080);

	// Windowed play also allows the usual smaller sizes.
	for (const FIntPoint& Common : { FIntPoint(1280, 720), FIntPoint(1600, 900), FIntPoint(1920, 1080), FIntPoint(2560, 1440), FIntPoint(3840, 2160) })
	{
		if (Common.X <= Desktop.X && Common.Y <= Desktop.Y)
		{
			Resolutions.AddUnique(Common);
		}
	}
	Resolutions.AddUnique(Desktop);
	if (Settings)
	{
		Resolutions.AddUnique(Settings->GetScreenResolution());
	}

	Resolutions.RemoveAll([](const FIntPoint& Res) { return Res.X < 1024 || Res.Y < 576; });
	Resolutions.Sort([](const FIntPoint& A, const FIntPoint& B) { return A.X != B.X ? A.X < B.X : A.Y < B.Y; });
	if (Resolutions.Num() == 0)
	{
		Resolutions.Add(FIntPoint(1280, 720));
	}
}

FIntPoint SIASettingsPanel::EffectiveResolution(EWindowMode::Type Mode, const FIntPoint& Res) const
{
	const UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	return (Mode == EWindowMode::WindowedFullscreen && Settings) ? Settings->GetDesktopResolution() : Res;
}

void SIASettingsPanel::SyncPendingVideo()
{
	if (const UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr)
	{
		PendingMode = Settings->GetFullscreenMode();
		PendingResolution = Settings->GetScreenResolution();
		// Pick the nearest entry of the list.
		int32 Best = 0;
		int64 BestDistance = MAX_int64;
		for (int32 Index = 0; Index < Resolutions.Num(); ++Index)
		{
			const int64 Dx = Resolutions[Index].X - PendingResolution.X;
			const int64 Dy = Resolutions[Index].Y - PendingResolution.Y;
			if (Dx * Dx + Dy * Dy < BestDistance)
			{
				BestDistance = Dx * Dx + Dy * Dy;
				Best = Index;
			}
		}
		PendingResolution = Resolutions[Best];
	}
}

bool SIASettingsPanel::HasPendingVideo() const
{
	const UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	if (!Settings)
	{
		return false;
	}
	if (PendingMode != Settings->GetFullscreenMode())
	{
		return true;
	}
	// Borderless always uses the desktop resolution, so only the mode counts there.
	return PendingMode != EWindowMode::WindowedFullscreen
		&& EffectiveResolution(PendingMode, PendingResolution) != Settings->GetScreenResolution();
}

void SIASettingsPanel::ApplyPendingVideo()
{
	UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	if (!Settings || !HasPendingVideo() || (Modal.IsValid() && Modal->IsOpen()))
	{
		return;
	}

	PreviousResolution = Settings->GetScreenResolution();
	PreviousMode = Settings->GetFullscreenMode();

	const FIntPoint Target = EffectiveResolution(PendingMode, PendingResolution);
	UE_LOG(LogInstagib, Log, TEXT("Video: applying %dx%d mode %d (was %dx%d mode %d)"), Target.X, Target.Y,
		static_cast<int32>(PendingMode), PreviousResolution.X, PreviousResolution.Y, static_cast<int32>(PreviousMode));

	Settings->SetFullscreenMode(PendingMode);
	Settings->SetScreenResolution(Target);
	Settings->ApplyResolutionSettings(false);

	if (!Modal.IsValid())
	{
		KeepVideo();
		return;
	}

	const TWeakPtr<FIAModal> WeakModal = Modal;
	Modal->Show(INVTEXT("KEEP THESE SETTINGS?"),
		[WeakModal]()
		{
			const TSharedPtr<FIAModal> Pinned = WeakModal.Pin();
			const int32 Seconds = Pinned.IsValid() ? FMath::CeilToInt(Pinned->GetSecondsLeft()) : 0;
			return FText::Format(INVTEXT("If you can read this, the new display settings work. They will be undone in {0} seconds unless you keep them."),
				FText::AsNumber(Seconds));
		},
		{ { INVTEXT("KEEP"), [this]() { KeepVideo(); }, true }, { INVTEXT("REVERT"), [this]() { RevertVideo(); }, false } },
		[this]() { RevertVideo(); }, 10.f);
}

void SIASettingsPanel::KeepVideo()
{
	if (UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr)
	{
		Settings->ConfirmVideoMode();
		Settings->SaveSettings();
	}
	UE_LOG(LogInstagib, Log, TEXT("Video: new display settings kept"));
	SyncPendingVideo();
}

void SIASettingsPanel::RevertVideo()
{
	if (UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr)
	{
		Settings->SetFullscreenMode(PreviousMode);
		Settings->SetScreenResolution(PreviousResolution);
		Settings->ApplyResolutionSettings(false);
		Settings->ConfirmVideoMode();
		Settings->SaveSettings();
	}
	UE_LOG(LogInstagib, Log, TEXT("Video: display settings reverted to %dx%d mode %d"), PreviousResolution.X, PreviousResolution.Y, static_cast<int32>(PreviousMode));
	SyncPendingVideo();
}

TSharedRef<SWidget> SIASettingsPanel::BuildVideoTab()
{
	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
	auto Add = [&Rows](TSharedRef<SWidget> Widget, float Top = 7.f, float Bottom = 7.f)
	{
		Rows->AddSlot().AutoHeight().Padding(0.f, Top, 0.f, Bottom)[ Widget ];
	};
	auto Settings = []() -> UGameUserSettings* { return GEngine ? GEngine->GetGameUserSettings() : nullptr; };

	// ---- display mode and resolution (applied with the APPLY button)
	{
		struct FModeInfo { const TCHAR* Name; EWindowMode::Type Mode; };
		static const FModeInfo Modes[] = {
			{ TEXT("Fullscreen"), EWindowMode::Fullscreen },
			{ TEXT("Borderless"), EWindowMode::WindowedFullscreen },
			{ TEXT("Windowed"), EWindowMode::Windowed } };
		TSharedRef<SHorizontalBox> Chips = SNew(SHorizontalBox);
		for (const FModeInfo& Info : Modes)
		{
			const EWindowMode::Type Mode = Info.Mode;
			Chips->AddSlot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
			[
				Chip(Owner, FText::FromString(Info.Name), [this, Mode]() { PendingMode = Mode; },
					[this, Mode]() { return PendingMode == Mode; }, 110.f, 15)
			];
		}
		Add(Row(INVTEXT("Display mode"), Chips, 220.f,
			INVTEXT("Fullscreen takes over the screen. Borderless is a full-screen window at your desktop resolution (easiest to switch away from). Windowed can be any size.")));
	}
	Add(Row(INVTEXT("Resolution"),
		Stepper(Owner,
			[this]() -> FText
			{
				const FIntPoint Res = EffectiveResolution(PendingMode, PendingResolution);
				return FText::Format(INVTEXT("{0} x {1}{2}"), FText::AsNumber(Res.X, &FNumberFormattingOptions::DefaultNoGrouping()),
					FText::AsNumber(Res.Y, &FNumberFormattingOptions::DefaultNoGrouping()),
					PendingMode == EWindowMode::WindowedFullscreen ? INVTEXT(" (desktop)") : FText::GetEmpty());
			},
			[this]()
			{
				const int32 Index = Resolutions.IndexOfByKey(PendingResolution);
				PendingResolution = Resolutions[FMath::Max(0, (Index == INDEX_NONE ? 0 : Index) - 1)];
			},
			[this]()
			{
				const int32 Index = Resolutions.IndexOfByKey(PendingResolution);
				PendingResolution = Resolutions[FMath::Min(Resolutions.Num() - 1, (Index == INDEX_NONE ? 0 : Index) + 1)];
			}, 230.f),
		220.f, INVTEXT("Only the sizes your screen supports are listed. Borderless always uses the desktop resolution.")));
	Add(Row(FText::GetEmpty(),
		SNew(SHorizontalBox)
		.Visibility_Lambda([this]() { return HasPendingVideo() ? EVisibility::Visible : EVisibility::Collapsed; })
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 14.f, 0.f)
		[
			PrimaryButton(Owner, INVTEXT("APPLY"), [this]() { ApplyPendingVideo(); }, 150.f)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			Note([]() { return INVTEXT("You get 10 seconds to confirm."); })
		], 220.f), 2.f, 8.f);

	Add(SectionLabel("PERFORMANCE"), 14.f, 4.f);

	Add(Row(INVTEXT("VSync"),
		Toggle(Owner,
			[Settings]() { const UGameUserSettings* S = Settings(); return S && S->IsVSyncEnabled(); },
			[Settings](bool bValue) { if (UGameUserSettings* S = Settings()) { S->SetVSyncEnabled(bValue); S->ApplyNonResolutionSettings(); S->SaveSettings(); } }),
		220.f, INVTEXT("Waits for the screen to refresh. Stops tearing but can add a little input delay.")));

	{
		struct FCap { const TCHAR* Name; float Value; };
		static const FCap Caps[] = { { TEXT("60"), 60.f }, { TEXT("120"), 120.f }, { TEXT("144"), 144.f }, { TEXT("Unlimited"), 0.f } };
		TSharedRef<SHorizontalBox> Chips = SNew(SHorizontalBox);
		for (const FCap& Cap : Caps)
		{
			const float Value = Cap.Value;
			Chips->AddSlot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
			[
				Chip(Owner, FText::FromString(Cap.Name),
					[Settings, Value]() { if (UGameUserSettings* S = Settings()) { S->SetFrameRateLimit(Value); S->ApplyNonResolutionSettings(); S->SaveSettings(); } },
					[Settings, Value]() { const UGameUserSettings* S = Settings(); return S && FMath::IsNearlyEqual(S->GetFrameRateLimit(), Value); }, 84.f, 15)
			];
		}
		Add(Row(INVTEXT("FPS limit"), Chips, 220.f, INVTEXT("The most frames per second the game draws. A lower limit saves power and heat.")));
	}

	{
		static const TCHAR* const Names[] = { TEXT("Low"), TEXT("Medium"), TEXT("High"), TEXT("Epic") };
		TSharedRef<SHorizontalBox> Chips = SNew(SHorizontalBox);
		for (int32 Level = 0; Level < 4; ++Level)
		{
			Chips->AddSlot().AutoWidth().Padding(0.f, 0.f, 6.f, 0.f)
			[
				Chip(Owner, FText::FromString(Names[Level]),
					[Settings, Level]()
					{
						if (UGameUserSettings* S = Settings())
						{
							S->SetOverallScalabilityLevel(Level);
							S->ApplyNonResolutionSettings();
							S->SaveSettings();
							IASettings::SetMotionBlurEnabled(IASettings::IsMotionBlurEnabled());
						}
					},
					[Settings, Level]() { const UGameUserSettings* S = Settings(); return S && S->GetOverallScalabilityLevel() == Level; }, 84.f, 15)
			];
		}
		Add(Row(INVTEXT("Quality"), Chips, 220.f, INVTEXT("Sets shadows, effects, textures and more at once. Choose a lower level if the game runs slowly.")));
	}

	Add(Row(INVTEXT("Motion blur"),
		Toggle(Owner, []() { return IASettings::IsMotionBlurEnabled(); }, [](bool bValue) { IASettings::SetMotionBlurEnabled(bValue); }),
		220.f, INVTEXT("Smears the picture while the view moves fast. Turn it off for a sharper image.")));

	Add(SectionLabel("INTERFACE"), 14.f, 4.f);
	Add(Row(INVTEXT("UI scale"),
		Stepper(Owner,
			[]() { return FText::Format(INVTEXT("{0}%"), FText::AsNumber(FMath::RoundToInt(IASettings::GetUiScale() * 100.f))); },
			[]() { IASettings::SetUiScale(IASettings::GetUiScale() - 0.1f); },
			[]() { IASettings::SetUiScale(IASettings::GetUiScale() + 0.1f); }, 110.f),
		220.f, INVTEXT("Makes the menus smaller or larger on top of the automatic size.")));

	Add(Note([]() { return INVTEXT("Resolution and display mode change when you press APPLY. Everything else is applied at once."); }), 12.f, 0.f);
	return Rows;
}

// ---------------------------------------------------------------- audio

TSharedRef<SWidget> SIASettingsPanel::BuildAudioTab()
{
	const TWeakObjectPtr<APlayerController> OwnerCopy = Owner;
	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
	auto Add = [&Rows](TSharedRef<SWidget> Widget)
	{
		Rows->AddSlot().AutoHeight().Padding(0.f, 7.f)[ Widget ];
	};
	auto Percent = [](float Value) { return FText::Format(INVTEXT("{0}%"), FText::AsNumber(FMath::RoundToInt(Value))); };

	Add(Row(INVTEXT("Music volume"),
		Slider(Owner, 0.f, 100.f, 5.f,
			[OwnerCopy]() { const UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(OwnerCopy.Get()); return Audio ? Audio->GetMusicVolume() * 100.f : 0.f; },
			[OwnerCopy](float Value) { if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(OwnerCopy.Get())) { Audio->SetMusicVolume(Value / 100.f); } },
			Percent), 220.f));
	Add(Row(INVTEXT("Effects volume"),
		Slider(Owner, 0.f, 100.f, 5.f,
			[OwnerCopy]() { const UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(OwnerCopy.Get()); return Audio ? Audio->GetSfxVolume() * 100.f : 0.f; },
			[OwnerCopy](float Value) { if (UIAAudioSubsystem* Audio = UIAAudioSubsystem::Get(OwnerCopy.Get())) { Audio->SetSfxVolume(Value / 100.f); } },
			Percent), 220.f, INVTEXT("Shots, footsteps, hits and the menu sounds.")));
	Add(Row(INVTEXT("Mute when unfocused"),
		Toggle(Owner, []() { return IASettings::GetMuteWhenUnfocused(); }, [](bool bValue) { IASettings::SetMuteWhenUnfocused(bValue); }),
		220.f, INVTEXT("Silences the game while another window is in front.")));
	Rows->AddSlot().AutoHeight().Padding(0.f, 12.f, 0.f, 0.f)
	[
		Note([]() { return INVTEXT("Changes are saved automatically."); })
	];
	return Rows;
}

// ---------------------------------------------------------------- developer check

bool SIASettingsPanel::DevCommand(const FString& Command)
{
	FString Name = Command;
	FString Value;
	Command.Split(TEXT("="), &Name, &Value);

	if (Name == TEXT("tab")) { SetTab(FCString::Atoi(*Value)); return true; }
	if (Name == TEXT("mode"))
	{
		PendingMode = Value == TEXT("0") ? EWindowMode::Fullscreen : Value == TEXT("1") ? EWindowMode::WindowedFullscreen : EWindowMode::Windowed;
		return true;
	}
	if (Name == TEXT("res"))
	{
		FString X, Y;
		if (Value.Split(TEXT("x"), &X, &Y))
		{
			PendingResolution = FIntPoint(FCString::Atoi(*X), FCString::Atoi(*Y));
			if (!Resolutions.Contains(PendingResolution)) { Resolutions.Add(PendingResolution); }
		}
		return true;
	}
	if (Name == TEXT("apply")) { ApplyPendingVideo(); return true; }
	if (Name == TEXT("keep")) { if (Modal.IsValid() && Modal->IsOpen()) { Modal->Hide(); KeepVideo(); } return true; }
	if (Name == TEXT("revert")) { if (Modal.IsValid() && Modal->IsOpen()) { Modal->Cancel(); } return true; }
	if (Name == TEXT("rebind"))
	{
		FString Id, KeyName;
		if (Value.Split(TEXT(":"), &Id, &KeyName)) { ControlsPanel->DevRebind(FName(*Id), FKey(*KeyName)); }
		return true;
	}
	if (Name == TEXT("listen")) { ControlsPanel->DevListen(FName(*Value)); return true; }
	if (Name == TEXT("reset-keys")) { ControlsPanel->DevReset(); return true; }
	return false;
}
