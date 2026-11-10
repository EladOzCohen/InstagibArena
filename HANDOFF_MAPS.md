# HANDOFF - MAPS engineer (branch worktree-agent-a99df6f5d14760718)

## Setup notes
- docs/DEVELOPMENT.md and Tools/exclusive.ps1 are NOT in git; they live only in the main checkout (C:\Users\elado\Desktop\claude_projects\InstagibArena). Read/use them from there.
- No system Python. For gen_audio use UE's: C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe
- restore_mannequins.ps1 was already run in this worktree. Editor build was run twice and succeeded (with IAJumpPad and EIASound::JumpPad).
- Shell guard: heredocs and compound git commands are refused in this worktree; use Write/Edit tools and plain commands.

## Done (built, NOT yet run/looked at)
- Source/InstagibArena/IAJumpPad.h/.cpp: AIAJumpPad (trigger box, base + glow disc + cone, pulsing M_IABody Glow, point light, flash on launch, whoosh via EIASound::JumpPad). Overlap on all machines; LaunchCharacter on server (HasAuthority) and on the locally controlled character; 0.5 s cooldown per character. Properties: launch_velocity, pad_color.
- IAAudioSubsystem.h/.cpp: EIASound::JumpPad appended at the end (+ path /Game/Audio/SFX/S_JumpPad).
- Tools/gen_audio.py: jump_pad() whoosh appended. Wav generated into the session scratchpad only (not imported yet).
- Tools/mapkit.py extensions: launch_velocity(), MapBuilder.glow() (emissive MIC of M_IABody), fog(), jump_pad() (computes ballistic velocity, gravity 1127), light_strip(), frame(), check_starts() (logs START_LOS pairs).
- Tools/make_map_neon.py: DM-Neon (small night street duel map, 10 starts, 2 pads to arcade roof). Script written, never executed.

## Not started
- Maps Forge (lava pit, kill_z), Glacier (arctic outpost + ice cave), Canyon (big, bridges, spires). Designs: Forge medium indoor with lava hole + bridges + gantry + pads from island to gantry; Glacier outdoor snow plateau, central ridge with tunnel, huts, radio mast platform reached by pad; Canyon 8000x4800, chasm with bridges (kill_z), mesas W/E with ramps, spire tops via pads.
- IAMapList.h entries (append 4 lines), Config/DefaultGame.ini MapsToCook entries for the 4 maps (shared file, tiny append).
- Import S_JumpPad: import only jump_pad.wav (import_audio.py reimports everything; prefer a one-off import script) to /Game/Audio/SFX.

## Next steps in order
1. Import the whoosh (generate with gen_audio.py into a scratch folder, import jump_pad.wav as S_JumpPad).
2. Run Neon: powershell exclusive.ps1 -Command "& scratchpad\runmap.ps1 neon" (script at the session scratchpad; it runs UnrealEditor-Cmd with -ExecutePythonScript). Check MAKEMAP_DONE, START_LOS lines, fix.
3. Screenshots (-IAShotCam overview + 2 first person), fix lighting (point light intensities are small numbers, ~30-120, as in Dock; verify pad light level).
4. Bot test 8 bots 70 s, NavGrid "connected areas" must be 1 with starts all in it. Note: pads are not nav links; every pad destination needs a walking route too (stairs <=40 cm riser).
5. Build the other 3 maps the same way, then host+client pad test (DEVELOPMENT.md section 6), IAMapList, MapsToCook, menu check (-IAMenuPage=1).

## Known problems / unverified
- Nothing has been executed in-game. Neon script untested (possible API errors, e.g. check_starts line_trace_single signature, m.glow on M_IABody, unreal.IAJumpPad class name).
- Bots randomly walking onto a pad get launched; the bot code repaths when grounded with Delta.Z > 250, believed fine but untested.
