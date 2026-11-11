"""Works out how a rifle must sit in hand_r so that it fits the rifle poses of the Mannequin animations:
the barrel points from the right hand to the left hand, and the rifle's up axis follows the character's up.
Prints the rotation and location to put into TPRifleHandRotation / TPRifleHandOffset (IAPlayerCharacter.cpp).

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript=Tools/probe_rifle.py -unattended -nullrhi -nosplash
Output lines start with RIFLE.
"""
import unreal

lib = unreal.AnimationLibrary
math = unreal.MathLibrary
base = "/Game/Characters/Mannequins/Anims/Rifle/"
clips = [("MF_Rifle_Idle_ADS", [0, 60, 120]), ("Jog/MF_Rifle_Jog_Fwd", [0, 10, 20]), ("Walk/MF_Rifle_Walk_Fwd", [0, 12])]

right_chain = ["pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"]
left_chain = ["pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l"]


def component_space(anim, chain, frame):
    comp = None
    for bone in chain:
        local = lib.get_bone_pose_for_frame(anim, bone, frame, False)
        comp = local if comp is None else local.multiply(comp)
    return comp


for name, frames in clips:
    anim = unreal.EditorAssetLibrary.load_asset(base + name)
    for f in frames:
        r = component_space(anim, right_chain, f)
        l = component_space(anim, left_chain, f)
        forward = (l.translation - r.translation)
        forward.normalize()
        # axes expressed in the space of hand_r
        x_axis = math.inverse_transform_direction(r, forward)
        z_axis = math.inverse_transform_direction(r, unreal.Vector(0, 0, 1))
        rot = math.make_rot_from_xz(x_axis, z_axis)
        grip = unreal.Vector(4.0 * 0.85, 0.0, -8.0 * 0.85)  # the grip of the rifle model, scaled like the rifle
        rotated = math.transform_direction(unreal.Transform(unreal.Vector(0, 0, 0), rot, unreal.Vector(1, 1, 1)), grip)
        unreal.log("RIFLE %s frame %d  hand_r=(%.1f,%.1f,%.1f) hand_l=(%.1f,%.1f,%.1f) dist=%.1f  rot(P,Y,R)=(%.1f,%.1f,%.1f)  offset=(%.1f,%.1f,%.1f)" % (
            name, f, r.translation.x, r.translation.y, r.translation.z, l.translation.x, l.translation.y, l.translation.z,
            (l.translation - r.translation).length(), rot.pitch, rot.yaw, rot.roll, -rotated.x, -rotated.y, -rotated.z))
