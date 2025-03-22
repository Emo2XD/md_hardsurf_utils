"""MD Project
This Gives Blender the concept of  'Current Working Directory'
"""


import bpy
from bpy.app.handlers import persistent
from pathlib import Path
from typing import List
from ..myblendrc_utils import utils as myu
from . import constants as ct
from ..prefs import get_preferences
import json
from ..setup_tools.register import register_other


def open_project(proj_root_dir:str):
    """Open MD Project Asset Folder
    This sets current working directory (CWD). But this do nothing. Just storing
    directory string value in .md_home. (and create history for recent project)

    After setting CWD info into .md_home, set as asset, use this CWD to use ctrlP file search, store harpoon history etc.
    """
    # setup_md_home_folder() # ensure having one.
    set_cwd(cwd=proj_root_dir)
    setup_project_folder(proj_root_dir=proj_root_dir, exists_ok=True)
    setup_md_proj_asset()
    set_current_project_to_wm()
    load_harpoon()
    print(f"Opened MD Project:'{proj_root_dir}'")
    return



def close_project():
    """Close MD Project Asset Folder."""
    save_harpoon() # save first
    set_cwd(cwd=None)
    unload_md_proj_asset()
    set_current_project_to_wm()
    print(f"Closed MD Project")
    return


# def setup_md_home_folder(cls, exists_ok:bool=True):
#     """In home directory, store following information
#     -Recent projects
#     -
#     """
#     md_home_dir_p = Path(get_cwd())
#     md_home_dir_p.mkdir(exist_ok=True)
#     pass


def get_cwd()->str:
    """Get CWD from .md_home
    Returns:
        absolute path in string form. or None.
    """
    d = read_home_info_dict()
    return d.get(ct.MD_PROJECT_CWD, None)


def set_cwd(cwd:str):
    """Write CWD to ~/.md_home/md_home_info.json"""
    d = read_home_info_dict()
    d[ct.MD_PROJECT_CWD] = cwd
    write_home_info_dict(d)


def read_home_info_dict()->dict:
    """Get MD Home Info Dictionary. If None generate default.
    Dictionary key:
        'md_project_cwd': Current working directory. if not set, None.
    """
    md_home_p = Path(get_md_home_folder_path())
    home_info_path = md_home_p/ct.MD_HOME_INFO_JSON
    home_info_dict = {}
    if home_info_path.exists():
        with open(str(home_info_path), 'r') as f:
            home_info_dict = json.load(f)
            pass
    else:
        # default setup
        home_info_dict[ct.MD_PROJECT_CWD] = None

    return home_info_dict


def write_home_info_dict(home_info_dict:dict):
    """Write MD HOME Info Dictionary. into ~/.md_files/md_home_info.json
    """
    md_home_p = Path(get_md_home_folder_path())
    md_home_p.mkdir(exist_ok=True) #ensure save location is there.
    home_info_path = md_home_p/ct.MD_HOME_INFO_JSON
    with open(str(home_info_path), 'w') as f:
        json.dump(home_info_dict, f)


def get_md_home_folder_path()->str:
    return str(Path(get_preferences().md_home_dir)/ct.MD_HOME_FOLDER_NAME)


def setup_project_folder(proj_root_dir:str, exists_ok:bool=True):
    """mkdir .md_project folder
    in .md_project folder, store following information
    - Harpoon file paths
    - Harpoon active file index
    """
    proj_root_dir_p = Path(proj_root_dir)
    (proj_root_dir_p/ct.MD_PROJECT_INFO_FOLDER_NAME).mkdir(exist_ok=True)


def setup_md_proj_asset():
    # ensure close every other md project asset
    asset_libs = bpy.context.preferences.filepaths.asset_libraries
    unload_md_proj_asset() # remove currently opened project.
    
    # ensure only one asset library per one path,
    # If specified proj_root_directory is already an asset, then skip new asset creation.
    # by nesting with Path and abspath, it ensures that each path is sharing the same format.
    cwd = get_cwd()

    for al in asset_libs:
        if Path(bpy.path.abspath(al.path)) == Path(bpy.path.abspath(cwd)):
            proj_lib = al
            break
    else:
        proj_lib = asset_libs.new(
            name=f"{ct.MD_PROJECT_ASSET_PREFIX}-{Path(cwd).name}", # somehow bpy.path.basename not work.
            directory=cwd
            )
        
    proj_lib.import_method = 'LINK'
    proj_lib.use_relative_path = True
    
    
    return


