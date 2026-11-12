# Development guide

How to build, run and test Instagib Arena from the command line, and the lessons learned so far.
Read this before changing anything. Paths below assume Unreal Engine 5.8 at `C:\Program Files\Epic Games\UE_5.8`
and `<proj>` is the folder that holds `InstagibArena.uproject` (your checkout or worktree).

## 1. First setup of a fresh checkout or worktree

```powershell
cd <proj>
powershell -ExecutionPolicy Bypass -File Tools\restore_mannequins.ps1     # Epic's characters are not in git
```
Binaries, Intermediate, Saved and DerivedDataCache are not in git. The first build compiles everything (a few minutes).
If a build fails because a path is too long, map your folder to a short drive letter (`subst X: <proj>`) and build from `X:\`.

## 2. Heavy jobs take turns

Building and running the game uses several GB of RAM and every core. Several people or agents may work in parallel,
so **wrap every heavy command (build, game, editor commandlet, packaging) in the lock**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <proj>\Tools\exclusive.ps1 -Command "<the command line>"
```
It waits for its turn and passes the exit code through. Git, reading and editing files need no lock.
Keep each locked job short: do not leave a game window running longer than needed, and stop it when done.

## 3. Build

```powershell
$bat = "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat"
& $bat InstagibArenaEditor Win64 Development "-Project=<proj>\InstagibArena.uproject" -WaitMutex -NoHotReload 2>&1 |
    Select-String -Pattern "error|warning C4|Result:"
```
A build must succeed with no errors before you report anything. Close any running editor first (a running editor locks the DLL).
Packaging (rarely needed while developing): `Tools\package_and_installer.ps1`.

## 4. Run the game

```powershell
$exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
& $exe "<proj>\InstagibArena.uproject" "/Game/Maps/DM-Foundry?Mode=TDM?Bots=6?BotSkill=1?ScoreLimit=0?TimeLimit=0?Char=3" `
    -game -windowed -ResX=1280 -ResY=720 -nosound -nosplash
```
- Options after the map name travel in the URL: `Mode=FFA|TDM`, `ScoreLimit`, `TimeLimit`, `Bots` (2-10, 0 = none), `BotSkill` (0-2), `Char` (0-14), `Name`, `listen`.
- Without a map, the game starts on the main menu (`/Game/Maps/MainMenu`).
- Use `UnrealEditor-Cmd.exe` plus `-nullrhi -nosound -unattended` for headless runs (no graphics, no window). Add `"-abslog=<file>"` to get a log file, and `-LogCmds="LogInstagib Verbose"` for verbose game logs.
- A window you start from a script does not close itself. Use `-IAShotDelay` (below) or `Start-Process ... -PassThru` and stop it after a timeout.

## 5. Look at the game without a person watching (screenshots)

Development builds have command-line helpers (`Source/InstagibArena/IADevSubsystem.*`):

| Option | What it does |
|---|---|
| `-IAShotDelay=20 -IAShotName=name` | After 20 s take `Saved/IAShots/name.png` (UI included) and quit |
| `-IAShotCam=X,Y,Z,Pitch,Yaw` | Look through a camera placed there instead of the player's view |
| `-IAFire` | The local player fires 0.12 s before the shot |
| `-IAShowroom=X,Y,Z,Yaw -IAShowroomFrom=5` | Line up five characters (look 5-9) there |
| `-IAImpact=X,Y,Z` | Play three impact bursts, a hit marker and two messages |
| `-IAPause` | Open the pause menu before the shot |
| `-IAMenuPage=N -IAMenuTab=T` | Open main menu screen N (0 main, 1 custom, 2 multiplayer, 3 character, 4 settings, 5 credits) |
| `-IAPreviewCycle` | The menu preview steps through all characters |
| `-IAReport` | Log one line every 4 s about what this machine sees (players, scores, pawns) |
| `-IAWalk`, `-IAFireEvery=2` | Walk and turn the local player, fire every 2 s |
| `-IASetMusic=0.3` | Set and save the music volume |

Add more helpers there when you need them (development only: wrap in `#if !UE_BUILD_SHIPPING`).
Look at screenshots with the Read tool. Reading a screenshot is how you check layout, colours and effects, so do it.
At 1280x720 the UI scale is about 0.69, so a 640-unit panel is about 440 pixels wide.

## 6. Test multiplayer on one PC

