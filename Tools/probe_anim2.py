"""Finds the stride cycle of the rifle walk and jog clips (frames where the left/right foot is lowest).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript=Tools/probe_anim2.py -unattended -nullrhi -nosplash
Output lines start with CYCLE.
"""
import unreal

base = "/Game/Characters/Mannequins/Anims/Rifle/"
dirs = ["Fwd", "Fwd_Right", "Right", "Bwd_Right", "Bwd", "Bwd_Left", "Left", "Fwd_Left"]

def minima(values):
    out = []
    n = len(values)
    for i in range(1, n - 1):
        if values[i] <= values[i - 1] and values[i] < values[i + 1]:
            out.append(i)
    return out

for gait in ("Jog", "Walk"):
    for d in dirs:
        name = "%s%s/MF_Rifle_%s_%s" % (base, gait, gait, d)
        a = unreal.EditorAssetLibrary.load_asset(name)
        if a is None:
            unreal.log("CYCLE missing " + name)
            continue
        n = unreal.AnimationLibrary.get_num_frames(a)
        length = a.get_editor_property("sequence_length")
        rootend = unreal.AnimationLibrary.get_bone_pose_for_frame(a, "root", n - 1, True).translation
        res = {}
        for foot in ("foot_l", "foot_r"):
            zs = []
            for f in range(n):
                side = foot[-1]
                chain = [foot, "calf_" + side, "thigh_" + side, "pelvis"]
                tr = None
                for b in chain:
                    lt = unreal.AnimationLibrary.get_bone_pose_for_frame(a, b, f, False)
                    tr = lt if tr is None else tr.multiply(lt)
                t = tr.translation
                # translation in bone-parent space, so use the mesh-space height through the pelvis-less pose: approximate with y/z mix
                zs.append(t.z)
            res[foot] = minima(zs)
        unreal.log("CYCLE %s %s frames=%d len=%.3f root=(%.0f,%.0f) footL_min=%s footR_min=%s" % (gait, d, n, length, rootend.x, rootend.y, res["foot_l"], res["foot_r"]))
