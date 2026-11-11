# Where we stopped (handoff note)

Written 2026-11-10 (late evening) when the owner went to sleep. Read this first when resuming.

## UPDATE 2026-11-11 (second interruption, token limit)

The four agents were resumed in the morning and worked for a while, then the owner's token limit forced another stop
(about 3 hours). Before stopping, each agent was asked to commit a final `WIP:` commit, refresh its
`HANDOFF_<NAME>.md` and release the heavy-job lock. **The `HANDOFF_*.md` files in the worktrees are newer than the table
below: trust them over the "Real state" section.** The MAPS branch already contains `main` (merged), and FEEL and MENUS
were given the same camera-settings snippet to add to `IASettings.*`.
Next session: check for leftover processes, read the four handoff files, check `git log --oneline main..<branch>` per branch,
resume the agents with SendMessage (or start new ones from the handoff files), then follow "How to continue".

## The big picture

Goal of this round: take Instagib Arena toward industry standard: **more maps, better UX and UI, more realistic
movement, physics and animation.** Graphics are fine as they are.

Released so far: **v1.0.0** and **v1.1.0** (new main menu, pause menu, settings). v1.1.0 is on GitHub with its installer.
Everything below is **after v1.1.0** and is **not released, not pushed, not merged**.

## What exists right now

### Shared base (committed on `main`, not pushed)
Commit `a3fa032` "Shared base for parallel work":
- `Source/InstagibArena/IAInputConfig.*`: one table of rebindable keys (Forward, Back, Left, Right, Jump, Fire, Scoreboard). Input mapping and the scoreboard key read from it.
- `IASettings`: crosshair style, colour and scale getters/setters.
- `Tools/exclusive.ps1`: a lock so heavy jobs (builds, game runs) take turns when several agents work at once.
- `docs/DEVELOPMENT.md`: how to build, run, take screenshots and test (single source of truth for working on the project).

### Four builder agents, each in its own git worktree and branch
They were launched in parallel and were asked to commit their work in progress as `WIP:` commits and to write a
`HANDOFF_<NAME>.md` file in the root of their worktree. **Read those four files first**, they say exactly what is done,
half done and not started.

| Agent | Area | Effort | Worktree (under `.claude/worktrees/`) | Branch | Handoff file |
|---|---|---|---|---|---|
| MAPS | 4 new maps (total 8), jump pads (`AIAJumpPad`) | medium | `agent-a99df6f5d14760718` | `worktree-agent-a99df6f5d14760718` | `HANDOFF_MAPS.md` |
| FEEL | movement tuning, crouch and walk, camera, 8-way locomotion animation, rifle in hands, ragdoll, decals | high | `agent-a95c2ed04ef78f716` | `worktree-agent-a95c2ed04ef78f716` | `HANDOFF_FEEL.md` |
| HUD | match flow (countdown, results), stats, kill feed, medals, new HUD, death cam, smart spawn | high | `agent-a2aa4a07693255a52` | `worktree-agent-a2aa4a07693255a52` | `HANDOFF_HUD.md` |
| MENUS | controls rebinding, settings tabs (video/audio/gameplay), map thumbnails, loading screen, first-run, polish | high | `agent-a50b41cc388d0bce2` | `worktree-agent-a50b41cc388d0bce2` | `HANDOFF_MENUS.md` |

Full path of a worktree: `C:\Users\elado\Desktop\claude_projects\InstagibArena\.claude\worktrees\<folder above>`.

**Careful:** the MAPS worktree was created from the older commit `2308648` (v1.1.0), so it does **not** contain the shared
base (`docs/DEVELOPMENT.md`, `Tools/exclusive.ps1`, `IAInputConfig`). Merge `main` into that branch before anything else.

Agent file ownership (to avoid conflicts) was: MAPS = map scripts, `mapkit.py`, `Content/Maps`, `IAJumpPad*`;
FEEL = `IACharacterMovement.*`, `IAPlayerCharacter.*`, animation; HUD = `IAHUD.*`, `IAGameMode.*`, `IAGameState.*`,
`IAPlayerState.*`; MENUS = `SIA*` menu files, `IAMenuStyle.*`, `IAMenuPlayerController.*`.
Append-only shared files (expect small merge conflicts): `IASettings.*`, `IAInputConfig.cpp`, `IAAudioSubsystem.*`,
`IADevSubsystem.*`, `Tools/gen_audio.py`, `Tools/import_audio.py`, `IAMapList.h`.

## Real state after the agents stopped (they worked only about 10 minutes)

All four stopped cleanly, committed everything as `WIP:` and wrote their handoff files. **No goal is finished, nothing was run in the game, and two branches do not compile yet.** What each one has:

