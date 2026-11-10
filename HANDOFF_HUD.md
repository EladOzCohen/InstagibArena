# HUD engineer handoff (WIP)

Branch: `worktree-agent-a2aa4a07693255a52` (based on main a3fa032). Nothing has been built or run yet.

## Compiles?
NO. `IAGameMode.h` is rewritten but `IAGameMode.cpp` is still the old file, so the module does not build until the .cpp is updated
(new members: `ChoosePlayerStart_Implementation`, `StartNewMatch`, `BeginWarmup`, `StartLive`, `ScheduleRespawn`, `AnnounceKillMedals`,
`UpdateLeadStates`, `CheckFragsLeft`, `FinishMatch(Text, WinnerPlayerId, WinnerTeam)`, dev hooks `SetupDevHooks`).
`IAPlayerState.*` and `IAGameState.*` are new/finished but never compiled.

## Done (written, unbuilt, unverified)
- `Tools/gen_audio.py`: `hud_cues()` appended at the END (16 cues: count_tick, count_go, clock_tick, warning, first_blood,
  medal_low/mid/high, streak_low/mid/high, lead_gain/lose/tie, victory, defeat). Generated once into `Tools/audio_out/sfx`
  (gitignored) with UE's python (`C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe`,
  run in `Tools`: `python -c "import gen_audio; gen_audio.hud_cues()"`). Not listened to, not imported yet.
- `IAPlayerState`: replicated ShotsFired, ShotsHit, Streak, BestStreak, MultiKill; server-only LastKillTime, LeadState;
  `RegisterKill/RegisterDeath/ResetMatchStats`; static `RegisterShot(const APawn*)` (counts the shot AND returns false when the
  phase is not Live, i.e. it is the server-side fire gate) and `RegisterHit`.
- `IAGameState`: `EIAMatchPhase {Warmup, Live, Ended}`, replicated Phase, PhaseEndTime (server time), WinnerPlayerId, WinnerTeam;
  `IsFiringAllowed()`, `GetPhaseSecondsLeft()`; `EIAAnnounce` enum; reliable multicasts `MulticastKillFeed(KillerId, VictimId)` and
  `MulticastAnnounce(Kind, Subject, Param)`; local kill feed list `GetKillFeed()` and `OnAnnounce` delegate for the HUD.
- `IAGameMode.h`: new design (see its header comment). RestartDelay is now the results time (20 s), WarmupSeconds 5, MultiKillWindow 4.

## Not started
IAGameMode.cpp rewrite, IAPlayerController (death cam, `ClientYouDied`, phase polling in `PlayerTick`, results widget lifecycle,
`IsMenuOpen()` returning true when frozen in Ended, input mode restore after pause closes), IAHUD redesign, `SIAScoreboard` and
`SIAMatchResults` Slate widgets, audio enum/path entries, import of the audio, the two ServerFire lines, dev flags, all testing.