def unload_md_proj_asset():
    """Unload all md_proj_asset asset library which is generated by this addon.
    """
    asset_libs = bpy.context.preferences.filepaths.asset_libraries
    existing_md_proj_asset = [al for al in asset_libs if al.name.startswith(f"{ct.MD_PROJECT_ASSET_PREFIX}-")]
    for al in existing_md_proj_asset: # asset library (al)
        asset_libs.remove(al)
    
    return


def set_current_project_to_wm():
    """Set Current Project name to window manager property.
    This is used to visualize the name in the UI. If Project is not opened, then
    project name will be empty ''.
    """
    cwd = get_cwd()
    if cwd is not None:
        project_name = Path(cwd).name
    else:
        project_name = ''
    setattr(bpy.context.window_manager, ct.MD_PROJECT_CWD, project_name)


@persistent
def set_current_project_on_startup(dummy):
    """Set Current Project On Startup of Blender
    Args:
        load_post needs one paramter to work so dummy is needed
    """
    set_current_project_to_wm()
    load_harpoon()

def register_set_current_project_on_startup():
    bpy.app.handlers.load_post.append(set_current_project_on_startup)

def unregister_set_current_project_on_startup():
    if set_current_project_on_startup in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(set_current_project_on_startup)

register_other(
    register_func=register_set_current_project_on_startup, 
    unregister_func=unregister_set_current_project_on_startup)



#-------------------------------------------------------------------------------
# Harpoon
#-------------------------------------------------------------------------------
def harpoon_go_to_file_slot(index:int=0):
    wm = bpy.context.window_manager
    uilist = getattr(wm, ct.MD_HARPOON_UILIST_COLLECTION)
    setattr(wm, ct.MD_HARPOON_INDEX, index)
    save_harpoon()
    slot = None
    try:
        slot = uilist[index]
    except Exception as e:
        print(f"harpoon_go_to_file_slot: {e}")
        print(f"index: {index} not found in uilist")
        return

    if slot.filepath == bpy.data.filepath:
        print(f"harpoon tries to go to the same file path: abort")
        return
    elif slot.filepath == '':
        print(f"harpoon File path is empty: abort")
        return
    
    bpy.ops.wm.save_mainfile()
    try:
        bpy.ops.wm.open_mainfile(filepath=slot.filepath)
    except Exception as e:
        print(f"harpoon failed open file '{slot.filepath}': {e}")
        return 1
    return


def harpoon_add_file_slot(filepath:str=''):
    print(f"Harpoon Add File Slot: {filepath}")
    wm = bpy.context.window_manager
    uilist:bpy.types.CollectionProperty = getattr(wm, ct.MD_HARPOON_UILIST_COLLECTION)

    existing_file_paths = [Path(bpy.path.abspath(e.filepath)) for e in uilist]

    # don't create new slot if given file name has harpoon slot.
    if (filepath != '') and (Path(bpy.path.abspath(filepath)) in existing_file_paths):
        print(f"'{filepath}' already assigned")
        return
    
    slot = uilist.add()

    if filepath == '': # always create empty slot.
        slot.filepath = ''
        slot.name = 'Empty'
    else:
        slot.filepath = filepath
        slot.name = str(Path(filepath).relative_to(Path(get_cwd())))
        
    setattr(wm, ct.MD_HARPOON_INDEX, len(uilist)-1)
    save_harpoon()
    return

def harpoon_assign_to_slot(filepath:str=''):
    wm = bpy.context.window_manager
    uilist:bpy.types.CollectionProperty = getattr(wm, ct.MD_HARPOON_UILIST_COLLECTION)
    active_index = getattr(wm, ct.MD_HARPOON_INDEX)
    slot = uilist[active_index]

    if filepath == '': # always create empty slot.
        slot.filepath = ''
        slot.name = 'Empty'
    else:
        slot.filepath = filepath
        slot.name = str(Path(filepath).relative_to(Path(get_cwd())))
    
    save_harpoon()
    return 