Start a listen server and a client, both headless, with `-IAReport -IAWalk`:
```
server: UnrealEditor-Cmd.exe <uproject> "/Game/Maps/DM-Foundry?listen?Mode=TDM?Bots=4" -game -nullrhi -nosound -unattended -IAReport -IAWalk "-abslog=server.log"
client: UnrealEditor-Cmd.exe <uproject> "127.0.0.1?Char=2" -game -nullrhi -nosound -unattended -IAReport -IAWalk -IAFireEvery=2 "-abslog=client.log"
```
Compare the `REPORT` and `HUMANS` lines of both logs: players, scores, clock and pawn positions must match.
`LogNet` warnings or errors in either log are bugs.

## 7. Bots on every map

Run a headless match with 8 bots for 60-70 s per map and count `was fragged by` lines in the log (about 1 per second is normal).
`NavGrid: N nodes, M links, K connected areas` in the log shows that bots can navigate the map.

## 8. Maps

Maps are built by Python scripts run in the editor commandlet, using `Tools/mapkit.py`:
```
UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<proj>\Tools\make_map_temple.py -unattended -nullrhi -nosplash -nopause "-abslog=map.log"
```
- Always create maps through `mapkit.MapBuilder` or `mapkit.begin_level`. `new_level` refuses to overwrite an existing map and then the script silently edits whatever map is open. This once destroyed the main menu.
- After a script, look for `MAKEMAP_DONE` in the log.
- Walkable surfaces are found automatically (`IANavGrid`) from `StaticMeshActor`s with collision; decoration that must not be walkable: `solid=False`.
- Lighting: use `MapBuilder.sky(...)` (sun + warm sky light + a fill light). Indoor maps: point lights, no sky light (a closed room with a real-time sky light shows an on-screen error).
- A map appears in the menu when it has a line in `Source/InstagibArena/IAMapList.h`.

## 9. Code conventions

- Classes: `AIA...`, `UIA...`, `FIA...`; Slate widgets `SIA...`; namespaces `IAMenu`, `IASettings`, `IAInput`, `IAMaps`, `IACharacters`. Log category `LogInstagib`.
- No absolute paths in code or scripts. Use `FPaths`, `unreal.SystemLibrary.get_project_directory()`, `$PSScriptRoot`.
- Windows-only APIs are not allowed in game code (the game must still compile on Mac). Editor-only code goes in `#if WITH_EDITOR`.
- Everything the game loads by path (`LoadObject`) must be under a folder listed in `Config/DefaultGame.ini` (`DirectoriesToAlwaysCook`) or the packaged game will not find it.
- Do not download assets. Everything is generated by scripts or comes from Unreal Engine's own content. No third-party libraries.
- Network: gameplay state lives on the server (`HasAuthority()`), clients only show it. Cosmetic effects run locally on every machine (not replicated). The player's movement is client-predicted through `UIACharacterMovement` saved moves.
- Settings and bindings: `IASettings.h` (settings, crosshair, last match) and `IAInputConfig.h` (rebindable keys, one table). Both save to `GameUserSettings.ini`.
- New text for the player is English. Keep texts short.

## 10. Gotchas

- The editor adds an `[/Script/AndroidFileServerEditor...]` block with a security token to `Config/DefaultEngine.ini` every time it starts. Delete that block before committing.
- `LogAutomationTest: Error: Condition failed` at the start of every log is engine noise.
- `SBox.HAlign` aligns the child inside the box, not the box. To align a whole panel, use `ChildSlot.HAlign(...)`.
- Slate `SBorder` and `SBox` size from their content unless you use `WidthOverride`. Check every screen at 1280x720.
- `FParse::Value` stops at a comma unless you pass `bShouldStopOnSeparator = false`.
- Widgets that need their own button for hover or focus: see `IAMenu::Chip` and `IAMenu::NavButton` in `IAMenuStyle.cpp`.
- Skinned meshes need the material flag `used_with_skeletal_mesh` (`M_IABody` has it). The Mannequin skeleton is `SK_Mannequin`; attach pieces to bones with `IACharacterRoster.h` (offsets are in character space).
- Sounds are generated by `Tools/gen_audio.py` and imported by `Tools/import_audio.py`; adding a sound means: generate, import, add to `EIASound` and the path switch in `IAAudioSubsystem.cpp`.

## 11. Git

Commit your work in small steps with clear messages. End every commit message with
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push. Do not commit the Mannequins, Builds, Saved, Binaries or Intermediate folders (they are ignored).

## 12. Menu helpers (MENUS)

