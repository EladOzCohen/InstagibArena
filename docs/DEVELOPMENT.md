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
- Options after the map name travel in the URL: `Mode=FFA|TDM`, `ScoreLimit`, `TimeLimit`, `Bots` (2-10, 0 = none), `BotSkill` (0-2), `Char` (0-43), `Name`, `listen`.
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
- Free CC0 assets may be downloaded (Poly Haven, ambientCG), but only through a script that caches them outside the repository (`Tools/fetch_textures.py`, cache `~/AssetCache/textures`) and every asset must be credited in `NOTICE.md`. Everything else is generated by scripts or comes from Unreal Engine's own content. No third-party code libraries.
- World surfaces: use the material library, not flat colours: `from matlib import surface` then `mat = surface("BrickRed")` (see section 13).
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

## 13. World materials (MATLIB)

Realistic PBR surfaces for map building: `Tools/matlib.py` (library), `Tools/fetch_textures.py` (downloads the CC0 texture sets from Poly Haven and ambientCG into `~/AssetCache/textures`, outside the repository), `Tools/build_matlib.py` (builds everything), `Tools/matlib_demo.py` (test level to look at every surface).
- `M_IAWorld` is world-aligned (triplanar): scaled cubes, cylinders, cones and spheres do not stretch, pieces line up, no UVs needed, no emissive. Parameters: `DiffuseTex NormalTex RoughnessTex TilingMeters Tint Desaturate RoughnessScale RoughnessBias NormalStrength Metallic MacroStrength MacroMeters DirtAmount DirtHeight DirtGroundZ`.
- In a map script (after `import mapkit`): `from matlib import surface, glass, water, lava`, then `mat = surface("BrickRed")` and pass it as `mat=` to `b.box(...)`. `surface()` imports what it needs and creates `/Game/Materials/MI_W_<Name>` on first use. The table of surfaces is `matlib.SURFACES` (about 70 names).
- Variants: `surface("ConcreteDirty", tiling=3.0)`, `surface("ConcreteClean", albedo=(120, 40, 40))` (aim at an sRGB colour), `tint=(r, g, b)` (linear multiplier), `rb=-0.3` (wetter), `rs`, `ns`, `metal`, `desat`, `macro`, `dirt`, `dirt_h`. A variant is its own instance asset named `MI_W_<Name>_<tag or hash>` (`tag="Neon"` gives a readable name). Prefer the standard surfaces when they fit; add new standard surfaces to `SURFACES` for colours several maps share.
- Do not use an emissive texture on world pieces: neon and lights keep using `MapBuilder.glow`. Lava is `matlib.lava()`, water `matlib.water()`, clear glass `matlib.glass()`.
- Prefer big pieces over many tiny ones: the cost per pixel is the same, but a 10 m wall as one box tiles seamlessly.
- A new texture set: add one line to `TEXTURES` in `fetch_textures.py` (source, slug), run `fetch_textures.py` (it also rewrites the credits in `NOTICE.md`), then add a `SURFACES` entry. After changing the HLSL in `matlib.py` run `build_matlib.py` with `IA_MATLIB_FORCE=1`.
## 14. Light and shading look (LOOK)

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
## 15. 3D props (PROPS)

