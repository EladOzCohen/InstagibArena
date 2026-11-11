// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SWidget.h"

/**
 * The loading screen shown while travelling between the menu and a match (and back).
 * It uses Unreal's MoviePlayer module, so it keeps animating while the game thread is busy loading,
 * and it works in packaged builds. Shows the map's thumbnail and name, an animation and a rotating tip.
 */
namespace IALoadingScreen
{
	/** Hooks the loading screen into map loading. Called once when the game module starts. */
	void Register();

	/** The widget itself. MapName may be a package path ("/Game/Maps/DM-Foundry") or empty. Also used for screenshots. */
	TSharedRef<SWidget> MakeWidget(const FString& MapName);

	/** The tips, with the player's current keys filled in. */
	TArray<FString> GetTips();
}
