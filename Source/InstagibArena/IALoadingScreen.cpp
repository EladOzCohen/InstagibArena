// Instagib Arena

#include "IALoadingScreen.h"
#include "IAInputConfig.h"
#include "IAMapList.h"
#include "IAMapPreview.h"
#include "IAMenuStyle.h"
#include "InstagibArena.h"
#include "MoviePlayer.h"
#include "Misc/CoreDelegates.h"
#include "Styling/CoreStyle.h"
#include "UObject/UObjectGlobals.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	const FIAMapInfo* FindMap(const FString& MapName)
	{
		FString Clean = MapName;
		Clean.Split(TEXT("?"), &Clean, nullptr);
		const FString Short = FPackageName::GetShortName(Clean);
		for (const FIAMapInfo& Info : IAMaps::List)
		{
			if (Short.Equals(FPackageName::GetShortName(FString(Info.AssetPath)), ESearchCase::IgnoreCase))
			{
				return &Info;
			}
		}
		return nullptr;
	}

	void OnPreLoadMap(const FWorldContext& Context, const FString& MapName)
	{
		// Not in the editor, not on a server, and not for the very first map (the game starts without delay).
		static bool bFirstMap = true;
		const bool bSkip = bFirstMap;
		bFirstMap = false;
		if (bSkip || GIsEditor || IsRunningDedicatedServer() || IsRunningCommandlet() || !IsMoviePlayerEnabled() || !GetMoviePlayer() || !Context.World())
		{
			return;
		}

		FLoadingScreenAttributes Attributes;
		Attributes.WidgetLoadingScreen = IALoadingScreen::MakeWidget(MapName);
		Attributes.MinimumLoadingScreenDisplayTime = 2.2f;
		Attributes.bAutoCompleteWhenLoadingCompletes = true;
		Attributes.bMoviesAreSkippable = false;
		Attributes.bWaitForManualStop = false;
		Attributes.bAllowInEarlyStartup = false;
		GetMoviePlayer()->SetupLoadingScreen(Attributes);
		UE_LOG(LogInstagib, Log, TEXT("LoadingScreen: shown for %s"), *MapName);
	}
}

namespace IALoadingScreen
{
	void Register()
	{
		if (IsRunningDedicatedServer() || IsRunningCommandlet())
		{
			return;
		}
		FCoreUObjectDelegates::PreLoadMapWithContext.AddStatic(&OnPreLoadMap);
	}

	TArray<FString> GetTips()
	{
		const FString Scoreboard = IAMenu::KeyText(IAInput::GetKey(TEXT("Scoreboard"))).ToString();
		const FString Jump = IAMenu::KeyText(IAInput::GetKey(TEXT("Jump"))).ToString();
		return {
			TEXT("Every hit is a kill. Stay calm and line up the shot."),
			TEXT("Double-tap a movement key to dodge sideways, forward or back."),
			FString::Printf(TEXT("Press %s again in the air for a double jump."), *Jump),
			TEXT("Keep moving. A target that stands still is an easy target."),
			FString::Printf(TEXT("Hold %s to see the scoreboard."), *Scoreboard),
			TEXT("Listen. Footsteps and landings give away where enemies are."),
			TEXT("Use height. Ledges and catwalks give you a long view."),
			TEXT("In Team Deathmatch, check the colour before you shoot."),
			TEXT("New here? Start the bots on Rookie to learn the maps."),
			TEXT("Pick a crosshair you can see on every map: Settings, Gameplay."),
			TEXT("Find a mouse sensitivity you can control. The best aim is a calm one."),
			TEXT("Esc opens the pause menu. In a multiplayer game the match keeps running."),
		};
	}

