# Polish spec (written for an executing agent: follow it literally, do not redesign)

Project: Instagib Arena (Unreal Engine 5.8, Windows). Repository root = the folder that contains `InstagibArena.uproject`.
All commands below are run from the repository root in PowerShell, one at a time, in the foreground.
Never push to GitHub, never create releases, never touch files that are not named in your task.
If a command fails twice with the same error, STOP and write what happened into `docs/POLISH_REPORT.md`.

## Tools that already exist
- `Tools\run_ue.ps1 -Script Tools\make_map_<name>.py -Log Saved\mk_<name>.log -Grep "MAKEMAP_DONE|Traceback|LogPython: Error"`
  rebuilds one map from its script (about 1 minute). The output must contain a `MAKEMAP_DONE` line. `<name>` = foundry, temple,
  dock, skyline, neon, forge, glacier, canyon.
- `Tools\polish_shots.ps1 -Tag <tag> -Maps <Map> -ViewNames auto` takes a screenshot (about 2 minutes) and writes
  `Saved\IAShots\polish\<tag>_<Map>_auto.png`. `<Map>` = Foundry, Temple, Dock, Skyline, Neon, Forge, Glacier, Canyon.
- `Tools\polish_stats.ps1 -Files <png>` prints `mean`, `burnt`, `crushed` and `sat` of a screenshot.
- Every command runs under a shared lock; if it prints `[exclusive] waiting for my turn` just wait.

## Task TUNE: bring the brightness of every map back to the approved look

Background: the maps were approved by the user with the brightness listed below. A new photographic sky made all maps about
twice as bright and washed out. We fix it by two numbers per map, in the `m.look(...)` / `b.look(...)` line of the map script
(file `Tools\make_map_<name>.py`, find it with: `Select-String -Path Tools\make_map_*.py -Pattern "\.look\("`):

- `ambient_gain=<number>`: multiplies the light that comes from the sky. 1.0 = as now. Smaller = darker shadows and darker
  surfaces that are not in the sun. Allowed range 0.10 to 1.00.
- `ev=<number>`: exposure. Bigger = darker whole picture. If the line already contains `ev=...` change that number, otherwise add
  `ev=0.0` as a new keyword argument (look at the current preset value in `Tools\maplooks.py` under LOOKS to know the starting
  value; if you add `ev`, start from the preset's value).
- Some lines already pass `**_look` (Foundry, Dock): there, change the dictionary `_look` defined a few lines above; add the key
  `"ambient_gain": <number>` and/or change `"ev"`.
Do not change any other argument. Do not change anything except these two numbers.

Targets (measured on the same camera, view `auto`, with `Tools\polish_stats.ps1`):

| Map | target mean | start ambient_gain |
|---|---|---|
| Foundry | 110 | 0.5 |
| Temple | 87 | 0.35 |
| Dock | 73 | 0.35 |
| Skyline | 86 | 0.3 |
| Neon | 55 | 0.3 |
| Forge | 40 | 0.2 |
| Glacier | 136 | 0.5 |
| Canyon | 97 | 0.35 |

A map is DONE when: `mean` is within plus or minus 12 percent of the target, `burnt` is below 5, `crushed` is below 20, and
`sat` is not lower than 0.12.

Loop for each map, in the order of the table (at most 8 rounds per map):
1. Edit the number(s) in the map script (round 1: set `ambient_gain` to the "start" value of the table).
2. Rebuild the map: `Tools\run_ue.ps1 ...` (see above). Check for `MAKEMAP_DONE`.
3. Screenshot: `Tools\polish_shots.ps1 -Tag tune -Maps <Map> -ViewNames auto`
4. Measure: `Tools\polish_stats.ps1 -Files Saved\IAShots\polish\tune_<Map>_auto.png`
5. Decide:
   - mean too high (above target + 12 percent): first multiply `ambient_gain` by 0.75 (but not below 0.10). If `ambient_gain` is
     already 0.15 or lower, raise `ev` by 0.4 instead.
   - mean too low (below target - 12 percent): first lower `ev` by 0.4 if you raised it before, otherwise multiply
     `ambient_gain` by 1.3 (but not above 1.0).
   - `burnt` 5 or more: raise `ev` by 0.3.
   - `crushed` 20 or more: lower `ev` by 0.3 and multiply `ambient_gain` by 1.2.
   - `sat` below 0.12 only: do nothing (report it).
6. Repeat from step 1 until DONE or 8 rounds are used. Keep the best numbers (closest to the target) in the script.

When all maps are done, write the table (map, final ambient_gain, final ev, mean, burnt, crushed, sat, rounds used) to
`docs/POLISH_REPORT.md`, and make one git commit on the current branch containing ONLY the changed `Tools\make_map_*.py` files, the
regenerated `Content\Maps\DM-*.umap` files and `docs\POLISH_REPORT.md`:
`git add Tools\make_map_*.py Content\Maps\DM-*.umap docs\POLISH_REPORT.md` then `git commit -m "Tune map exposure after the new sky"`.
Before committing run `git checkout Config\DefaultEngine.ini` (the editor adds junk to it) and do not add any other file.
Then reply with the table and nothing else.