def harpoon_remove_file_slot():
    """Remove Harpoon File Slot
    """
    print(f"Harpoon Remove File Slot")
    wm = bpy.context.window_manager
    uilist = getattr(wm, ct.MD_HARPOON_UILIST_COLLECTION)
    active_slot_index = getattr(wm, ct.MD_HARPOON_INDEX)
    uilist.remove(active_slot_index)
    new_index = max(min(len(uilist)-1, active_slot_index), 0)
    setattr(wm, ct.MD_HARPOON_INDEX, new_index)
    save_harpoon()
    return


def harpoon_move_file_slot(move_type:str='UP'):
    """Move Harpoon File Slot
    """
    wm = bpy.context.window_manager
    uilist = getattr(wm, ct.MD_HARPOON_UILIST_COLLECTION)
    active_slot_index = getattr(wm, ct.MD_HARPOON_INDEX)
    uilist_len = len(uilist)
    

    move_from = active_slot_index
    if move_type == 'UP':
        move_to = (active_slot_index - 1) % uilist_len
        
    elif move_type == 'DOWN':
        move_to = (active_slot_index + 1) % uilist_len
    else:
        print(f"WARNING: move_type must be 'UP' or 'DOWN', but {move_type} was given")
        return

    uilist.move(move_from, move_to)

    setattr(wm, ct.MD_HARPOON_INDEX, move_to)
    save_harpoon()
    return


def load_harpoon():
    """Load Harpoon Info from .md_project/md_harpoon_info.json
    Usually used in launch or opening of project.
    """
    harpoon_dict = read_harpoon_dict()
    harpoon_dict_to_wm(harpoon_dict)
    

def save_harpoon():
    """Save Harpoon Info to .md_project/md_harpoon_info.json
    usually used in change of harpoon uilist.
    """
    harpoon_dict = harpoon_wm_to_dict()
    write_harpoon_dict(harpoon_dict)



def harpoon_wm_to_dict()->dict:
    """Convert Harpoon Window Manager property into dictionary.
    """
    wm:bpy.types.WindowManager = bpy.context.window_manager
    harpoon_uilist:bpy.types.CollectionProperty = getattr(wm, ct.MD_HARPOON_UILIST_COLLECTION)
    harpoon_index:int = getattr(wm, ct.MD_HARPOON_INDEX)

    harpoon_dict = {}
    harpoon_dict[ct.MD_HARPOON_UILIST_COLLECTION] = [(i.name, i.filepath) for i in harpoon_uilist]
    harpoon_dict[ct.MD_HARPOON_INDEX] = harpoon_index

    return harpoon_dict


def harpoon_dict_to_wm(harpoon_dict:dict):
    """Convert Harpoon Dictionary into Window manager property
    """
    wm = bpy.context.window_manager
    setattr(wm, ct.MD_HARPOON_INDEX, harpoon_dict[ct.MD_HARPOON_INDEX])

    uilist:bpy.types.CollectionProperty = getattr(wm, ct.MD_HARPOON_UILIST_COLLECTION)

    # ensure uilist is empty
    for _ in range(len(uilist)):
        uilist.remove(0) # you have to remove index zero. Remove is similar to pop. UIList will be updated.

    for name, filepath in harpoon_dict[ct.MD_HARPOON_UILIST_COLLECTION]:
        slot = uilist.add()
        slot.name = name
        slot.filepath = filepath
    
    return


def write_harpoon_dict(harpoon_dict:dict):
    """Write Harpoon Dictionary to 
    """
    md_proj_p = Path(get_cwd())/ct.MD_PROJECT_INFO_FOLDER_NAME
    md_proj_p.mkdir(exist_ok=True) #ensure save location is there.
    harpoon_info_p = md_proj_p/ct.MD_HARPOON_INFO_JSON
    with open(str(harpoon_info_p), 'w') as f:
        json.dump(harpoon_dict, f, indent=4)


def read_harpoon_dict()->dict:
    md_proj_p = Path(get_cwd())/ct.MD_PROJECT_INFO_FOLDER_NAME
    harpoon_info_p = md_proj_p/ct.MD_HARPOON_INFO_JSON
    harpoon_dict = {}
    if harpoon_info_p.exists():
        with open(str(harpoon_info_p), 'r') as f:
            harpoon_dict = json.load(f)

    else:
        # default setup
        harpoon_dict[ct.MD_HARPOON_INDEX] = 0
        harpoon_dict[ct.MD_HARPOON_UILIST_COLLECTION] = []

    return harpoon_dict
