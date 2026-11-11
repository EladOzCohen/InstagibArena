# For developers

Everything you need to build and change Instagib Arena. (Players: you do not need any of this, see the
[main page](../README.md) to download and play.)

For build and test commands, conventions and gotchas, read [DEVELOPMENT.md](DEVELOPMENT.md) first.

## What you need
- Unreal Engine **5.8** (Epic Games Launcher)
- Visual Studio 2022 with the **Game development with C++** workload
- Optional: [Inno Setup 6](https://jrsoftware.org/isinfo.php) to build the installer

## Get the project running
```powershell
git clone https://github.com/EladOzCohen/InstagibArena.git
cd InstagibArena

# Epic's Mannequin characters are not stored in this repo (they are part of Unreal Engine's content).
# This copies them from your own Unreal Engine install:
powershell -ExecutionPolicy Bypass -File Tools\restore_mannequins.ps1
```
Then open `InstagibArena.uproject` (or build `InstagibArenaEditor` for Win64 with Visual Studio) and press Play.
The game starts on the main menu.

## Project layout
| Folder | What is there |
|---|---|
| `Source/InstagibArena` | All game code (C++): movement, animation, weapon, game modes, bots, HUD, menus, audio, effects |
| `Content/Maps` | The eight maps and the main menu level |
| `Content/Audio` | Sound effects and music (generated, see below) |
| `Content/UI` | Map pictures for the menu (made by `Tools/make_thumbnails.ps1`) |
| `Content/Characters` | The character material; the Mannequins are restored by the script above |
| `Tools` | Python and PowerShell tools that build maps, audio, thumbnails and the installer |
| `Tools/installer` | The Inno Setup script of the installer |
| `docs` | The development guide, this file, and the landing page (`index.html`, served by GitHub Pages) |

## Tools
- **Sound and music** are synthesized from scratch by `Tools/gen_audio.py` (standard library only), then imported with
  `Tools/import_audio.py`. Nothing is sampled, so there are no licensing questions.
- **Maps** are built by scripts (`Tools/make_map_*.py`, helpers in `Tools/mapkit.py`) run headless with
  `UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript=Tools/make_map_temple.py -unattended -nullrhi`.
- **Map pictures** for the menu: `Tools/make_thumbnails.ps1` (reads `IAMapList.h`, so a new map only needs a line there).
- **Character look** is defined in `Source/InstagibArena/IACharacterRoster.h` (colors and attached parts per character).
- **Game options** travel in the map URL, for example
  `/Game/Maps/DM-Temple?Mode=TDM?ScoreLimit=30?TimeLimit=10?Bots=6?BotSkill=2?Char=4`.
- **Build the Windows package and the installer:** `powershell -File Tools\package_and_installer.ps1`.
- **Testing without a screen:** `IADevSubsystem` adds command-line options for development builds, for example
  `-IAShotDelay=20 -IAShotName=test` (screenshot and quit), `-IAReport` (log what a machine sees, for comparing a host and a client),
  `-IAWalk`, `-IAFireEvery=2`, `-IAShowroom=X,Y,Z,Yaw` and `-IAPreviewCycle`. The full list is in [DEVELOPMENT.md](DEVELOPMENT.md).

## Making a release
1. Raise the version in `Source/InstagibArena/IASettings.h` (`GameVersion`) and `Tools/installer/InstagibArena.iss` (`AppVersion`).
2. Run `Tools\package_and_installer.ps1`. It makes `Builds\InstagibArena_Setup_<version>.exe`.
3. Copy that file to `Builds\InstagibArena_Setup.exe` (the same name every time) and attach **that** file to the GitHub
   release. The big download button on the main page links to
   `releases/latest/download/InstagibArena_Setup.exe`, so the button always gets the newest version without any edit.

## Mac
Nothing in the code is Windows-specific, but a Mac build has to be made on a Mac with Xcode.
