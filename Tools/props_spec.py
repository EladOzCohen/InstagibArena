"""What to import from the downloaded Poly Haven models, and how. Plain Python (no unreal import).

Used by fetch_models.py (which slugs to download), import_props.py (how to import each model) and props.py
(the catalogue the map scripts use).

One JOB = one import of one glTF file (possibly only some of its nodes) that yields one or more static meshes:

    J(slug, category, kind, name, nodes=None, mode='combine', coll='box', tags=(), ...)

  slug      Poly Haven asset name (folder in the model cache, see fetch_models.py)
  category  folder below /Game/Props (Industrial, Lighting, Marine, Temple, Rocks, Trees, Plants)
  kind      free word used to look things up: barrel, crate, barrier, fence, pipe, machine, lamp, vehicle, rock, ...
  name      catalogue name. mode='combine' -> one mesh called `name`; mode='separate' -> one mesh per node called
            name_a, name_b ... (the nodes in the order given)
  nodes     glTF node names to import (None = all). Nodes of a combined mesh keep their offsets relative to each
            other; separate nodes are moved to the origin so that each mesh is centred on its own pivot.
  coll      collision: 'box', 'convex:N' (N hulls), 'trunk:R' (a vertical capsule of radius R cm at the pivot),
            'none'
  scale     default scale used when this entry is placed (catalogue 'scale')
  sizes     extra size classes for rocks etc.: {'_s': 0.5, '_l': 2.0} adds catalogue entries name_s, name_l
  tex       texture size in pixels (256, 512 or 1024); None = automatic from the object's size (small things get 256)
  nanite    True / False to force it; None = automatic (dense meshes without glass become Nanite)
  solid     False = decoration without collision by default
  tags      the maps it suits (foundry temple dock skyline neon forge glacier canyon)
"""

ALL = ("foundry", "temple", "dock", "skyline", "neon", "forge", "glacier", "canyon")


class Job(dict):
    pass


JOBS = []


def J(slug, category, kind, name, nodes=None, mode="combine", coll="box", tags=(), scale=1.0, sizes=None,
      nanite=None, solid=True, keep_pivot=False, tex=None):
    JOBS.append(Job(slug=slug, category=category, kind=kind, name=name, nodes=nodes, mode=mode, coll=coll,
                    tags=list(tags), scale=scale, sizes=sizes or {}, nanite=nanite, solid=solid,
                    keep_pivot=keep_pivot, tex=tex))


# ------------------------------------------------------------------ industrial yard, steelworks, harbour, city
I = "Industrial"
J("Barrel_01", I, "barrel", "barrel_red", coll="convex:1", tags=("foundry", "forge", "dock", "neon", "canyon"))
J("Barrel_02", I, "barrel", "barrel_plastic", coll="convex:1", tags=("foundry", "dock", "neon", "skyline"))
J("barrel_stove", I, "barrel", "barrel_fire", coll="convex:1", tags=("neon", "glacier", "foundry"))
J("wooden_barrels_01", I, "barrel", "barrel_wood", nodes=["wooden_barrels_01_barrel01", "wooden_barrels_01_barrel02"],
  mode="separate", coll="convex:1", tags=("dock", "canyon", "glacier", "temple"))
J("wine_barrel_01", I, "barrel", "barrel_wine",
  nodes=["wine_barrel_01", "wine_barrel_01_Lid", "wine_barrel_01_bung", "wine_barrel_01_base"], coll="convex:1",
  tags=("temple", "canyon", "dock"))
J("concrete_road_barrier", I, "barrier", "barrier_a", tags=("foundry", "forge", "neon", "dock", "skyline"))
J("concrete_road_barrier_02", I, "barrier", "barrier_b", tags=("foundry", "forge", "neon", "dock", "skyline"))
J("modular_chainlink_fence", I, "fence", "fence",
  nodes=["modular_chainlink_fence", "modular_chainlink_fence_double"],
  mode="separate", tags=("foundry", "dock", "neon", "skyline", "glacier"))
J("modular_industrial_pipes_01", I, "pipe", "pipe", nodes=["modular_industrial_pipes_01_pipe01", "modular_industrial_pipes_01_pipe02", "modular_industrial_pipes_01_pipe03", "modular_industrial_pipes_01_pipe05", "modular_industrial_pipes_01_pipe07"], mode="separate", tags=("foundry", "forge", "skyline", "neon"))
J("modular_airduct_circular_01", I, "duct", "duct",
  nodes=["modular_airduct_circular_triple", "modular_airduct_circular_double", "modular_airduct_circular_bend_half",
         "modular_airduct_circular_fan"],
  mode="separate", tags=("skyline", "foundry", "neon", "forge"))