Realistic props and nature (rocks, trees, barrels, crates, lamps, statues ...) are CC0 models from Poly Haven, imported to `/Game/Props`.
- `python Tools/fetch_models.py --all` downloads the glTF models (1k textures) into `%USERPROFILE%\AssetCache\models` (outside the repository, shared between checkouts; use UE's embedded Python, there is no system Python). `Tools/props_spec.py` lists what is used and how it is imported.
- `Tools/run_ue.ps1 -Script Tools\import_props.py` imports them (Interchange), builds simple collision, Nanite/LODs and our own materials (`M_Prop`: roughness never below 0.5 unless metal, no emissive), and writes `Tools/props_measured.json`. Commit the imported `Content/Props` folder together with that file.
- Map scripts: `import props` after `import mapkit`, then `b.prop(label, name, x, y, z, yaw=..., scale=...)` (z = ground height) and `b.scatter(names, region, count, seed=...)`. The catalogue and the exact API are documented at the top of `Tools/props.py`.
- `Tools/props_demo.py` builds the throwaway level `/Game/Maps/_PropDemo` with every prop in labelled rows; `Tools/props_demo_shots.ps1` takes the screenshots. Delete the level afterwards (`-Delete`).
- Props referenced by a map are cooked with it; nothing in `/Game/Props` is loaded by path in code, so no `DirectoriesToAlwaysCook` entry is needed. Every model's author and licence is in `NOTICE.md`.
## 16. Generated meshes for maps (MAP-B tools)
Temple and Canyon build real irregular geometry (fluted columns, ruined walls, layered cliffs, dunes, rope bridges) as static meshes from python:
`Tools/mesh_b.py` (pure python mesh builder: boxes with chipped corners, lathes, lumpy rocks, noise), `Tools/mesh_arch_b.py` (walls, arches, stairs, cliff strips with rock strata, heightfields),
`Tools/mesh_misc_b.py` (roofs, buttes, ropes, cloth, plank decks), `Tools/mapkit_b.py` (`commit(name, mesh)` builds `/Game/Maps/Gen/SM_<name>` through Geometry Script, `put(...)` places it; collision = the mesh itself).
- Pure python parts run with UE's embedded python without the editor (`Engine\Binaries\ThirdParty\Python3\Win64\python.exe`), handy for syntax checks.
- An old gameplay box can stay as invisible collision (`actor.set_actor_hidden_in_game(True)`) while a generated mesh stands in front of it (Canyon cliffs): the layout cannot change by accident.
- Helpers: `Tools/ue.ps1` (run a python script in the editor commandlet inside the lock), `Tools/shots_b.ps1` (several screenshots of a map), `Tools/bottest_b.ps1` (70 s match with 8 bots, counts frags and problems).
- `Tools/mapkit_a.py` (additive helpers used by DM-Foundry and DM-Dock): `strut` (box between two 3D points), `pipe`, `rail` (handrail with posts, no collision), `ramp` (slab with stringers, rails, legs), `Wall` (local frame on a wall: u along it, v into the room) with `window`, `container` (shipping container with posts, rails, door bars), `pallet`, `disc`, `cyl`. Thin non-solid pieces are made non-shadow-casting automatically. Never run two scripts that write the same file name into a shared scratch folder; surface() re-saves the standard MI_W_* assets every run, so `git checkout Content/Materials/MI_W_<Standard>.uasset` before committing.
## 17. City kit (MAP-C)

`Tools/mapkit_c.py` and `Tools/kc_parts.py` (additive, used by `make_map_skyline.py` and `make_map_neon.py`):
- `kc.facade(tag, wall="BrickRed", grid_z=..., lit=0.2, glow=0.3, ...)` makes an instance of `M_IAFacade`: a wall texture (matlib set) with a **window grid drawn in the shader** (frames, glass with a sky gradient, sills, lintels, curtains, dirt streaks, a fraction `lit` of windows emissive). Big backdrop buildings cost one actor. Windows align to cells of `cell=(300, 330)` cm; `grid_z` is the height of a cell base (put string courses there). Window centres are at 150 + 300 k along any wall.
- `kc.emit(name, rgb, intensity)` is an emissive instance of `M_IAEmit` (window pane, neon tube, bulb). The scale is not `M_IABody`'s Glow: a lit shop window is about 0.15-0.3, a thin neon tube 1.4-1.8 at the `night_city` exposure.
- `kc.neon_text(b, label, "BAR", x, y, z, 0, height, mat, yaw=...)` builds letters from thin tubes (A-Z, 0-9). `yaw` is the reading direction: a wall seen from the street looking +y reads along -x (yaw 180), looking -y yaw 0, looking +x yaw 90, looking -x yaw -90. Light the sign with a small `b.accent_light` in front of it.
- `kc.rbox` (box with roll), `kc.cyl` (cylinder between two points), `kc.bar` (thin bar between two points), `kp.car`, `kp.chiller`, `kp.water_tank`, `kp.curb` (roof edge curb with gaps for bridges), `kp.bridge_gaps`.
- `kp.car(b, label, x, y, z, yaw, paint, glass, dark, kind)` places a generated car (`sedan`, `hatch`, `van`; `Tools/mesh_car.py` builds the meshes, pure python): a lofted body with wheel arches, a raked greenhouse, glass, tyres, hubs, lamps and door seams as six static meshes (`/Game/Maps/Gen/SM_Car_<kind>_<part>`, one per material, shared by every car of a kind). `solid=True` adds two hidden box colliders. Materials: `kp.car_paint(tag, (r, g, b))`, `kp.car_glass_mat()`, `kp.car_rubber_mat()`.
- `kc.facade(...)` extras: `desat` (per pixel desaturation of the wall scan, tames orange brick), `frame_rgb` (painted window frames, linear colour: `matlib.srgb(...)`), `sill_boost` (brightness of the stone sills), `lit_rows` (fraction of whole floors that are lit, office style) and a `Reveal` shadow inside the frame. After changing the HLSL in `mapkit_c.py` run one map script with `IA_FACADE_FORCE=1` so that `M_IAFacade` is rebuilt.
- Lessons: accent lights are in candela with inverse-square falloff, so a 100 cd lamp 1 m from a wall is far brighter than the 1.5 lux moon; shop pools 8-15 cd, street lamps about 140 cd, neon signs 20-30 cd. Everything that is only decoration is `solid=False` (the nav grid is built from collision, the street far below Skyline is non-solid for that reason).
## 18. The rifle (WEAPON)

The rifle is modelled, not made of primitives: `Tools/mesh_weapon.py` (pure python: chamfered lofts, lathes, struts, planar/cylindrical UVs, six material ids) builds it in two detail levels,
`Tools/make_weapon_assets.py` turns it into `/Game/Characters/Weapon/SM_IARifle_FP` (first person, about 8000 triangles) and `SM_IARifle_TP` (carried by the characters, about 4800), plus the master `M_IAWeapon`
(`BodyColor AccentColor Glow Roughness Metallic Detail Tile Specular`, brushed-metal normal/roughness detail) and one instance per slot: `MI_IAWeapon_Body, Trim, Rubber, Accent, Core, Glass`.
The folder is under `/Game/Characters`, which is always cooked (the code loads the meshes by path). Rebuild after editing the model: `Tools\ue.ps1 -Script Tools\make_weapon_assets.py`.
- Rifle space: X forward, Y right, Z up, cm. The pistol grip is at about x 4, z -9.5 (the hand), the muzzle at `MUZZLE` (64.4, 0, 0.5) = `RifleMuzzle` in `IAPlayerCharacter.cpp`: the beam and the flash start there. If the model changes, update both and re-fit the hand with `Tools/probe_rifle.py` (it prints `TPRifleHandOffset/Rotation` for the scale in `RS`).
- C++ (`BuildWeapon`, `UpdateWeaponView`): one component with six `UMaterialInstanceDynamic`s (Accent slot = painted trim, Core = emissive, both in the player's colour). The first-person rifle follows the camera bob (`CamBobPhase/Alpha`), breathes, lags behind fast turns, kicks on a shot and pulls back when a wall is in front of the camera (one sphere sweep per frame); the core `Glow` is about 2 at rest and +2.8 right after a shot. Other players' rifles flare on `MulticastShotEffect`.
- Quick tuning without a rebuild: `-IAFPRifle=x,y,z,scale` (first person placement), `-IARifleOffset=x,y,z,pitch,yaw,roll,scale` (hand).
- Without the meshes the code falls back to the old primitive rifle, so a missing asset never crashes.

## 19. Main menu backdrop and camera (MENU)

- `Tools/make_map_menu.py` builds `/Game/Maps/MainMenu`: a stone gate in the golden hour (kits: matlib surfaces, generated meshes, catalogue props, flames, the `dusk` look with a photographic sky). The camera and the dais are placed together: `IAMenuPlayerController::SpawnPreview` puts the preview character 430 cm ahead and 190 cm to the right of the level's `MenuCamera`, so `HERO = CAM + (430, 190)` in the script. The key spot light, the rim light and the low sun (azimuth 10, seen through the gate opening) are made for that spot. Check `MAKEMAP_DONE` in the log; run it through `Tools\run_ue.ps1`.
- The controller copies the level camera into a movable runtime camera: a slow drift (about 2 degrees of yaw, a breath of pitch, a few cm sideways) that fades out while a screen opens, and a smooth move to a close-up of the character on the Character screen (`SIAMainMenu` calls `OnPageChanged` with the screen number; screen 3 = close-up). Everything is in `AIAMenuPlayerController::UpdateMenuCamera`.
- `IAMenu::Gradient(Orient_Horizontal | Orient_Vertical, {{pos, colour}, ...})` draws a Slate gradient without a texture (Slate calls its two types the other way round, the wrapper hides that). It only paints, so the loading screen thread can use it. `IAMenu::SpacedFont(size, bold, letterSpacing)` gives titles letter spacing.
- The loading screen (`IALoadingScreen.cpp`) shows the selected map's thumbnail twice: dim and full screen behind everything, sharp in the card, with an eased progress bar.
## 20. Character gear (GEAR)

The 15 characters wear modelled gear (helmets, plates, pauldrons, bracers, greaves, belts, packs, capes, wings ...) instead of the primitive accessories of the roster. Everything is generated by python (no downloads):
- `Tools/mesh_char.py` pure python mesh builder (`GM`: lathes, sweeps, chamfered boxes, curved plates with bevelled edges, cloth). `Tools/gear_body.py` the measurements of the two Mannequins (bone positions, torso ellipses per height, head), `Tools/gear_parts.py` the pieces (`Helm`, `cuirass`, `pauldron`, `bracer`, `greave`, `hang` cloth ...), `Tools/gear_chars_a/b/c.py` one function per character (`bulwark(B)` ...) returning a `Kit` (pieces per bone, absolute reference-pose coordinates).
- **Roles**: each vertex carries a palette role in the second UV set (u = role: 0 Plate (suit colour), 1 Cloth, 2 Accent, 3 Team, 4 Trim (dark metal), 5 Glow (visors only), 6 Light; v = ambient occlusion). `M_IAGear` picks the colour, roughness and metallic of the role in the shader, so **one material and one draw call per piece**. Colours come from the roster (`IACharacterRoster.h`: Body, Accent, Roughness, Metallic, AccentMetal, optional `GearCloth`), the team colour is applied like on the body; `IAGear::Attach` (`IACharacterGear.cpp`) makes one dynamic instance per character.
- `Tools/make_gear_assets.py` builds `/Game/Characters/Gear/M_IAGear`, `MI_IAGear`, `SM_<Name>_<bone>` (mesh in the bone's local space with character axes, so it attaches with no offset) and writes `Source/InstagibArena/IACharacterGear.inl` (bone + asset path per look; rebuild the C++ when a character gains or loses a bone). `IA_GEAR_ONLY=0,3` rebuilds some looks only, `IA_GEAR_FORCE=1` the material. The folder is under `/Game/Characters` (always cooked). When no gear mesh loads, the roster's primitive `Parts` are used again.
- Look without the engine: `Tools/probe_mannequin.py` (once, dumps the Mannequins to `~/AssetCache/char_probe`), then `python -I Tools/gear_preview.py 0 5` (software renderer: front, side, back, 3/4 with a height ruler; PNG in `~/AssetCache/char_probe`). In the engine: `Tools/gear_shots.ps1 -Name x -From 5 -View mid` (five characters in a row in DM-Foundry; views front, mid, back, side, q34, close; `-Mode TDM -Extra "-IAShowroomTeams"` for team colours, `-Extra "-IAShowroomWalk -IAShowroomJump -IAShowroomCrouch"` for poses), `Tools/gear_game_shot.ps1` (bot match), `Tools/gear_botrun.ps1` (headless bots).
- Rules of thumb: a thin cone or sheet is only visible from one side unless it is `double=True` (lathe) or `cloth`; under 6k triangles per character; mannequin bones move rigidly, so skirts and capes stay short or hang behind the legs; the torso table in `gear_body.py` is measured on the mesh, plates stand 1-2 cm off it.

## 21. Capture the Flag (CTF)

Two teams (red 0, blue 1), URL option `Mode=CTF`. Each team has a flag on its base; the match is decided in `AIAGameMode` on the server, the flag actors only replicate their state.

**Rules.** An enemy touching a flag that is Home or Dropped takes it (radius `FlagTouchRadius` 130 cm). The carrier scores a capture (+1 team point, the flag goes home) by touching his own base (`CaptureRadius` around `AIAFlagBase`) **while his own flag is Home**. A team mate touching his own Dropped flag returns it at once (`Returns` +1). A dropped flag goes home alone after `FlagReturnSeconds` (15). A carrier who dies, falls out of the world or disconnects drops the flag where he stood; no floor below it or a floor under `kill_z` sends it home at once. Nobody can pick up the own flag. No other restriction for a carrier. Kills are frags (`Kills`) as in TDM but do not score for the team; `Captures`, `Returns`, `FlagKills` (killed carriers) are replicated counters in `AIAPlayerState`. `ScoreLimit` = captures (default 5), `TimeLimit` default 15 min (`ScoreLimit=0?TimeLimit=0` = unlimited); at the time limit more captures win, equal = draw (no sudden death). Teams are balanced like TDM, respawn like TDM (spawn protection stays) but a team uses its own starts (`PlayerStartTag` "Red"/"Blue", untagged starts are used by both, own tagged starts are preferred; FFA and TDM still use every start) and never spawns within 11 m of the enemy base.

**Classes.** `AIAFlagBase` (`IAFlagBase.*`, the map contract: `FlagTeam`, `CaptureRadius`; pad with a team ring, hides itself outside CTF; `bFallback` = made by the game mode), `AIAFlag` (`IAFlag.*`, replicated State/Carrier/RestLocation/DropEndTime, `bAlwaysRelevant`, no movement replication: every machine places it from `RestLocation` or attaches it to the carrier's `spine_03` bone; a dropped flag falls with a local bounce; the carrier does not see his own flag), `AIAGameMode::SetupCTF/TickFlags/PickUpFlag/DropFlag/ReturnFlag/CaptureFlag` (25 Hz touch checks), `AIAGameState::MulticastFlagEvent` (banner, kill feed row, sound on every machine; `EIAFlagEvent`), HUD `DrawFlagMarkers/DrawFlagPrompt`, `SIAScoreboard` (CAPTURES/RETURNS columns), `AIABotController::UpdateObjective/MoveToObjective`.

**Maps.** One `AIAFlagBase` per team on the ground in the middle of the base (`unreal.IAFlagBase`, `flag_team`, optional `capture_radius`), team starts tagged "Red"/"Blue". **No bases, no problem:** the game mode groups the starts (tags if both teams have tagged starts, else the two farthest apart), takes the start nearest to each group's centre and puts a base on the nearest flat free spot (line traces, capsule overlap test); the log says `CTF: FALLBACK BASES on <map>` and the position of both bases.

**Assets.** `Tools\make_ctf_assets.py` (run it through `Tools\ue.ps1`) builds `/Game/CTF`: `SM_IAFlagPole`, `SM_IAFlagCloth` (pennant, waves in `M_IAFlag` through world position offset: `TeamColor`, `WaveStrength`), `SM_IAFlagBeam` + `M_IAFlagBeam` (additive, faint, `Intensity`), `SM_IABasePad` + `M_IABase` (ring = capture zone), `M_IAFlagMetal`. `/Game/CTF` is in `DirectoriesToAlwaysCook`. Without the assets engine shapes are used. Sounds: `gen_audio.py` `ctf_cues()` (`IA_AUDIO_ONLY=1` writes only those five files), import with `IA_AUDIO_ONLY=flag_ ... import_audio.py`, `EIASound::FlagTaken/Dropped/Returned/Captured/Lost`.

**Bots.** Roles by place among the living bots of the team (sorted by slot): attacker, defender, balancing (attacks unless the team leads and its flag is home), attacker ... The carrier runs home (no combat stops, it still shoots and dodges), everybody hunts the carrier of the own flag, the two bots nearest to a dropped own flag go and touch it, attackers escort a team mate who carries, defenders patrol within 6.5 m of the own base. The enemy carrier of the own flag is the first target (distance x 0.3). Path searches: at most one per frame in the whole world (`UIANavGrid::TryConsumePathBudget`), one bot searches at most 4 times a second and waits 1.5 s after a failed search; `FindNearestNode` uses a cell index. A bot that holds a flag for 110 s sends it home (`BOT CARRY TIMEOUT` warning in the log: none in the tests).

**Menu.** Custom Game / Host: three game types, the score row is "Capture limit" (1..10, default 5, stored apart from the frag limit: `FIAMatchSetup::CaptureLimit`, `GameType`; an old file with `TeamGame` still loads). `-IAMenuScript="gametype=2;page=1"`.

**Tests and screenshots.**
- Bot match on any map: `UnrealEditor-Cmd.exe <uproject> "/Game/Maps/DM-Foundry?Mode=CTF?Bots=8?BotSkill=3?ScoreLimit=0?TimeLimit=0" -game -nullrhi -nosound -unattended -nosplash -IAReport "-abslog=ctf.log"` (3 minutes; look for `CTF: ... CAPTURED`, `FALLBACK BASES`, `CTFREPORT`, `NAVSTATS`, `BOT CARRY TIMEOUT`).
- Multiplayer: listen server `"/Game/Maps/DM-Foundry?listen?Mode=CTF?Bots=4" -game -windowed ... -IAReport` and a client `127.0.0.1`; compare `REPORT` and `CTFREPORT` lines (flag states, carrier, captures) of both logs, no `LogNet` warnings.
- Dev flags (game mode): `-IACtfForce=S[,Team]` (S seconds after the fight starts the first human, else bot, of that team takes the enemy flag), `-IACtfDrop=S` (carried flags drop), `-IACtfCapture=S` (the carrier is moved onto his base). Screenshots: `-IAShotCamFlag=Team,Distance,Height,YawAround` (camera that watches a flag; home, carried or dropped), `-IAFlagCarry=x,y,z,pitch,yaw,roll,scale` (how the flag sits on the back), plus the usual `-IAShotDelay/-IAShotName/-IAShotCam`.

## 22. Big maps and DM-Quarry (BIG2)

`Tools/make_map_quarry.py` builds DM-Quarry (about 13200 x 8600 uu playable, CTF / FFA / TDM). Its pieces:
- `Tools/quarry_terrain.py` (pure python, run with UE's embedded python without the editor): ONE height function `height(x, y)` for the whole map (terraced pit, haul roads, heaps, base platforms, cliff walls), the tunnel rectangles and a cheap nav estimate. `python -I Tools/quarry_terrain.py` writes `Saved/quarry_top.png`; `Tools/_qt_nav.py` prints which parts of the map are connected.
- `Tools/mapkit_big2.py`: `build_terrain(grid)` cuts the height field into tile meshes per material; steep triangles are clipped against gently dipping rock beds, so strata are clean bands of one rock surface; `build_tunnels(grid)` makes floors, walls and ceilings of the underground corridors (the terrain sheet is cut open where the corridor is not roofed by the ground); `K` is a mesh kit (beams, rails, stairs, silos, trusses, lattice towers).
- `Tools/quarry_struct.py`, `quarry_struct2.py`, `quarry_bases.py`: structures as merged meshes (`Struct` holds one mesh per material and solid flag, `put_struct` commits and places them): walls with openings, halls, silos, conveyors, girder bridges, haul trucks, excavators, rigs, containers, the red crushing plant and the blue loading dock.
- NavGrid facts learned here (`IANavGrid.cpp`): a cell becomes a node only when the capsule fits 2 cm above the surface, so every slope above about 20 degrees and every stair with open or high risers has NO nodes (bots cannot use them); make walkable connections ramps of 18 degrees or less. `Tools/navdump_quarry.ps1` dumps all nodes (`-IANavDump=0,0,0,30000`) and `Tools/_qt_navmap.py` draws them. `Tools/bottest_quarry.ps1 -Mode FFA|TDM` runs the 100 s headless bot match.
- CTF contract: two `unreal.IAFlagBase` (`flag_team` 0 red / 1 blue) at the centre of the base halls, PlayerStarts with `player_start_tag` "Red" / "Blue" plus untagged ones in the middle.

## 23. Campaign "The Apex League" and Survival

- **Data** (`IACampaignData.h`, pure data): 5 factions, the story cast, 5 chapters, 20 matches (`FIACampaignMatch`: map, mode, skill, enemy/ally counts, limit, faction, recruit, briefing/win/lose lines, `FIABonusGoal` for the third star), 2 endings. Character looks beyond `IACharacters::LookCount` wrap onto existing ones until the new characters exist (`LookKestrel`, `LookSovereign`).
- **Progress** (`UIACampaignSubsystem`, a GameInstance subsystem): hero, difficulty (-1/0/+1 skill), next match, stars, squad (max 3 recruits), ending. Saved in `GameUserSettings.ini` section `InstagibArena.Campaign`. `BuildTravelOptions(match)` makes the URL; `BuildAllyLooks/BuildEnemyLooks` choose the characters (squad first, then the League's draft; the enemy faction first). `LastResult` and `bOpenLadderOnMenu` bring the player back to the ladder after a match.
- **Game mode**: URL option `Camp=1..20` (`GetCampaignMatch`). The roster is scripted in `SpawnBots`, the human is team 0 (red) with the allies, the enemies are team 1; a duel has one bot. A campaign match never restarts by itself. `ReportCampaignResult` (in `FinishMatch`) records win, stars (1 win, 2 clear win = at least 1.5 x the opponent, 3 bonus goal) in the subsystem.
- **Survival** (`Mode=Survival`, `ScoreLimit` = waves, `TimeLimit`): the humans and allies are team 0 and the waves team 1. Wave n has `SurvivalEnemyBase + n - 1` bots (at most 10), created by `SpawnWaveBot`; nobody respawns during a wave, `StartWave` revives the squad. `CheckWaveState` (from `OnPlayerKilled`) ends a wave, wins after the last one, loses when the whole team 0 is down or the clock ends. `RedScore` = waves cleared, `BlueScore` = enemies left, shown by the HUD as CLEARED / ENEMIES. `AIAGameState::Wave/WaveEnemiesLeft` are replicated.
- **UI**: `SIAMainMenuCampaign.cpp` (home, new campaign, ladder with chapter arrows, star squares, endings), the results screen has CONTINUE and RETRY in a campaign match (`SIAMatchResults`).
- **Tests**: `Tools\camp_botrun.ps1 -Match N -MapName X -Opts "Mode=...?Camp=N"` (headless, starts a test campaign with `-IACampStart`); `Tools\menu_shot.ps1 -Page 7 -Tab 0|1|2` (screens of the campaign menu).

## 24. Space arenas and the campaign characters

- **Skies:** `Tools/make_space_sky.py` (pure python, about 5 s each) writes `~/AssetCache/hdri/space_{orbital,derelict,nexus}.hdr` (2048 x 1024 long-lat, stars, nebula, a lit planet / moon, a black hole with an accretion ring, a sun disc). `Tools/import_space_skies.py` imports them as `/Game/Sky/T_Sky_space_*`; `maplooks.py` has the looks `space_orbital|derelict|nexus` (one hard sun, no atmosphere or fog, ambient light from the cube map: `ambient_gain` 6-15, `ev` 1-2.4 per map).
- **Maps** (`Tools/make_map_orbital.py`, `make_map_derelict.py`, `make_map_nexus.py`, boxes and columns only, matlib surfaces, glass and glow materials): Orbital = a long concourse with a slotted ceiling, a reactor core, two raised decks with ramps and pads, two base halls; Derelict = a cargo bay with a hole in the floor (kill), catwalks, a cross walkway, low corridors, engine room and bridge with a nebula window; Nexus = a stone disc beside a black hole, a dais with four ramps, eight arches, gold gateways behind the bases. All have CTF bases (`IAFlagBase`), Red / Blue start tags and 8 untagged starts; tested headless with `Tools\ctf_botrun.ps1 -Map X`. Screenshots: `Tools\map_shot.ps1 -Map X -Cams "x,y,z,pitch,yaw;..."`. The campaign plays on the real maps once they are in `IAMapList.h` (`UIACampaignSubsystem::ResolveMapName` has stand-ins otherwise).
- **Characters 15-36** (Kestrel, Sovereign, four per faction): `Tools/gear_chars_d.py` (Rustborn) ... `gear_chars_i.py` (Kestrel, Sovereign), roster entries in `IACharacterRoster.h` (`LookCount` 37 then, 44 since section 27). Preview: `python -I Tools/gear_preview.py N` (use the engine's python), assets: `run_ue.ps1 -Script Tools\make_gear_assets.py -Env "IA_GEAR_ONLY=15,16,..."`, in game: `Tools\gear_shots.ps1 -Name x -From N`.
- **Radio chatter:** `IACampaign::Chatter(chapter)`, two lines per campaign match (at 22 s and 110 s into the fight).

## 25. Enlarging the old maps

`MapBuilder.scale_world(s)` (called by `finish(scale=s)`, env `IA_MAP_SCALE=1` builds a map at its original size) makes a finished level s times bigger across and along (x, y) and keeps all heights, so steps, jump heights and the NavGrid limits (`MaxStepUp` 110) still work. Boxes, generated meshes and wide cylinders are moved and stretched; tilted slabs (ramps) keep their rise (new pitch, longer); catalogue props, slender columns, lights (longer reach), flames, flag bases and PlayerStarts are only moved; jump pads fly s times as far at the same flight time. The sky, sun, sky light, fog and post process are untouched. Foundry, Temple, Dock, Skyline, Neon and Glacier are built at 1.3, Forge at 1.35. **Forge is built at 1.35**: at 1.3 (and 1.2, 1.25) two gantries were cut off from their ramps. The cause is not the geometry but where the NavGrid cell centres fall: a cell centre that lands exactly on the join of ramp and deck gets no node (the capsule test fails there), so the 150 cm link is missing. 1.28, 1.35 and 1.4 are fine; `-IANavDump=X,Y,Z,R` lists the nodes near a point and the NavGrid log now prints the bounds of the biggest areas. If a map is changed and a start is suddenly cut off, try another scale a little higher or lower. Canyon is already huge. Uniform scaling (heights too) was tried first and broke Temple (stairs above the nav step limit).


## 26. Character detail layer, music

- `Tools/gear_detail.py` adds a shared detail layer to looks 17-36 (called by `gear_roster.build`): wrist and ankle cuffs, thigh straps, a segmented spine ridge and a faction emblem on the left chest (hex bolt for the Rustborn, medallion for the Legion, glow diamond for the Syndicate, patch for the Void Corps, triangle rune for the Hollow Court). Colours and materials of the roster entries were made darker and more metallic (`IACharacterRoster.h`; colours are linear, so 0.35 looks mid-grey in game).
- Music: `EIAMusic::Campaign` (`M_CampaignTheme`, played on the campaign screens), `Battle` now picks `M_Finale` in campaign match 20 and `M_Space01` (65 percent) on Orbital, Derelict and Nexus. The songs are made in `Tools/gen_audio.py` (`SONGS`), rendered with `render_song(name, spec)` and imported with `import_audio.py`; re-importing re-saves every sound asset, so revert the unchanged ones (`git checkout Content/Audio/SFX ...`).

## 27. Characters 37-43 (reward characters)

- **Who:** the four Obsidian Crown fighters 37 Regent (captain, 1.10), 38 Sentinel (heavy, tower shoulder guard), 39 Harrier (scout, Quinn), 40 Oracle (caster, gold half-mask and floating ring), 41 Voss (the League director, white and black suit, monocle, no helmet), 42 Wildcard (hooded cloak, blank mask, one orange line) and 43 Gino Gasket (the only humorous one: a short plumber with a fan moustache, a red cap with a pipe-wrench badge, overalls, white gloves). Gear: `Tools/gear_chars_j.py`; roster entries at the end of `IACharacterRoster.h`. Everything is generated, nothing is downloaded. The Crown share a gold crown badge on the chest (`crown_badge`) and get the cuffs and thigh straps of `gear_detail.py` (no ridge under Regent's cape and Oracle's coat); 41-43 have no detail layer.
- **Not random:** `IACharacters::LookCount` is 44, `IACharacters::PlayableByDefault` is 37 and `IACharacters::IsPlayableByDefault(i)` says whether a look needs no unlock. Random picks use only the first 37: the bots of a free match (`AIAGameMode::SpawnBots`), Survival waves without a scripted list (`StartWave`) and the filler of the campaign draft (`PickLooks`). Scripted campaign rosters, `?Char=N` and the character screen still accept all 44. The locking itself belongs to the profile subsystem (not done here). Names: `IACharacters::LookRegent ... LookGino`.
- **Palette overrides:** `FIACharacterLook::GearRoles` (a list of `FIAGearRole {Role, Color, Roughness, Metal, Glow}`) overrides single roles of the gear material in `IAGear::Attach`; negative values / alpha 0 keep the default. The Crown use it for glossy obsidian plate (roughness 0.3, the default plate clamp is 0.5) and a red glow beside the gold accent; Gino for brass trim, a non-glowing dark brown glow role (moustache, belt, boots: `Glow` 0) and white gloves. `gear_chars_j.PREVIEW_ROLES` gives the software preview the same colours.
- **Size and hit boxes:** `MeshScale` only scales the skeletal mesh and its gear (Gino is 0.92, Regent 1.10, Sentinel 1.12). The collision capsule (34 x 92) is the same for every character and the shots are traced against it, so nobody is easier or harder to hit.
- **Names with spaces:** `gear_roster.py` accepts them and `make_gear_assets.py` drops the space in asset names (`SM_GinoGasket_head`).
- **Gotcha:** `gear_parts.Helm(...).shell(z_bot=...)` with a `z_bot` above the helmet's equator folds the shell back down to the equator (it then covers the eyes). For a cap or hair that starts high, pass `z_eq` just below `z_bot` (Gino's cap) or build the surface yourself (Voss's hair).
