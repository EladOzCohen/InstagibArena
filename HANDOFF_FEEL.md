# FEEL engineer handoff

Branch: `worktree-agent-a95c2ed04ef78f716` (based on main a3fa032).

## Compile state
Last full successful build included everything except 4 tiny edits made afterwards (a build was killed at the interruption):
`IAAnimInstance.cpp` (`bGrounded = !IsFalling()`), `IADevSubsystem.cpp` (`SetDefaultMovementMode()` for showroom pawns),
`IADevSubsystem.h` (comment only), `Tools/make_decal_assets.py` (removed a protected property). Expect it to compile; rebuild first.

## Done and verified (run in game)
- Movement (IACharacterMovement): crouch (hold, capsule 60, speed 300), slow walk (320, FLAG_Custom_3), double jump (86%, 0.1 s delay), dodge (800/280, cooldown 0.4, landing lockout), wall dodge with 9 traces, hard-landing slowdown, replay-safe saved-move state. Keys Crouch (Left Ctrl) / Walk (Left Shift) in the IAInput table, wired in `AIAPlayerController::BuildInput` and the character.
- Camera (AIAPlayerCharacter::UpdateCamera): smooth eye height (crouch, stairs), bob, strafe/dodge roll, landing dip, fire punch, dodge FOV kick. Settings `IsCameraBobEnabled/IsViewRollEnabled/IsReducedMotion` (+Set...) added exactly as the coordinator specified. NOT yet looked at on screen (first-person camera effects unverified visually).
- Movement test `-IAMoveTest` host+client (Foundry): jump 169 cm, double jump 291 cm, wall dodge works, crouch/walk speeds right. `p.NetShowCorrections 1`: 0 corrections on client and server with 4 bots, no LogNet warnings. Positive control (forced adjustments) printed 368/135 correction lines, so the counting works. Logs were in the session scratchpad (feel_mp2_*.log, feel_mpctl_*.log).
- Headless bot matches 68 s: DM-Temple 8 bots 102 frags, DM-Skyline 10 bots 154 frags, no errors, avg 2.8 ms/frame (headless: animation does not tick, so animation cost is NOT measured by this).
- Animation (IAAnimInstance.*): native anim instance, no AnimBP; screenshots `Saved/IAShots/feel_b1.png` show rifle poses, aim up/down per pitch, rifle in the right hand (rotation (-2,155,20), offset (2,-3.5,6.3) from `Tools/probe_rifle.py`). 
- Ragdoll with impulse (replicated DeathShotDir/DeathHitLocation, hit bone, CCD, damping, PhysicsOnly collision, sparks and removal at 3.6 s): `feel_b3.png` shows a corpse lying on the floor. Impulse direction not examined closely.

## Found, fix is written but not yet seen working
- Showroom pawns had MovementMode None (nobody possesses them), so my animation showed the air pose for all of them (b1-b4 screenshots show tucked legs; that is the showroom artefact, not the game). Fix: animation treats "not falling" as grounded + showroom calls `SetDefaultMovementMode()`. Check with `feel_c1`-style shot below that jog, crouch (pawn on screen-left) and jump (second pawn) look right; tune `JogFootDown/WalkFootDown` tables in IAAnimInstance.cpp if the legs cross when blending directions, and the crouch pose time (0.17 s of Fall_Land).

## Half done / not started
- Scorch decals: `IAScorch.h/.cpp` (UTickableWorldSubsystem, pool 30, hot glow cooling) and the call in `MulticastShotEffect` build; the material `/Game/Materials/M_Scorch` is NOT generated yet (python script had an error, now fixed): run `Tools/make_decal_assets.py` (look for DECALASSET_DONE), then view with `-IAFireEvery=2 -IAShotDelay=15`. Without the material nothing is drawn (no error).
- Not done: 10-bot windowed frame-time check (`-IAReport` prints `FRAMES` lines), all 15 looks check (`-IAShowroom=...,180 -IAShowroomWalk -IAShowroomFrom=0/5/10`), packaged Shipping check, camera look, final host+client run with the final build, the HUD/other branches merge.

## Next steps in order
1. Build. Run `Tools/make_decal_assets.py`. 2. Shots: showroom walk (cam `-IAShotCam=-300,-1750,150,-4,0`, `-IAShowroom=0,-1750,100,180 -IAShowroomWalk -IAShowroomJump -IAShowroomCrouch`), fire at wall, FromA 0/5/10, 10 bots windowed with `-IAReport`. 3. Fix what is seen. 4. Rerun `-IAMoveTest` host+client. 5. Final report.

## Tools (flags documented in IADevSubsystem.h)
`-IAMoveTest[-Quit]`, `-IAShowroomWalk/Jump/Crouch`, `-IARifleOffset=...`, `FRAMES` lines with `-IAReport`; `Tools/probe_anim.py`, `probe_anim2.py`, `probe_rifle.py`, `make_decal_assets.py`.
Scratch scripts (build/shot/mp/bots) are in the session scratchpad, not the repo; the scratchpad is shared between agents, name your scripts uniquely.
