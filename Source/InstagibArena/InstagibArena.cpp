// Instagib Arena

#include "InstagibArena.h"
#include "IALoadingScreen.h"
#include "IASettings.h"
#include "Misc/CoreDelegates.h"
#include "Modules/ModuleManager.h"

/** The game module: besides loading, it hooks up the loading screen and applies the saved settings once the engine is up. */
class FInstagibArenaModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override
	{
		FDefaultGameModuleImpl::StartupModule();
		// The editor and commandlets (map scripts, builds) must not get the player's video and sound tweaks.
		if (!GIsEditor && !IsRunningCommandlet())
		{
			IALoadingScreen::Register();
			FCoreDelegates::GetOnPostEngineInit().AddStatic(&IASettings::ApplyStartupSettings);
		}
	}
};

IMPLEMENT_PRIMARY_GAME_MODULE(FInstagibArenaModule, InstagibArena, "InstagibArena");

DEFINE_LOG_CATEGORY(LogInstagib);