	TSharedRef<SWidget> MakeWidget(const FString& MapName)
	{
		const FIAMapInfo* Map = FindMap(MapName);
		const FString Title = Map ? FString(Map->DisplayName) : (MapName.Contains(TEXT("MainMenu")) ? FString(TEXT("Main menu")) : FPackageName::GetShortName(MapName));
		const FString Subtitle = Map ? FString(Map->Description) : FString();
		const FSlateBrush* Thumbnail = Map ? IAMapPreview::GetThumbnail(*Map) : nullptr;

		const TArray<FString> Tips = GetTips();
		const double Start = FPlatformTime::Seconds();
		const int32 FirstTip = FMath::RandRange(0, Tips.Num() - 1);

		auto TipIndex = [Tips, Start, FirstTip]() { return (FirstTip + static_cast<int32>((FPlatformTime::Seconds() - Start) / 4.5)) % Tips.Num(); };

		const FLinearColor Orange = IAMenu::Accent;

		TSharedRef<SWidget> Content = SNew(SOverlay)
			// Left: the picture of the map.
			+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(FMargin(140.f, 0.f, 0.f, 40.f))
			[
				SNew(SBox).WidthOverride(960.f).HeightOverride(540.f)
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(FLinearColor(1.f, 0.42f, 0.f, 0.85f))
					.Padding(FMargin(3.f))
					[
						SNew(SOverlay)
						+ SOverlay::Slot()
						[
							SNew(SBorder)
							.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
							.BorderBackgroundColor(FLinearColor(0.06f, 0.07f, 0.10f))
						]
						+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
						[
							SNew(STextBlock)
							.Text(INVTEXT("INSTAGIB\nARENA"))
							.Justification(ETextJustify::Center)
							.Font(IAMenu::Font(72, true))
							.ColorAndOpacity(FLinearColor(0.16f, 0.17f, 0.22f))
							.Visibility(Thumbnail ? EVisibility::Collapsed : EVisibility::HitTestInvisible)
						]
						+ SOverlay::Slot()
						[
							SNew(SImage).Image(Thumbnail).Visibility(Thumbnail ? EVisibility::HitTestInvisible : EVisibility::Collapsed)
						]
					]
				]
			]
			// Right: name, description and the animated word.
			+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(FMargin(1160.f, 0.f, 80.f, 40.f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(STextBlock).Text(FText::FromString(Title.ToUpper())).Font(IAMenu::Font(64, true)).ColorAndOpacity(FLinearColor::White)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 10.f, 0.f, 0.f)
				[
					SNew(STextBlock).Text(FText::FromString(Subtitle)).AutoWrapText(true).WrapTextAt(620.f)
					.Font(IAMenu::Font(24)).ColorAndOpacity(IAMenu::TextDim)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 44.f, 0.f, 0.f)
				[
					SNew(STextBlock)
					.Text_Lambda([Start]()
					{
						const int32 Dots = static_cast<int32>((FPlatformTime::Seconds() - Start) * 3.0) % 4;
						return FText::FromString(FString(TEXT("LOADING")) + FString::ChrN(Dots, TEXT('.')));
					})
					.Font(IAMenu::Font(34, true)).ColorAndOpacity(Orange)
				]
			]
			// Bottom: the tip.
			+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Bottom).Padding(FMargin(140.f, 0.f, 140.f, 120.f))
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 24.f, 0.f)
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(Orange)
					.Padding(FMargin(14.f, 6.f))
					[
						SNew(STextBlock).Text(INVTEXT("TIP")).Font(IAMenu::Font(22, true)).ColorAndOpacity(FLinearColor::Black)
					]
				]
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text_Lambda([Tips, TipIndex]() { return FText::FromString(Tips[TipIndex()]); })
					.Font(IAMenu::Font(30))
					.ColorAndOpacity_Lambda([Start]() -> FSlateColor
					{
						// Fades in and out every 4.5 seconds.
						const double Phase = FMath::Fmod((FPlatformTime::Seconds() - Start), 4.5) / 4.5;
						const float Alpha = static_cast<float>(FMath::Clamp(FMath::Min(Phase / 0.12, (1.0 - Phase) / 0.12), 0.0, 1.0));
						return FLinearColor(0.86f, 0.88f, 0.94f, Alpha);
					})
				]
			]
			// Very bottom: a bar with a bright block sweeping across it.
			+ SOverlay::Slot().VAlign(VAlign_Bottom)
			[
				SNew(SBox).HeightOverride(8.f)
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(FLinearColor(0.08f, 0.09f, 0.12f))
					.Padding(FMargin(0.f))
					[
						SNew(SBox)
						.Padding_Lambda([Start]()
						{
							const double Phase = FMath::Fmod((FPlatformTime::Seconds() - Start) * 0.7, 1.0);
							return FMargin(static_cast<float>(Phase * 1920.0 - 360.0), 0.f, 0.f, 0.f);
						})
						.HAlign(HAlign_Left)
						[
							SNew(SBox).WidthOverride(360.f)
							[
								SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(Orange)
							]
						]
					]
				]
			];

		// The picture is laid out for 1920x1080 and scaled to fit the screen. The dark background covers any extra width.
		return SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.012f, 0.014f, 0.022f))
			.Padding(FMargin(0.f))
			[
				SNew(SScaleBox)
				.Stretch(EStretch::ScaleToFit)
				[
					SNew(SBox).WidthOverride(1920.f).HeightOverride(1080.f)
					[
						Content
					]
				]
			];
	}
}
