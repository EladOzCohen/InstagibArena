import unreal
base = "/Game/Characters/Mannequins/Anims/"
names = ["Rifle/Jog/MF_Rifle_Jog_Fwd","Rifle/Jog/MF_Rifle_Jog_Bwd","Rifle/Jog/MF_Rifle_Jog_Left","Rifle/Jog/MF_Rifle_Jog_Fwd_Left","Rifle/Walk/MF_Rifle_Walk_Fwd","Rifle/Walk/MF_Rifle_Walk_Bwd","Rifle/MF_Rifle_Idle_ADS",
 "Rifle/Jump/MM_Rifle_Jump_Start","Rifle/Jump/MM_Rifle_Jump_Apex","Rifle/Jump/MM_Rifle_Jump_Fall_Loop","Rifle/Jump/MM_Rifle_Jump_Fall_Land","Rifle/Jump/MM_Rifle_Jump_Start_Loop","Rifle/Jump/MM_Rifle_Jump_RecoveryAdditive",
 "Rifle/AIM/MM_Rifle_Idle_ADS_AO_CC","Rifle/AIM/MM_Rifle_Idle_ADS_AO_CD","Rifle/AIM/MM_Rifle_Idle_ADS_AO_CU","Rifle/MM_Rifle_Fire","Rifle/MM_Rifle_Equip","Unarmed/MM_Idle","Unarmed/Jump/MM_Dash","Unarmed/Jump/MM_Land","Unarmed/Jog/MF_Unarmed_Jog_Fwd","Death/MM_Death_Back_01"]
for n in names:
    a = unreal.EditorAssetLibrary.load_asset(base + n)
    if a is None:
        unreal.log("PROBE missing " + n); continue
    s = ""
    try:
        s += " len=%.3f" % a.get_editor_property("sequence_length")
    except Exception as e:
        s += " lenerr"
    for p in ("enable_root_motion","force_root_lock","root_motion_root_lock","rate_scale","additive_anim_type","ref_pose_type","ref_pose_seq","loop"):
        try:
            s += " %s=%s" % (p, a.get_editor_property(p))
        except Exception as e:
            pass
    try:
        s += " cls=%s" % a.get_class().get_name()
        s += " nframes=%d" % unreal.AnimationLibrary.get_num_frames(a)
    except Exception as e:
        s += " err"
    unreal.log("PROBE %s %s" % (n, s))
ao = unreal.EditorAssetLibrary.load_asset(base + "Rifle/AIM/AO_Rifle")
unreal.log("PROBE AO %s" % ao.get_class().get_name())
for p in ("blend_parameters","sample_data","target_weight_interpolation_speed_per_sec"):
    try: unreal.log("PROBE AO %s=%s" % (p, ao.get_editor_property(p)))
    except Exception as e: unreal.log("PROBE AO noprop %s" % p)
print([m for m in dir(ao) if not m.startswith('_')][:80])
# measure root speed of jog/walk
sk = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Meshes/SK_Mannequin")
for n in ["Rifle/Jog/MF_Rifle_Jog_Fwd","Rifle/Jog/MF_Rifle_Jog_Bwd","Rifle/Jog/MF_Rifle_Jog_Left","Rifle/Walk/MF_Rifle_Walk_Fwd","Rifle/Walk/MF_Rifle_Walk_Left","Rifle/Walk/MF_Rifle_Walk_Bwd"]:
    a = unreal.EditorAssetLibrary.load_asset(base + n)
    nf = unreal.AnimationLibrary.get_num_frames(a)
    for bone in ("root","pelvis"):
        try:
            t0 = unreal.AnimationLibrary.get_bone_pose_for_frame(a, bone, 0, True)
            t1 = unreal.AnimationLibrary.get_bone_pose_for_frame(a, bone, nf-1, True)
            unreal.log("PROBE move %s %s %s -> %s" % (n, bone, t0.translation, t1.translation))
        except Exception as e:
            unreal.log("PROBE move err %s %s %s" % (n, bone, e))
