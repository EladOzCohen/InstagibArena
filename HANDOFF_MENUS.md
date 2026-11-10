# HANDOFF - MENUS engineer (branch worktree-agent-a50b41cc388d0bce2)

Work stopped early on request. Nothing from this branch has been built or run since the edits below.

## State
- Branch was fast-forwarded to main (a3fa032) first: the worktree was created from an older commit and lacked docs/DEVELOPMENT.md.
- `Tools/restore_mannequins.ps1` was run; a baseline build of the untouched code succeeded (exit 0).
- Everything below is UNBUILT and UNTESTED. Files that may not compile yet:
  - `IAMenuStyle.h/.cpp` (new: HoverTick, MakeTip, KeyText, ScrollArea, FocusFirst, KeepNavigationInside, Slider, Toggle, Swatch, FIAModal; `Row` got a tooltip parameter; hover tick added to NavButton/Chip). Uses `SToolTip`, `FNavigationMetaData`, `SScrollBox`; API details not yet checked by a compiler. Expect small fixes.
  - `IASettings.h/.cpp` (appended MENUS block: UiScale, MotionBlur, MuteWhenUnfocused, TutorialDone, RecentAddresses, ValidateJoinAddress, ApplyStartupSettings).
  - `IAAudioSubsystem.h/.cpp`: `EIASound::UIHover` appended; sound asset `S_UiHover` does not exist yet (only a warning at runtime).
- `ApplyStartupSettings()` is not called from anywhere yet.

## Done (code written, not verified)
Shared widget toolkit and settings keys listed above.

## Not started
1. Build.cs: add `MoviePlayer`, `ApplicationCore` (and maybe `RHI`).
2. `Tools/gen_audio.py`: `ui_hover()` (tiny tick) appended at END + `"ui_hover"` in the sfx dict; run `import_audio.py`.
3. `SIAControlsPanel` (list `IAInput::GetBindings()`, click row, press key, Esc cancels, swap prompt via `IAInput::FindActionUsingKey`, reset to defaults, read-only mode for How to Play). Listen using `OnPreviewKeyDown` / `OnPreviewMouseButtonDown`.
4. `SIASettingsPanel` rewrite with tabs GAMEPLAY / VIDEO / AUDIO / CONTROLS (crosshair live preview as an SLeafWidget; resolutions from `UKismetSystemLibrary::GetSupportedFullscreenResolutions`; display mode; VSync; FPS cap via `SetFrameRateLimit`; quality via `SetOverallScalabilityLevel`; motion blur; UI scale via SDPIScaler; apply-and-confirm with `FIAModal` and 10 s auto-revert; mute-on-focus-loss). Camera options (CameraBob, ViewRoll, ReducedMotion) do NOT exist in IASettings on this base: leave a marked TODO row block and re-check after merge.
5. Main menu rework: rebuild pages on `GoTo` (no widget switcher), per-page width, scroll area + pinned footer, fade/slide transition (Tick), HOW TO PLAY page, map card (thumbnail, name, description, recommended players, prev/next), join validation (`IASettings::ValidateJoinAddress`) and last-5 recent chips, host COPY ADDRESS (`FPlatformApplicationMisc::ClipboardCopy`), Quit confirmation, FocusFirst on every page, Esc handling through `FIAModal::Cancel`.
6. Pause menu: same settings panel (`InMatch`), note "key changes apply from the next match", tall panel with margins.
7. `SIAWelcome` first-run overlay + "Reset tutorial".
8. Loading screen: `IALoadingScreen.*` with `FCoreUObjectDelegates::PreLoadMapWithContext` and `GetMoviePlayer()->SetupLoadingScreen`, registered from the module (`InstagibArena.cpp`), 12 tips, thumbnail via `FDeferredCleanupSlateBrush`, call `IASettings::ApplyStartupSettings` on `FCoreDelegates::OnPostEngineInit`.
9. Thumbnails: `-IAShotAuto` in `IADevSubsystem` (bounds of static mesh actors, overview camera, line trace for indoor maps, hide HUD and pawn, log PlayerStart count), `Tools/make_thumbnails.ps1` (parse `IAMapList.h`, run the game per map under `exclusive.ps1`, copy PNGs to `Tools/MapThumbs`), `Tools/import_thumbnails.py` (import to `/Game/UI/MapThumbs/T_<MapName>`), add `/Game/UI` to `DirectoriesToAlwaysCook` in `Config/DefaultGame.ini`.
10. Dev helpers: `-IAMenuScript` (page, tab, key, rebind, apply), `-IAFirstRun`, `-IALoadingPreview`, `-IAPauseTab`. Then screenshots at 1280x720, 1920x1080, 2560x1080 and UI scales 0.8-1.5, and a headless Quick Play check.

## Notes
- Heredocs are blocked in this environment; use the Write/Edit tools.
- Build helper script lives in the session scratchpad (build.ps1); recreate from DEVELOPMENT.md section 3, run through `Tools\exclusive.ps1`.
- Exact next step: build, fix compile errors in IAMenuStyle.cpp, commit, then continue with item 1 above.
