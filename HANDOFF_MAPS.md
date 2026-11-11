# HANDOFF - MAPS engineer (branch worktree-agent-a99df6f5d14760718), state at third stop

Use docs/DEVELOPMENT.md and Tools/exclusive.ps1. No system Python. Bash here refuses heredocs and compound git; use Write/Edit.
My helper scripts are in the session scratchpad `...\scratchpad\maps\` (NOT in git): runpy.ps1 (editor-cmd python), genmaps.ps1 (regenerate maps), bots.ps1 (headless 8-bot match + log grep), shot.ps1 (screenshots), dump.ps1 (-IANavDump), mp.ps1 (host+client pad test, written, never run), build.ps1. Recreate if lost.

## Key lessons (all fixed in scripts/mapkit)
- `solid=False` decoration had collision (fixed: NoCollision profile in mapkit._place). Existing old maps are untouched.
- The NavGrid cannot place nodes on STAIRS with run < ~60 cm or on slopes steeper than ~20 degrees. All ramps in my maps are slopes <= 18 degrees; no stairs. Ramps must run head-on into the upper platform edge.
- unreal.Color is (b,g,r,a): mapkit uses `_color()` now.
- Nav check: log line "NavGrid: largest area N of M nodes; K of S player starts outside it" (reference area = the one holding most starts), plus `-IANavDump=X,Y,Z,R` to list nodes near a point.

## Status per map (8 bots, 65-70 s headless; last successful runs)
- Forge: 80 frags, 0 of 10 starts outside start area. Screenshots looked at (lighting later made dimmer in script; not re-shot).
- Canyon (mesa z=450, ramps 17 deg): 72 frags, 0 of 12 outside. Screens taken before sun/exposure change; not re-shot.
- Glacier (deck z=440 via ramp, huts via ramps): 77 frags, 0 of 12 outside. Screens looked at.
- Neon: last good run 115 frags, 0 of 8 starts outside, but only 8 starts (need >= 10 with no mutual line of sight). I was adding partitions (see make_map_neon.py partition list; the last variant (400,600..800) and (-400,-800..-600) was being tested when stopped). Content/Maps/DM-Neon.umap may be from an interrupted run: REGENERATE it first (genmaps.ps1 neon). If 10 starts do not fit, reduce min_sep or accept 9 and say so in the report.
- IAMapList.h has the 4 entries; DefaultGame.ini MapsToCook has the 4 maps. Menu not yet checked (-IAMenuPage=1 screenshot).

## Still to do, in order
1. Regenerate Neon, check START_CHECK (>=10 starts, pairs_in_sight=0) and nav line, bot test 70 s.
2. Rebuild C++ (IAJumpPad -IAPadTest code and IANavGrid diagnostics were built OK earlier) and run mp.ps1 (server+client, -IAPadTest) on DM-Neon; compare PADWATCH positions of both logs, check LogNet warnings. Jump pad multiplayer behaviour is UNVERIFIED so far.
3. Check bots around pads (not looping): 70 s bot runs showed normal frags on all maps, but no specific log check was made.
4. Re-shoot overview + 2 first-person per map (shots_new.ps1 pattern; camera lines: Neon 0,-1500,2700,-52,90 / -1600,0,170,-3,0 / 900,-300,170,0,150 ; Forge 0,-2400,1250,-38,90 / -2000,-2000,170,-8,45 / -2300,1800,620,-8,-30 ; Glacier 0,-3700,2800,-40,90 / -1200,-1500,170,0,20 / 500,0,500,-5,180 ; Canyon 0,-3300,3500,-50,90 / -1500,1200,170,0,0 / 3300,0,620,-3,180). Fix anything dark/blown out. Canyon first look was grey/flat (sun now steeper and sky warm in script).
5. Menu check with -IAMenuPage=1 (4 new maps appear), full build, commit, final report. Delete the AndroidFileServerEditor block in Config/DefaultEngine.ini before committing (git checkout that file).

## Ideas not done
- Polishing the 4 old maps; more props; Canyon looks blocky.
