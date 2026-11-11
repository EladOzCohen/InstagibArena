# HANDOFF - MAPS engineer (branch worktree-agent-a99df6f5d14760718) - state at second stop

Use docs/DEVELOPMENT.md and Tools/exclusive.ps1 from this worktree (merged from main). No system Python (UE's python is in Engine\Binaries\ThirdParty\Python3\Win64).
Shell guard: no heredocs / compound git in Bash here; use Write/Edit tools. The session scratchpad is SHARED with other agents: my helper scripts live in `<scratchpad>\maps\` (runpy.ps1, genmaps.ps1, shot.ps1, shots_new.ps1, bots.ps1, build.ps1, dbg.py); they are not in git. Re-create if lost: runpy = UnrealEditor-Cmd -ExecutePythonScript, shot = UnrealEditor -game ... -IAShotDelay -IAShotName -IAShotCam, bots = UnrealEditor-Cmd map?Mode=FFA?Bots=8 for 70 s then count "was fragged by" and grep NavGrid.

## Done and verified (ran it)
- AIAJumpPad (IAJumpPad.h/.cpp), EIASound::JumpPad, S_JumpPad imported (Content/Audio/SFX/S_JumpPad.uasset), gen_audio jump_pad(). Builds. Pad cone/glow visible in screenshots of Glacier/Canyon/Forge. Pad trigger is query-only, WorldDynamic, overlaps Pawn only.
- Dev test built-in: `-IAPadTest` (IAJumpPad.cpp, non-shipping): server drops every human onto the first pad every 7 s; every machine logs PADLAUNCH / PADWATCH lines (pos, vel). NOT YET RUN (host+client test still to do).
- IANavGrid.cpp: added diagnostics (largest area, biggest 6 areas with centre, warning per PlayerStart outside the largest area).
- mapkit.py: launch_velocity(), glow(), fog(), post() (unbound post process: exposure/bloom), jump_pad(), light_strip(), frame(), cone(), _trace(), auto_starts() (picks starts with standing room and no mutual line of sight, spread over levels), check_starts(). IMPORTANT FIX: unreal.Color takes (b,g,r,a); mapkit now uses `_color()` with keywords (sun/sky/point light colours were red/blue swapped before; existing maps keep their baked look, only regenerated maps change).
- Maps generated (scripts Tools/make_map_{neon,forge,glacier,canyon}.py -> Content/Maps/DM-*.umap) and screenshotted/looked at (Saved/IAShots/*_over/_fp1/_fp2.png): Neon (night, small), Forge (lava, medium, kill_z -150, 4 pads island->balconies), Glacier (arctic, medium, 2 pads to relay deck), Canyon (big, kill_z -700, 4 pads to spire tops). All have >=10 PlayerStarts with no mutual line of sight (Forge 10, Neon 10, Glacier 12, Canyon 12).
- 8-bot headless frags in 70 s: Neon 76, Forge 90, Glacier 85, Canyon 49 (big map; ok but lowest).
- Config/DefaultGame.ini: MapsToCook block for the 4 maps added (marked MAPS).

## ROOT CAUSE FOUND, NOT YET FIXED (do this first)
NavGrid shows many connected areas (Neon 62, Forge 64, Glacier 51, Canyon 103; most starts outside the largest area; Neon largest area only 156 of 984 nodes) and nodes at z=3000+ : the `solid=False` decoration (backdrop, signs, windows, strips...) STILL HAS COLLISION. Verified by dbg.py: Skyline_* actors report CollisionEnabled.QUERY_AND_PHYSICS although mapkit._place calls comp.set_collision_enabled(NO_COLLISION). So decoration blocks bots and creates walkable fake surfaces (and probably blocks player movement/shots too). Fix in Tools/mapkit.py `_place` when not solid: also `comp.set_collision_profile_name("NoCollision")` (and/or set_generate_overlap_events(False)); verify again with dbg.py (expect NO_COLLISION), regenerate all 4 maps (genmaps.ps1 neon,forge,glacier,canyon), re-run bots and check "NavGrid: largest area N of M nodes; 0 of K player starts outside it". The same bug probably affects the old maps (Foundry has 20 areas but 0 starts outside, so it is fine there; do not regenerate old maps).
Then expect fewer areas; fix any remaining start outside the largest area (rare small islands are fine; every start must be inside).

## Remaining steps in order
1. Fix NoCollision (above), regenerate maps, re-run 70 s bot tests (record frags and NavGrid lines), rerun Neon/Forge/Glacier/Canyon shots with the tweaks already in the scripts (Forge dimmer lights/lava; Glacier exposure 0; Canyon sun pitch -36, warm sky_rgb; Canyon overview camera should be higher/closer e.g. 0,-3300,3500,-50,90). Canyon fp shots looked grey/flat before the sun change.
2. Host+client pad test: server `UnrealEditor-Cmd proj "/Game/Maps/DM-Neon?listen?Mode=FFA?Bots=2" -game -nullrhi -nosound -unattended -IAReport -IAWalk -IAPadTest -abslog=server.log`, client `127.0.0.1?Char=2 ... -IAPadTest`; compare PADWATCH lines (pos/vel) of server and client, and check no LogNet warnings. Also check bots do not loop on pads (grep bot positions / stuck logs; roof pads on Neon land on arcade roof which has stairs).
3. Append the 4 maps to Source/InstagibArena/IAMapList.h (file uses CRLF/tabs; Edit failed to match once, view with Read and match exactly). Suggested lines: Neon Street /Game/Maps/DM-Neon, Forge /Game/Maps/DM-Forge, Glacier /Game/Maps/DM-Glacier, Canyon /Game/Maps/DM-Canyon, one-sentence descriptions. Verify with -IAMenuPage=1 screenshot.
4. Build, commit per map, delete the AndroidFileServerEditor block from Config/DefaultEngine.ini if the editor added it (check git diff), final report.

## Known issues / ideas
- Pads are not nav links; all pad targets also have walking routes (Neon arcade roof via stairs, Forge balconies via gantry ramps, Glacier deck via stairs, Canyon spire tops via plank bridges).
- Canyon is blocky; ideas: more strata detail, rope-bridge sag. Polishing the 4 old maps not started.
