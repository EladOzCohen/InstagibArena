# FEEL engineer handoff (work in progress)

Branch: `worktree-agent-a95c2ed04ef78f716` (fast-forwarded to main a3fa032, the shared base, before any work).

## State of the build
**DOES NOT COMPILE right now.** `Source/InstagibArena/IACharacterMovement.h` was rewritten (new members, `DoJump`,
`GetMaxSpeed`, `FindWall`, walk flag, landing info) but `IACharacterMovement.cpp` is still the OLD file, so
`DoJump`, `GetMaxSpeed` and `FindWall` are declared but not defined. Next step 1 fixes this. No other source file was touched.
(The baseline build of the untouched base succeeded in this worktree before the header edit.)

## Done and verified
- Worktree set up: `Tools/restore_mannequins.ps1` now also copies `Anims/Rifle` (run once, 99 files). Mannequins live in `Content/Characters/Mannequins` (git-ignored).
- Baseline build (editor, Development) succeeded.
- Animation asset probe (`Tools/probe_anim.py`, run with `-ExecutePythonScript` in the editor commandlet, output lines start with `PROBE`). Facts:
  - Rifle jog/walk clips: `MF_Rifle_Jog_Fwd` 1.533 s (46 frames), `Jog_Bwd` 1.8 s, `Jog_Left` 0.467 s (very short), `Jog_Fwd_Left` 1.533 s; `Walk_Fwd` 1.533 s, `Walk_Bwd` 1.2 s.
    Lengths differ per direction, so check sync before blending with a shared normalized phase.
  - All MF_* clips have root motion enabled and force_root_lock=True (no drift when extracted without root motion).
    Root travel per clip, in cm/s: Jog_Fwd 934/1.533 = about 610, Jog_Bwd 1044/1.8 = about 580, Jog_Left 256/0.467 = about 549, Walk_Fwd 456/1.533 = about 298, Walk_Bwd 350/1.2 = about 292. Use these as clip speeds for play-rate scaling.
  - `MF_Rifle_Idle_ADS` is an 8 s pose loop (not additive). The aim clips `MM_Rifle_Idle_ADS_AO_CC/CD/CU` are 1 frame, additive (rotation offset, mesh space), base = a frame of MF_Rifle_Idle_ADS. There are no left/right aim clips (pitch only). `AO_Rifle` is an AimOffsetBlendSpace whose samples cannot be read through python properties.
  - Jump set: Jump_Start 0.233 s, Start_Loop 2 s, Apex 0.667 s, Fall_Loop 3 s (rate_scale 2), Fall_Land 0.4 s, RecoveryAdditive (additive, local space).
  - No crouch animations exist. Idea: freeze a frame of `MM_Rifle_Jump_Fall_Land` (deep knee bend) as the crouch pose.
  - Death clips exist (`Death/MM_Death_*`) but the plan is ragdoll from the live pose.

## Half done
- `IACharacterMovement.h` (new API, see the comments in the file). Planned .cpp content, in order of importance:
  1. Saved move stores and restores `CooldownRemaining`, `bWallDodgedThisJump`, `bWantsToWalk` (SetMoveFor/PrepMoveFor); walk uses `FLAG_Custom_3` in the compressed flags.
  2. `GetMaxSpeed`: slow walk (320) only on ground. Crouch: `NavAgentProps.bCanCrouch=true`, `CrouchedHalfHeight=60`, `MaxWalkSpeedCrouched=300`, `bCrouchMaintainsBaseLocation=true`.
  3. `DoJump`: air jump sets Z to `JumpZVelocity*DoubleJumpScale` (not max), rejected within `DoubleJumpDelay` of the first jump (`TimeSinceJump`).
  4. Wall dodge via `FindWall`: several line traces (3 heights x 3 angles) in the dodge direction, accept near-vertical walls (|N.Z|<0.3) facing the player, push away along the normal and keep about 60% of the tangential speed.
  5. `ProcessLanded`: store `LastLandingSpeed/Time` (before calling Super, Velocity.Z is still the fall speed); speed penalty (x0.8) above `HardLandingSpeed`; dodge landing lockout.
  6. Tuning: PerchRadiusThreshold 10, AirControl about 0.45. Ground values (MaxWalkSpeed 600, accel 2600, friction 8, braking 2400) were kept; tweak only after the movement test.

## Not started
- Crouch and Walk keys: append `Crouch` (Left Ctrl) and `Walk` (Left Shift) to the table in `IAInputConfig.cpp`; wire in `AIAPlayerController::BuildInput` (new actions) and bind in `AIAPlayerCharacter::SetupPlayerInputComponent` (Crouch()/UnCrouch(), SetWantsToWalk).
- Camera: smooth eye height and step smoothing (relative Z of `FirstPersonCamera`), head bob, strafe/dodge roll, landing dip, fire punch, dodge FOV kick via `UCameraComponent::AddAdditiveOffset`. Settings (append block in IASettings): `CameraBob` (bool, on), `ViewRoll` (bool, on), `ReducedMotion` (bool, off; turns all of it off).
- Animation: plan = `UIAAnimInstance` (native class, no AnimBP) with an `FAnimInstanceProxy` subclass overriding `Evaluate`; extract poses from the UAnimSequences with `GetAnimationPose`; blend 8 directions (Fwd, FwdR, R, BwdR, Bwd, BwdL, L, FwdL) by angle; idle/walk/jog by speed; play rate = speed / clip speed; jump/fall/land states; pitch aim by accumulating the additive AO_CU/AO_CD poses (convert to mesh-space rotation first); frozen crouch pose. Attach the existing box rifle to `hand_r` instead of `spine_05` (see `BuildWeapon` in IAPlayerCharacter.cpp, tune the offset with the showroom). Everything loaded by path must stay under `/Game/Characters` (already cooked).
- Ragdoll: replicate the death impulse (direction + hit location, set before `bDead`), `AddImpulseAtLocation` on `FindClosestBone`, damping, `PhysicsOnly` collision (shots do not hit corpses), shrink out before `SetLifeSpan`. Optional scorch decals.
- Dev helpers in `IADevSubsystem`: scripted movement test (jump, double jump, dodge left/right, wall dodge, crouch) that logs positions; showroom walk helper (`bRunPhysicsWithNoController=true` is needed for controller-less pawns).
- host+client test with net correction count, 10-bot performance check, all 15 looks check, packaged-build check.

## Notes
- `docs/DEVELOPMENT.md` and `Tools/exclusive.ps1` come from main (a3fa032). Heavy jobs go through `Tools\exclusive.ps1 -Command "..."`.
- Build: `Build.bat InstagibArenaEditor Win64 Development -Project=<proj>\InstagibArena.uproject -WaitMutex -NoHotReload`.
- Shared append-only files (IASettings, IAInputConfig.cpp table) will conflict at the end of the file on merge; keep both blocks.
- Nothing from this branch has been run in game yet; there are no screenshots.
