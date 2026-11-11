// Instagib Arena

#include "IAMapPreview.h"
#include "IAMapList.h"
#include "IAMenuStyle.h"
#include "Engine/Texture2D.h"
#include "Slate/DeferredCleanupSlateBrush.h"
#include "Styling/CoreStyle.h"
#include "UObject/UObjectGlobals.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	struct FRecommended
	{
		const TCHAR* AssetPath;
		int32 Min;
		int32 Max;
	};

	const FRecommended Recommended[] = {
#include "IAMapRecommended.inl"
		{ nullptr, 2, 8 }
	};

	/** One brush per map, kept alive for the whole session. A null entry means "looked, found nothing". */
	TMap<FString, TSharedPtr<FDeferredCleanupSlateBrush>>& Cache()
	{
		static TMap<FString, TSharedPtr<FDeferredCleanupSlateBrush>> Brushes;
		return Brushes;
	}
}

namespace IAMapPreview
{
	FString ShortName(const FIAMapInfo& Info)
	{
		return FPackageName::GetShortName(FString(Info.AssetPath));
	}

	const FSlateBrush* GetThumbnail(const FIAMapInfo& Info)
	{
		const FString Name = ShortName(Info);
		if (const TSharedPtr<FDeferredCleanupSlateBrush>* Found = Cache().Find(Name))
		{
			return FDeferredCleanupSlateBrush::TrySlateBrush(*Found);
		}

		TSharedPtr<FDeferredCleanupSlateBrush> Brush;
		const FString Path = FString::Printf(TEXT("/Game/UI/MapThumbs/T_%s.T_%s"), *Name, *Name);
		if (FPackageName::DoesPackageExist(FString::Printf(TEXT("/Game/UI/MapThumbs/T_%s"), *Name)))
		{
			if (UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *Path))
			{
				Brush = FDeferredCleanupSlateBrush::CreateBrush(Texture);
			}
		}
		Cache().Add(Name, Brush);
		return FDeferredCleanupSlateBrush::TrySlateBrush(Brush);
	}

	FText RecommendedPlayers(const FIAMapInfo& Info)
	{
		int32 Min = 2;
		int32 Max = 8;
		for (const FRecommended& Entry : Recommended)
		{
			if (Entry.AssetPath && FCString::Stricmp(Entry.AssetPath, Info.AssetPath) == 0)
			{
				Min = Entry.Min;
				Max = Entry.Max;
				break;
			}
		}
		return FText::Format(INVTEXT("{0}-{1} players"), FText::AsNumber(Min), FText::AsNumber(Max));
	}

	TSharedRef<SWidget> MakeThumbnailWidget(TFunction<int32()> GetIndex, FVector2D Size)
	{
		auto Info = [GetIndex]() -> const FIAMapInfo& { return IAMaps::List[FMath::Clamp(GetIndex(), 0, IAMaps::Count - 1)]; };

		return SNew(SBox).WidthOverride(Size.X).HeightOverride(Size.Y)
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
				.BorderBackgroundColor(FLinearColor(1.f, 0.42f, 0.f, 0.7f))
				.Padding(FMargin(2.f))
				[
					SNew(SOverlay)
					// Placeholder: shown whenever the picture is missing.
					+ SOverlay::Slot()
					[
						SNew(SBorder)
						.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
						.BorderBackgroundColor(FLinearColor(0.07f, 0.08f, 0.11f))
						.HAlign(HAlign_Center)
						.VAlign(VAlign_Center)
						[
							SNew(STextBlock)
							.Text_Lambda([Info]() { return FText::FromString(Info().DisplayName); })
							.Font(IAMenu::Font(26, true))
							.ColorAndOpacity(FLinearColor(0.35f, 0.37f, 0.44f))
						]
					]
					+ SOverlay::Slot()
					[
						SNew(SImage)
						.Image_Lambda([Info]() -> const FSlateBrush* { return GetThumbnail(Info()); })
						.Visibility_Lambda([Info]() { return GetThumbnail(Info()) ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
					]
				]
			];
	}
}