## Next steps, in order
1. Rewrite `IAGameMode.cpp` per the header: 
   - `HandleMatchHasStarted`: create bot controllers WITHOUT `RestartPlayer`, then `BeginWarmup()`.
   - `BeginWarmup`: Phase=Warmup, PhaseEndTime=now+WarmupSeconds, timer -> `StartLive`.
   - `StartLive`: Phase=Live, start the 1 s clock timer (TickClock only when Phase==Live), `RestartPlayer` every pawn-less controller (bots spawn here).
   - `FinishMatch`: Phase=Ended, bMatchOver, winner fields, PhaseEndTime=now+RestartDelay, timer -> `StartNewMatch` (do NOT call EndMatch/RestartGame).
   - `StartNewMatch`: ++MatchGeneration, reset GS scores/clock/winner, `ResetMatchStats` on all PlayerStates, destroy all pawns, `BeginWarmup`, `RestartPlayer` humans.
   - `OnPlayerKilled`: ignore scoring unless Live (in Warmup just respawn humans after 1 s); stats via `RegisterKill/RegisterDeath`; `GS->MulticastKillFeed(killerId or -1, victimId)`;
     medals (first blood; multi 2/3/4/5+ = double/multi/ultra/monster; streak 5/10/15/20/25 = spree/rampage/dominating/unstoppable/godlike);
     then `CheckScoreLimit`, and if still Live `UpdateLeadStates` (took/lost/tied, per human by PlayerId; TDM per team with Subject=-1, Param=team) and `CheckFragsLeft` (Left 3/2/1);
     `ClientYouDied` to the victim; respawn via `ScheduleRespawn` (captures MatchGeneration; skips bots in Warmup and everyone in Ended).
   - `ChoosePlayerStart_Implementation`: score every `APlayerStart` (distance to nearest living other pawn, line of sight penalty, occupied < 220 uu, recently used penalty, small random), pick best.
   - Dev hooks (`#if !UE_BUILD_SHIPPING`, command line): `-IAWarmup=S`, `-IAResults=S`, `-IAFakeKills=delay` (fake 5 kills by the local human on bots via OnPlayerKilled), `-IAKillMe=delay` (ApplyDamage from a bot to the local pawn).
2. Add to `IAPlayerCharacter.cpp` ServerFire exactly two lines (FEEL owns the file): after `LastFireTime = Now;` add
   `if (!AIAPlayerState::RegisterShot(this)) { return; }` and before `ClientHitConfirm(Victim->IsDead());` add `AIAPlayerState::RegisterHit(this);`.
3. Append to `EIASound` (after MatchEnd) the 16 cues and the path switch in `IAAudioSubsystem.cpp` (names -> `/Game/Audio/SFX/S_CountTick` etc.:
   import_audio names are `S_` + capitalised words, e.g. `count_tick` -> `S_CountTick`). Run `Tools/import_audio.py` via the editor commandlet
   (needs `Tools/audio_out/sfx` and an existing `music` folder; only the 16 new wavs are there in this worktree, so existing assets are not re-imported).
4. `IAPlayerController`: `ClientYouDied` (RPC), local `ACameraActor` death cam (start at victim eye, ease to a pulled-back point looking at the killer, line-trace for walls),
   `PlayerTick` polling of the phase, results widget, freeze (`IsMenuOpen()` includes frozen), `ApplyInputMode` after the pause menu closes.
5. Slate: `SIAScoreboard` (rank, name, kills, deaths, K/D, acc %, best streak, ping; TDM grouped by team; local highlighted; bots tagged and "BOT" ping) and
   `SIAMatchResults` (winner banner, scoreboard, PLAY AGAIN host-only + countdown, MAIN MENU via `ReturnToMenu`). Use `IAMenuStyle` (use only).
6. `IAHUD` redesign (canvas): top bar (FFA rank + leader score + timer; TDM red vs blue), bottom-left stats, 4 crosshair styles from `IASettings`,
   kill feed top-right (5 entries, fade, local highlight, suicide/fell wording), centred banner queue, countdown numerals + FIGHT!, last-10-s clock ticks,
   death panel (killer name, character, distance, respawn timer, arrow toward killer), Tab scoreboard via the `Scoreboard` key. Scale by `ClipY/1080`.
   Remove the MatchStart sound in `AIAHUD::BeginPlay`.
7. Build (via `Tools\exclusive.ps1`), screenshots at 1280x720, 1920x1080, 2560x1080, bot matches on two maps, host+client test with match end and restart,
   no LogNet warnings. Commit.

## Known problems / notes
- Path is long: `subst W:` was mapped to the worktree for builds (`subst W: <worktree>`); it may still exist. The `Saved_build0.txt` stray file was removed.
- `python` is not on PATH; use UE's bundled python (above).
- Idea not decided: spawn protection without touching the character, by setting the capsule's ECC_Pawn response to Ignore for ~1.5 s on the server (shots pass through). Risky for pawn collision; probably only report it.
- Warmup fire lock on the client (recoil without shot) could be improved by unmapping the Fire key in the mapping context during Warmup.