| Agent | Last commit | Compiles? | What exists |
|---|---|---|---|
| MAPS | `849b6f3` | yes (built twice) | `AIAJumpPad` actor (never run), `mapkit.py` helpers (launch arc, glow, fog, jump pad, light strips, start-visibility check), `Tools/make_map_neon.py` (a night neon street duel map, written but **never executed**), jump-pad sound generated but not imported. Maps Forge, Glacier and Canyon not started. Nothing added to `IAMapList.h`. **Branch is based on `2308648`: merge `main` into it first.** |
| FEEL | `75f2ff3` | **no**: `IACharacterMovement.h` was rewritten, the `.cpp` is still the old file | Header with crouch/walk/landing/wall-find design, `restore_mannequins.ps1` also copies the Rifle animations, an animation probe script, a plan for a native `UAnimInstance` that blends the pack's sequences directly. Camera, ragdoll, decals, tests: not started. |
| HUD | `a12fcce` | **no**: `IAGameMode.h` was rewritten, the `.cpp` is still the old file | Match phases (warm-up, live, ended), per-player stats, kill-feed and announcement plumbing on the game state, 16 generated musical cues in `gen_audio.py` (not imported, not listened to). HUD drawing, results screen, medals logic, death cam, smart spawn: not started. The two `ServerFire` lines for shot statistics are not added yet (exact text in `HANDOFF_HUD.md`). |
| MENUS | `e08b6ea` | **unknown**: nothing was built after the edits | Menu toolkit in `IAMenuStyle` (slider, toggle, modal, tooltips, focus helpers), new settings keys (UI scale, motion blur, mute when unfocused, tutorial done, recent addresses, address validation), hover-sound enum. No screen uses them yet. Controls screen, settings tabs, thumbnails, loading screen, welcome overlay: not started. Likely compile trouble in `IAMenuStyle.cpp` (tooltip, navigation metadata, scroll box arguments). |

Notes from the agents worth keeping:
- There is no system Python. Use `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe`.
- `Tools/import_audio.py` re-imports every sound; to add just one sound, import only that wav with a one-off script.
- Jump pads are not navigation links: every pad destination also needs a walking route or a bot launched there gets stuck.
- The four new maps will also need `MapsToCook` lines in `Config/DefaultGame.ini`.
- Heredocs and compound git commands were refused inside the agents' worktrees; use the file tools for edits.
- The worktrees are marked "locked" by git (normal for agent worktrees). Use `git worktree unlock <path>` before removing one.

Because so little got done, the cheapest way forward is to treat each handoff file as a ready plan and relaunch fresh agents (or work directly) from there, one area at a time if the PC feels slow, instead of repeating the first launch.

## How to continue (in this order)

1. **Check nothing heavy is still running** (UnrealEditor, InstagibArena, UnrealBuildTool). Close any leftovers.
2. **Read the four `HANDOFF_*.md` files** and `git log` of each branch (`git log --oneline main..<branch>`).
3. **Decide per agent**: finish its remaining items (resume the agent by messaging it, or start a new one from its handoff file), or take the branch as it is.
   The agents' original assignments are summarised in the table above; the full briefs are in this conversation's history.
4. **Merge into `main`** one branch at a time (suggested order: MAPS, FEEL, HUD, MENUS), resolve the conflicts in the append-only files,
   and build after every merge (see `docs/DEVELOPMENT.md`, section 3).
5. **Wire up what the agents could not touch**: camera settings keys from FEEL (CameraBob, ViewRoll, ReducedMotion) into the settings screen,
   and any one-line hooks they listed in their reports.
6. **Integration checks**: headless bot matches on all maps, host + client test (positions and scores match, no `LogNet` warnings), screenshots of every menu screen and the HUD at 1280x720 and 1920x1080.
7. **A fresh reviewer agent** (high effort) to review the merged result: bugs, network correctness, performance, anything that would break the packaged build.
8. **Package and release** (`Tools\package_and_installer.ps1`): bump the version (`IASettings.h` GameVersion and `Tools/installer/InstagibArena.iss` AppVersion, suggested 1.2.0), update `README.md` (maps, features, controls, screenshots), test the installer silently, then ask the owner before pushing and publishing a GitHub release.

## Things to remember

- Nothing after commit `2308648` has been pushed to GitHub. `main` is ahead of `origin/main` by the shared-base commit (and the handoff note).
- The packaged build was last made for v1.1.0. A packaged build has not been tested with any of the new work.
- The editor re-adds an `[/Script/AndroidFileServerEditor...]` block with a token to `Config/DefaultEngine.ini`; remove it before every commit.
- Epic's Mannequin content is not in git: run `Tools\restore_mannequins.ps1` in any fresh checkout or worktree.
- The owner reads Hebrew; player-facing text in the game is English.
