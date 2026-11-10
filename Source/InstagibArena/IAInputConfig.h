// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"

/** One action whose key the player may change. */
struct FIABindingInfo
{
	const TCHAR* Id;      // stable name, also the key in the config file
	const TCHAR* Label;   // shown in the controls screen
	FKey DefaultKey;
};

/**
 * The table of rebindable keys and the player's choices.
 *
 * To add a rebindable action, add a line to the table in IAInputConfig.cpp, then read its key with
 * IAInput::GetKey("YourId") where the input is mapped (see AIAPlayerController::BuildInput).
 * The controls screen lists every line of the table automatically.
 * Mouse look and Esc (pause) are fixed and not in the table.
 * Changes are saved to GameUserSettings.ini and apply when the next match starts.
 */
namespace IAInput
{
	INSTAGIBARENA_API const TArray<FIABindingInfo>& GetBindings();

	/** The key the player uses for this action: their own choice, or the default. */
	INSTAGIBARENA_API FKey GetKey(FName Id);

	/** Saves a new key for the action. */
	INSTAGIBARENA_API void SetKey(FName Id, FKey Key);

	/** Forgets every change. */
	INSTAGIBARENA_API void ResetAll();

	/** The Id of another action that already uses this key, or NAME_None. For warning about clashes. */
	INSTAGIBARENA_API FName FindActionUsingKey(FKey Key, FName ExceptId);
}
