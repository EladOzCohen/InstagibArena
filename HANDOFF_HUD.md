# HUD engineer handoff (final state)

Branch `worktree-agent-a2aa4a07693255a52`. The branch compiles; no process left running.

## What exists (all built and run)
- Match flow (IAGameMode / IAGameState): Warmup 5 s -> Live -> Ended -> in-place restart. Server authoritative, replicated `Phase`, `PhaseEndTime`, winner fields.
- Per-player stats (shots, hits, streak, best streak, multi-kill), `SlotId` (unique id, engine PlayerId is not unique for bots).
- Kill feed (multicast), medals, spree, lead changes, frags left, countdown, FIGHT!, clock ticks, 16 generated cue sounds.
- HUD on the canvas (Slate fonts from the Roboto UFont so text is crisp), 4 crosshair styles from IASettings, Tab scoreboard + results screen (Slate).
- Death panel + death camera on the killer (client-spawned camera actor), respawn bar, arrow toward the killer.
- Smart spawning (distance + line of sight + recency).
- Spawn protection: 1.5 s after a spawn and at the start of the fight, the server sets the capsule/mesh response to `ECC_Pawn` to Ignore so shots pass through; shooting ends it (`AIAPlayerState::RegisterShot` -> `AIAGameMode::EndSpawnProtection`). Replicated `AIAPlayerState::SpawnProtectEndTime`; HUD cue = cyan edge glow + bar for you, a cyan ring around protected players.
- Fire lock on the client: in countdown and on the results screen the Fire key is unmapped from the mapping context (`AIAPlayerController::SetFireLocked`), so no recoil; the server also refuses the shot.

## Evidence (see the final report for details)
Screenshots in `Saved/IAShots` (not committed): a_*, b_*, d_* at 1280x720, 1400x875 and 1400x600. This PC cannot open a window larger than about 1400x875.
Logs in the shared scratchpad `hud/` folder: mp1..mp6 (host + client), bots_DM-*.log, probe.log (`PROTECTION PROBE: unprotected hit=1, protected hit=0, after protection hit=1`).

## Not verified
- True 1920x1080 / 2560x1080 renders (window clamp). Layout scales with ClipY / 900.
- Audio playback (all tests -nosound).
- Remote client death camera: log lines prove the RPC and camera start on the client; the visual on a real client was checked with a rendered client if `mpv*.png` exist in `Saved/IAShots` (see report).

## Ideas not done
Kill feed weapon icon, per-map spawn tuning, protecting from "spawn kill" by bots needs bots not to shoot instantly (they lose protection when they fire),
team colour for the death panel, options menu entries for the HUD scale (MENUS engineer).

## Helpers (scratchpad is shared between agents, use the `hud/` subfolder)
build.ps1, shot.ps1, batch.ps1 -Set A|B|C|D, mp.ps1, mpv.ps1, mpset*.ps1. `subst W: <worktree>` for short paths. Everything heavy through `Tools\exclusive.ps1`.
Dev flags (non-shipping): -IAWarmup, -IAResults, -IAFakeKills, -IAKillMe, -IACrosshair=style,color,scale (saves the settings), -IAProtProbe.
`Config/DefaultEngine.ini` is `skip-worktree` locally so the editor's AndroidFileServer block is never committed.
