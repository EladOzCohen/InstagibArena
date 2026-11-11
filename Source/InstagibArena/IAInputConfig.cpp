// Instagib Arena

#include "IAInputConfig.h"
#include "Misc/ConfigCacheIni.h"

namespace
{
	const TCHAR* const KeySection = TEXT("InstagibArena.Keys");
}

namespace IAInput
{
	const TArray<FIABindingInfo>& GetBindings()
	{
		// Add new rebindable actions here.
		static const TArray<FIABindingInfo> Bindings = {
			{ TEXT("Forward"),    TEXT("Move forward"),   EKeys::W },
			{ TEXT("Back"),       TEXT("Move back"),      EKeys::S },
			{ TEXT("Left"),       TEXT("Move left"),      EKeys::A },
			{ TEXT("Right"),      TEXT("Move right"),     EKeys::D },
			{ TEXT("Jump"),       TEXT("Jump"),           EKeys::SpaceBar },
			{ TEXT("Fire"),       TEXT("Fire"),           EKeys::LeftMouseButton },
			{ TEXT("Scoreboard"), TEXT("Scoreboard"),     EKeys::Tab },
			{ TEXT("Crouch"),     TEXT("Crouch (hold)"),  EKeys::LeftControl },
			{ TEXT("Walk"),       TEXT("Slow walk (hold)"), EKeys::LeftShift },
		};
		return Bindings;
	}

	FKey GetKey(FName Id)
	{
		FString Saved;
		if (GConfig->GetString(KeySection, *Id.ToString(), Saved, GGameUserSettingsIni) && !Saved.IsEmpty())
		{
			const FKey Key(*Saved);
			if (Key.IsValid())
			{
				return Key;
			}
		}

		for (const FIABindingInfo& Info : GetBindings())
		{
			if (Id == Info.Id)
			{
				return Info.DefaultKey;
			}
		}
		return EKeys::Invalid;
	}

	void SetKey(FName Id, FKey Key)
	{
		if (!Key.IsValid())
		{
			return;
		}
		GConfig->SetString(KeySection, *Id.ToString(), *Key.GetFName().ToString(), GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	void ResetAll()
	{
		GConfig->EmptySection(KeySection, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	FName FindActionUsingKey(FKey Key, FName ExceptId)
	{
		for (const FIABindingInfo& Info : GetBindings())
		{
			if (Info.Id != ExceptId && GetKey(Info.Id) == Key)
			{
				return Info.Id;
			}
		}
		return NAME_None;
	}
}
