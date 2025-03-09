"""constants"""
from ..blender_files import BLEND_PATH

# custom property name
IS_MD_HARDSURF_PART_COLLECTION = 'is_md_hardsrf_part_collection'
NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION = 'nromal_transfer_src_obj_per_collection'
IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE = 'is_md_face_strength_material_override'

# modifier name
DNT_NORMAL_TRANSFER_NAME = "DNT_NORMAL"
DNT_BEVEL_NAME = "DNT_BEVEL"
DNT_WEIGHTED_NORMAL_NAME = "DNT_WEIGHTED_NORMAL"
MD_NORMAL_TRANSFER_NAME = "MD_NORMAL"


# collection name prefix
DNT_COLLECTION = "DNT"
NORMAL_COLLECTION = "NORMAL"
DESIGN_COLLECTION = "D"
FINAL_COLLECTION = "F"

# blender file path
FACE_STRENGTH_MATERIAL_BLEND_PATH = f"{BLEND_PATH}/face_strength_material.blend"

# face strength material override
FACE_STRENGTH_MAT_NAME = f"__MD_FaceStrength" # Node tree name, material name, node name uses the same.
FACE_STRENGTH_TEMP_OUTPUT_NODE = f"__MD_TempOutput" # material output node name.
