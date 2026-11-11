// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SWidget.h"

struct FIAMapInfo;
struct FSlateBrush;

/**
 * Preview pictures and facts for the maps in IAMapList.h.
 * Thumbnails are textures in /Game/UI/MapThumbs/T_<MapName>, made by Tools/make_thumbnails.ps1.
 * A map without a picture shows a plain placeholder with its name.
 */
namespace IAMapPreview
{
	/** "DM-Foundry" for "/Game/Maps/DM-Foundry". */
	FString ShortName(const FIAMapInfo& Info);

	/** The thumbnail as a Slate brush, or null when the texture does not exist. Game thread only. */
	const FSlateBrush* GetThumbnail(const FIAMapInfo& Info);

	/** "4-8 players", or a default when the map is not in IAMapRecommended.inl. */
	FText RecommendedPlayers(const FIAMapInfo& Info);

	/** The picture (or the placeholder) at the given size. The map is looked up again every frame through GetIndex. */
	TSharedRef<SWidget> MakeThumbnailWidget(TFunction<int32()> GetIndex, FVector2D Size);
}
