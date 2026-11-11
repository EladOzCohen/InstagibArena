// Instagib Arena

using UnrealBuildTool;

public class InstagibArena : ModuleRules
{
	public InstagibArena(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

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
	}
}
