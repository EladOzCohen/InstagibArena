// Instagib Arena

using UnrealBuildTool;
using System.Collections.Generic;

public class InstagibArenaEditorTarget : TargetRules
{
	public InstagibArenaEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V7;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
		ExtraModuleNames.Add("InstagibArena");
	}
}