J("exterior_aircon_unit", I, "machine", "aircon_a", nodes=["exterior_aircon_unit"],
  mode="combine", tags=("skyline", "neon"))
J("utility_box_01", I, "machine", "utility_box_a", tags=("neon", "skyline", "foundry"))
J("fire_hydrant", I, "street", "hydrant_a",
  nodes=["fire_hydrant", "fire_hydrant_cap_01", "fire_hydrant_cap_02", "fire_hydrant_cap_03", "fire_hydrant_chain"],
  coll="convex:1", tags=("neon", "skyline", "foundry"))
J("covered_car", I, "vehicle", "car_covered", keep_pivot=True, tags=("neon", "foundry", "dock", "skyline"))
J("portable_generator", I, "machine", "generator", tags=("foundry", "forge", "dock", "glacier"))
J("propane_tank", I, "tank", "propane_tank", coll="convex:1", tags=("foundry", "forge", "glacier", "neon"))
J("metal_jerrycan", I, "tank", "jerrycan", tags=("foundry", "dock", "glacier", "canyon", "forge"))
J("metal_trash_can", I, "bin", "bin_a", nodes=["metal_trash_can"], mode="combine",
  coll="convex:1", tags=("neon", "skyline", "dock"))
J("wooden_crate_01", I, "crate", "crate_wood_a", tags=("foundry", "dock", "canyon", "glacier", "forge"))
J("wooden_crate_02", I, "crate", "crate_wood_b", nodes=["wooden_crate_02_crate"],
  tags=("foundry", "dock", "canyon", "glacier", "forge"))
J("old_tyre", I, "junk", "tyre", coll="convex:1", tags=("foundry", "neon", "canyon", "dock", "forge"))
J("large_iron_gate", I, "gate", "gate_iron", tags=("foundry", "neon", "temple", "forge"))
J("rollershutter_door", I, "gate", "shutter_door", nodes=["rollershutter_door"], tags=("neon", "foundry", "dock"))
J("overhead_crane", I, "crane", "crane_gantry", nodes=["overhead_crane", "overhead_crane_winch"], keep_pivot=True,
  coll="none", solid=False, tags=("dock", "foundry", "forge"))
J("modular_fire_escape", I, "structure", "fire_escape",
  nodes=["modular_fire_escape_stairs", "modular_fire_escape_platform_middle", "modular_fire_escape_ladder_bottom"],
  mode="separate", tags=("neon", "skyline"))

# ------------------------------------------------------------------ lamps
L = "Lighting"
J("street_lamp_01", L, "lamp", "lamp_street_a", coll="trunk:10", tags=("neon", "skyline", "dock", "foundry"))
J("street_lamp_02", L, "lamp", "lamp_street_b", coll="trunk:10", tags=("neon", "skyline", "dock", "foundry"))
J("security_light", L, "lamp", "lamp_security", coll="none", solid=False, tags=("neon", "foundry", "dock", "skyline"))
J("hanging_industrial_lamp", L, "lamp", "lamp_hanging", coll="none", solid=False, tags=("foundry", "forge", "dock"))
J("wooden_lantern_01", L, "lamp", "lantern", coll="none", solid=False, tags=("temple", "canyon", "dock"))

# ------------------------------------------------------------------ harbour
M = "Marine"
J("ocean_buoy", M, "marine", "buoy", coll="convex:1", tags=("dock",))
J("lateral_sea_marker", M, "marine", "sea_marker", coll="convex:1", tags=("dock",))
J("modular_wooden_pier", M, "structure", "pier",
  nodes=["modular_wooden_pier_section_01", "modular_wooden_pier_section_02"],
  mode="separate", tags=("dock",))