Menus are Slate (`SIAMainMenu`, `SIAPauseMenu`, `SIASettingsPanel`, `SIAControlsPanel`, `SIAWelcome`, `IALoadingScreen`). Shared pieces are in `IAMenuStyle.h`.
Slate's own arrow-key navigation does not work with our buttons (a focused `SButton` answers it first), so `SIAMainMenu` and `SIAPauseMenu` do arrow/Tab navigation themselves in `OnPreviewKeyDown` (`IAMenu::HandleNavKey`).
Development-only command line flags (they need a window with rendering: the menu is not built with `-nullrhi`):

| Option | What it does |
|---|---|
| `-IAMenuScript="a;b;c"` | Runs menu commands 1.5 s after start, 0.7 s apart: `page=N`, `mp=0/1`, `settings=N`, `key=Down` (a real Slate key event), `welcome=0/1/off`, `quit`, `quickplay`, `host`, `join=ADDRESS`, `map=N`, `uiscale=1.2`, `modal-cancel`, `wait=3`; on the settings screen also `tab=N`, `mode=0/1/2`, `res=WxH`, `apply`, `keep`, `revert`, `rebind=Id:Key`, `listen=Id`, `reset-keys` |
| `-IAPauseScript=...`, `-IAPauseTab=N`, `-IAPauseAt=20` | The same for the pause menu; `-IAPauseAt` opens it after 20 s (no screenshot needed) |
| `-IAFirstRun`, `-IASkipWelcome` | Force or skip the welcome overlay (it shows on the first launch; fresh worktrees need `-IASkipWelcome` for screenshots) |
| `-IALoadingPreview -IALoadingMap=/Game/Maps/DM-Foundry` | Covers the screen with the loading screen widget |
| `-IAShotAuto` | With `-IAShotDelay` and `-IAShotName`: overview camera for map thumbnails (`Tools/make_thumbnails.ps1` uses it) |

Map thumbnails: `powershell -File Tools\make_thumbnails.ps1` reads `IAMapList.h`, makes one picture per map, imports them as `/Game/UI/MapThumbs/T_<MapName>` and rewrites `IAMapRecommended.inl` (rebuild afterwards).
Settings tests write into the worktree's `Saved/Config`; undo with `-IAMenuScript=uiscale=1.0` or the RESET buttons.

## 13. Light and shading look (LOOK)

Findings (measured with screenshots, see the header of `Tools/maplooks.py`): the project has **no Lumen and no GI**
(`r.DynamicGlobalIlluminationMethod=0`, `r.ReflectionMethod=2` = screen space only, mesh distance fields off), auto exposure pumped and
re-normalised every map, default fog density 0.02, bloom 0.675, vignette 0.4, a fill light of another colour, emissive "light strips"
with Glow 6, and characters made of one glossy material (roughness 0.3-0.5, accessories Glow 6).

- **Pick a look per map** with one line in the map script (`m` = `mapkit.MapBuilder`): `m.look("day_clear")`, optionally with overrides
  (`m.look("dusk", sun_yaw=250, ev=1.0)`). Presets: `maplooks.available()` = day_clear, overcast, dusk, night_city, volcanic, arctic, desert, indoor.
  The old `m.sky(...)` now just places `day_clear` (only the sun direction is used); `m.post(...)` adjusts the look's volume (exposure bias limited to +-1.5 EV, bloom to 0.35).
- Exposure is **fixed** per look (EV100, min = max, no eye adaptation). `Config/DefaultEngine.ini` sets `r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True` so the values are EV.
  Brighter picture = lower EV. Sun intensity is in the engine's lux-like units (day = 10). The sky light is the only ambient light (no GI): raise `sky_intensity` for lighter shadows.
- Coloured accent lights: `m.accent_light(label, loc, rgb, candela=30, radius=450)` (no shadows, reduced specular). Prefer a few of these over big emissive walls; `Glow` of light strips is 2.5 by default (mapkit caps it at 5).
- Look test rooms: `Tools/make_looks.py` builds `/Game/Dev/Looks/LookTest_<look>` (grey cards, spheres from matte to glossy, a showroom spot). Never commit `Content/Dev`.
- People use `/Game/Characters/M_IACharacter` (matte cloth detail, plate/fabric split from the mannequin's own albedo map, `Rim` edge light in the team colour). Beams, sparks and jump pads keep `M_IABody` (pure emissive).
  Run `Tools/make_character_assets.py` after cloning (it downloads the CC0 cloth texture into `~/AssetCache` and imports it). `-IASlotDebug` colours the two body slots red and blue.
