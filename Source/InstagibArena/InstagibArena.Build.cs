// Instagib Arena

using UnrealBuildTool;

public class InstagibArena : ModuleRules
{
	public InstagibArena(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
			bUseUnity = false;   // each .cpp keeps its own names (a file-level "using namespace" would collide in a unity file)

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"NavigationSystem",
			"UMG",
			"Slate",
			"SlateCore",
			"Sockets",
			"ApplicationCore",
			"MoviePlayer"
		});

		// Frame timings in the development flags (-IAReport) and the hardware name for the first-start quality choice.
		PrivateDependencyModuleNames.AddRange(new string[] { "RHI", "RenderCore" });
	}
}