# ------------------------------------------------------------------ temple
T = "Temple"
J("gothic_statue", T, "statue", "statue_gothic", tags=("temple",))
J("marble_bust_01", T, "statue", "bust_marble", tags=("temple",))
J("antique_ceramic_vase_01", T, "vase", "vase_ceramic", coll="convex:1", tags=("temple", "canyon"))
J("brass_vase_01", T, "vase", "vase_brass", coll="convex:1", tags=("temple",))
J("stone_fire_pit", T, "brazier", "fire_pit", coll="convex:1", tags=("temple", "canyon", "glacier"))
J("rock_moss_set_01", T, "rock", "rock_moss_big",
  nodes=["rock_moss_set_01_rock01", "rock_moss_set_01_rock02", "rock_moss_set_01_rock04", "rock_moss_set_01_rock05"],
  mode="separate", coll="convex:3", tags=("temple",))
J("rock_moss_set_02", T, "rock", "rock_moss_small",
  nodes=["rock_moss_set_02_rock08", "rock_moss_set_02_rock12", "rock_moss_set_02_rock10"],
  mode="separate", coll="convex:2", tags=("temple",))

# ------------------------------------------------------------------ rocks (all maps)
R = "Rocks"
RK = dict(solid=True)
J("boulder_01", R, "rock", "rock_boulder", coll="convex:3", sizes={"_s": 0.5, "_l": 2.0},
  tags=("glacier", "temple", "forge", "canyon"))
J("rock_07", R, "rock", "rock_flat", coll="convex:1", scale=4.0, sizes={"_s": 0.5, "_l": 2.0}, tags=("glacier", "temple", "canyon"))
J("rock_face_01", R, "cliff", "cliff_a", coll="convex:4", tags=("glacier", "canyon", "temple"))
J("rock_face_02", R, "cliff", "cliff_b", coll="convex:4", tags=("glacier", "canyon", "temple"))
J("namaqualand_boulder_02", R, "rock", "rock_red_a", coll="convex:3", sizes={"_s": 0.5, "_l": 2.0},
  tags=("canyon", "forge"))
J("namaqualand_boulder_03", R, "rock", "rock_red_b", coll="convex:3", sizes={"_s": 0.5, "_l": 2.0},
  tags=("canyon", "forge"))
J("namaqualand_boulder_04", R, "rock", "rock_red_c", coll="convex:3", sizes={"_s": 0.5, "_l": 2.0},
  tags=("canyon", "forge"))
J("namaqualand_cliff_01", R, "cliff", "cliff_red_a", coll="convex:5", tags=("canyon", "forge"))
J("namaqualand_rocks_01", R, "rock", "rock_red_small", nodes=["namaqualand_rocks_02_a"],
  mode="combine", coll="convex:1", scale=4.0, sizes={"_s": 0.5, "_l": 2.0}, tags=("canyon",))

# ------------------------------------------------------------------ trees
TR = "Trees"
J("fir_sapling", TR, "tree", "fir", nodes=["fir_sapling_a"], mode="separate",
  coll="trunk:7", scale=4.0, tags=("glacier",))
J("dead_tree_trunk_02", TR, "tree", "trunk_dead_b", coll="convex:2", tags=("canyon", "glacier"))
J("dead_quiver_trunk", TR, "tree", "trunk_quiver", coll="convex:1", tags=("canyon",))
J("quiver_tree_02", TR, "tree", "tree_quiver_b", coll="trunk:12", tags=("canyon",))
J("tree_stump_01", TR, "stump", "stump_a", coll="convex:1", tags=("glacier", "canyon", "temple"))
# ------------------------------------------------------------------ plants (no collision)
P = "Plants"
J("anthurium_botany_01", P, "plant", "plant_anthurium", nodes=["anthurium_botany_01_a", "anthurium_botany_01_b"],
  mode="separate", coll="none", solid=False, tags=("temple",))
J("calathea_orbifolia_01", P, "plant", "plant_calathea", nodes=["calathea_orbifolia_01_a", "calathea_orbifolia_01_b"],
  mode="separate", coll="none", solid=False, tags=("temple",))
J("fern_02", P, "plant", "fern", nodes=["fern_02_b", "fern_02_c"], mode="separate", coll="none", solid=False,
  tags=("temple", "glacier"))
J("shrub_02", P, "plant", "shrub", nodes=["shrub_02_a", "shrub_02_c"], mode="separate", coll="none",
  solid=False, tags=("temple", "canyon"))
J("wild_rooibos_bush", P, "plant", "bush_dry", nodes=["wild_rooibos_bush_a", "wild_rooibos_bush_b"],
  mode="separate", coll="none", solid=False, scale=2.0, tags=("canyon",))


def slugs():
    out = []
    for j in JOBS:
        if j["slug"] not in out:
            out.append(j["slug"])
    return out
