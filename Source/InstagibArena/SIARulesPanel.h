// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SWidget.h"

class APlayerController;

/**
 * Menu pieces for the game options that rewards unlock (data in IARuleData.h):
 *   Custom Game / Host:  a RULES row (mutator toggles) and a TIME row (Day, Dusk, Night of the selected map)
 *   Campaign home:       the Apex+ Heat selector (after the campaign has an ending)
 *   Campaign briefing:   the active Heat rules and the best Heat cleared
 * Locked options show dimmed with what unlocks them. The choices are remembered in GameUserSettings.ini (InstagibArena.Rules).
 * Development: -IARulesPick="lowgrav,bigheads;2" preselects mutators and a time of day (0 day, 1 dusk, 2 night).
 */
namespace IARulesUI
{
	/** The RULES and TIME rows. GetMapIndex returns the index in IAMaps::List of the selected map. */
	TSharedRef<SWidget> BuildCustomRows(const TWeakObjectPtr<APlayerController>& Owner, TFunction<int32()> GetMapIndex);

	/** "?Mut=...?Variant=..." for the travel URL (only unlocked options), or empty. */
	FString UrlOptions(const TWeakObjectPtr<APlayerController>& Owner, int32 MapIndex);

	/** Campaign home: the Heat selector, or a line that says how to unlock it. */
	TSharedRef<SWidget> BuildHeatSelector(const TWeakObjectPtr<APlayerController>& Owner);

	/** Campaign ladder: what the current Heat adds to this match (empty widget at Heat 0 and without a record). */
	TSharedRef<SWidget> BuildHeatBriefing(const TWeakObjectPtr<APlayerController>& Owner, int32 MatchIndex);
}
