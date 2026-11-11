# FEEL engineer handoff

Branch: `worktree-agent-a95c2ed04ef78f716`.

## State (second session)
Movement, crouch/walk keys, camera feel, camera settings, movement test and the rifle-pose animation (native `UIAAnimInstance`)
are written and build. Movement and the host+client test were run and verified (see below). Animation was run in the
showroom (first screenshot looked right: rifle poses, directions). Ragdoll code is written, build pending when this was saved.

## Verified
- Build green (editor Development).
- Host+client movement test (`-IAMoveTest`, Foundry, 0 bots): jump 169 cm, double jump 291 cm total, dodge L/R/F/B, crouch (capsule 60), crouch walk 300, slow walk 320, wall dodge (speed 553 -> 818 away from the wall). `p.NetShowCorrections 1` printed no corrections on client or server, no LogNet warnings (no positive control done yet).
- Showroom screenshot `Saved/IAShots/feel_a2.png`: characters hold the rifle, strafe/back/diagonal poses differ.

## Not verified yet
Rifle grip look (values from `Tools/probe_rifle.py`: rotation (-2,155,20), offset (2,-3.5,6.3)), crouch pose, jump/landing poses, aim pitch,
ragdoll, 10-bot performance, 15 looks, camera feel on screen, packaged build.

## Tools
- `-IAMoveTest [-IAMoveTestQuit]`, `-IAShowroomWalk [-IAShowroomCrouch]` (pawns walk on the spot in 8 directions, pitch -44..44), `-IARifleOffset=x,y,z,pitch,yaw,roll[,scale]` (rifle in hand, no rebuild).
- `Tools/probe_anim.py`, `probe_anim2.py` (stride cycles), `probe_rifle.py` (grip transform).
- Scratch scripts used for runs live in the session scratchpad (feel_build.ps1, feel_mp.ps1, feel_shot.ps1) - not in the repo.
