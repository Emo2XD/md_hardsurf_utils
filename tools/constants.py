"""constants"""
from ..blender_files import BLEND_PATH

# custom property name
IS_MD_HARDSURF_PART_COLLECTION = 'is_md_hardsrf_part_collection'
NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION = 'nromal_transfer_src_obj_per_collection'
IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE = 'is_md_face_strength_material_override'
IS_DNT_NORMAL_OBJECT = 'is_dnt_normal_object'
OPEN_PART_COLLECTION_PLACEHOLDER = 'open_part_collection_place_holder' # this is needed because property pointer cannot be added to operator its self. Used in show only part operator.
IS_MD_HARDSURF_SUB_PART_COLLECTION = 'is_md_hardsrf_sub_part_collection'

# UIList custom property name
SCENE_COLLECTION_CHILD_INDEX = 'scene_collection_child_index'
ACTIVE_PART_COLLECTION = "active_part_collection" # read only property to keep track of active part collection.
ACTIVE_UILIST_COLLECTION = "active_uilist_collection"

TEMP_VISIBILITY = 'temp_visibility' # use for tracking visibility since there is no attribute.

# RESERVED_PART_COLLECTION_VISIBILITY = "reserved_part_collection_visibility"


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
DEP_COLLECTION = "DEP" # other dependency file needed for final render.

# blender file path
FACE_STRENGTH_MATERIAL_BLEND_PATH = f"{BLEND_PATH}/face_strength_material.blend"

# face strength material override
FACE_STRENGTH_MAT_NAME = f"__MD_FaceStrength" # Node tree name, material name, node name uses the same.
FACE_STRENGTH_TEMP_OUTPUT_NODE = f"__MD_TempOutput" # material output node name.


# MD Project System Constants
MD_HOME_FOLDER_NAME = '.md_files' # default: ~/.md_files/
MD_PROJECT_INFO_FOLDER_NAME = '.md_project' # stored in CWD root directory, ./.md_project/
MD_PROJECT_ASSET_PREFIX = '_MD_PROJ' # used as asset name._MD_PROJ-{asset_folder_name}
MD_HOME_INFO_JSON = 'md_home_info.json' # stored as  ~/.md_files/md_home_info.json
MD_PROJECT_CWD = 'md_project_cwd' # dictionary key in md_home_info.json and window manager property.

# HARPOON
MD_HARPOON_INDEX = 'md_harpoon_index'
MD_HARPOON_UILIST_COLLECTION = 'md_harpoon_ui_list_collection'
MD_HARPOON_INFO_JSON = 'md_harpoon_info.json' # store to project_root/.md_project/md_harpoon_info.json