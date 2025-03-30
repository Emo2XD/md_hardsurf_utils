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
from .navigation import Navigation
from ..myblendrc_utils.common_constants import DataAttrNameDict, DataS
from . import utils as ut

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
    bpy.ops.wm.save_userpref()

    set_current_project_to_wm()
    load_harpoon()
    print(f"Opened MD Project:'{proj_root_dir}'")
    return



def close_project():
    """Close MD Project Asset Folder."""
    save_harpoon() # save first
    set_cwd(cwd=None)
    unload_md_proj_asset()
    bpy.ops.wm.save_userpref()

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
    
    # ensure only one asset library per one path,
    # If specified proj_root_directory is already an asset, then skip new asset creation.
    # by nesting with Path and abspath, it ensures that each path is sharing the same format.
    cwd = get_cwd()
    if cwd is None:
        print("Project is not Opened: abort setup_md_proj_asset")
        return
    # ensure close every other md project asset
    asset_libs = bpy.context.preferences.filepaths.asset_libraries
    unload_md_proj_asset() # remove currently opened project.

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
    
    if bpy.data.is_saved:
        bpy.ops.wm.save_mainfile()
    elif not bpy.data.is_saved and not bpy.data.is_dirty:
        pass
    else:
        print(f"harpoon: current file not saved in Disk abort")
        return 2
    
    Navigation.add_nav_history()
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
    cwd = get_cwd()
    if cwd is None: # if project is not opened do nothing.
        return

    md_proj_p = Path(cwd)/ct.MD_PROJECT_INFO_FOLDER_NAME
    md_proj_p.mkdir(exist_ok=True) #ensure save location is there.
    harpoon_info_p = md_proj_p/ct.MD_HARPOON_INFO_JSON
    with open(str(harpoon_info_p), 'w') as f:
        json.dump(harpoon_dict, f, indent=4)


def read_harpoon_dict()->dict:
    harpoon_dict = {
        ct.MD_HARPOON_INDEX: 0,
        ct.MD_HARPOON_UILIST_COLLECTION: []
    } # default

    cwd = get_cwd()
    if cwd is None:
        return harpoon_dict # return ndefault
    
    md_proj_p = Path(cwd)/ct.MD_PROJECT_INFO_FOLDER_NAME
    harpoon_info_p = md_proj_p/ct.MD_HARPOON_INFO_JSON
    if harpoon_info_p.exists():
        with open(str(harpoon_info_p), 'r') as f:
            harpoon_dict = json.load(f)


    return harpoon_dict


#-------------------------------------------------------------------------------
# File Search
#-------------------------------------------------------------------------------
def search_file_in_project_callback(self, context):
    """Callback function for project file search."""
    # wm = context.window_manager
    cwd = get_cwd()
    # print(f"!!!!!!!!!!!!!!!!{cwd}")
    enum_list = []
    id_path_list, disp_path_list = myu.gen_blend_file_path_and_display_name_list(search_path=cwd, exclude_prefix='.')

    for path, disp_name in zip( id_path_list, disp_path_list):
        enum_list.append((path, disp_name, ''))

    return enum_list


# Parts Link
def search_parts_in_project_callback(self, context):
    """Callback function for search parts in project.
    """
    cwd = get_cwd()
    enum_list = []
    id_path_list, disp_path_list = myu.gen_blend_file_path_and_display_name_list(search_path=cwd, exclude_prefix='.')


    for path, disp_name in zip( id_path_list, disp_path_list):
        with bpy.data.libraries.load(path, link=True)  as (data_from, data_to):
            collection_name_list = [name for name in data_from.collections if name.startswith("F-")]

        for c_name in collection_name_list:
            enum_list.append((
                f"{path}|collections|{c_name}", 
                f"{disp_name}:{c_name}",
                  ''))

    return enum_list


def link_part(id_path:str):
    """Link collection 'id_path' retrieved from search_parts_in_project_callback()
    """
    filepath, data_id, name = parse_link_id_path(id_path)
    col_to_link = None

    if Path(bpy.path.abspath(filepath)) == Path(bpy.path.abspath(bpy.data.filepath)):
        col_to_link = bpy.data.collections.get(name)
    else:
        col_to_link = myu.load_from_lib_and_return(filepath=filepath, attr_name=data_id, name=name, link=True, relative=True)
    
    if col_to_link is not None:
        new_part_obj = bpy.data.objects.new(name=col_to_link.name, object_data=None)
        bpy.context.collection.objects.link(new_part_obj)
        new_part_obj.instance_collection = col_to_link
        new_part_obj.empty_display_size  = 0.01
        new_part_obj.instance_type = 'COLLECTION'

        myu.select_only(new_part_obj)
        # bpy.context.collection.children.link(col_to_link)

    return
    


def parse_link_id_path(id_path:str):
    """Parse id_path from search_parts_in_project_callback.
    Example
        'abs/path/to/*.blend|data_id|name'
        -> ('abs/path/to/*.blend', 'data_id', 'name')
    """
    return tuple(id_path.split("|", 2))



#-------------------------------------------------------------------------------
# Rename Move File and Data and Sync Project
#-------------------------------------------------------------------------------
def rename_data_sync_project(data_id:bpy.types.ID, new_name:str):
    """Rename Data and Sync project
    """
    # data_ids = getattr(bpy.data, DataAttrNameDict.get(dtype))n
    id_type:str = data_id.id_type

    if new_name == data_id.name:
        print("rename_data_sync_project: given same name. Unchanged.")
        return 1
    elif ut.is_name_exists(id_type=id_type, new_name=new_name, only_local=True): # When duplicate name found.
        print("rename_data_sync_project: Name Collision. Unchanged.")
        return 2
    
    all_fpaths = myu.find_blend_files(search_path=get_cwd(), exclude_prefix=None)
    all_fpaths_exclude_current = [p for p in all_fpaths if not myu.is_same_path(p, bpy.data.filepath)]

    old_name = data_id.name
    data_id.name = new_name
    src_filepath = bpy.data.filepath
    
    bpy.ops.wm.save_mainfile()
    for p in all_fpaths_exclude_current:
        bpy.ops.wm.open_mainfile(filepath=p)
        renamed_linked_data_and_remap(src_path=src_filepath, id_type=id_type, old_name=old_name, new_name=new_name)
        bpy.ops.wm.save_as_mainfile()

    bpy.ops.wm.open_mainfile(filepath=src_filepath)
    return


def renamed_linked_data_and_remap(src_path:str, id_type:str, old_name:str, new_name:str):
    """Rename Linked Data in file.
    """
    if Path(bpy.path.abspath(src_path)) not in [Path(bpy.path.abspath(lib.filepath)).resolve() for lib in bpy.data.libraries[:]]:
        print(f"'{bpy.data.filepath}' does not use library '{src_path}'")
        return

    data_s = getattr(DataS, id_type)
    data_ids:List[bpy.types.ID] = getattr(bpy.data, data_s.data_name)

    new_id = myu.load_from_lib_and_return(filepath=src_path, attr_name=data_s.data_name, name=new_name, link=True, relative=True)

    old_id:bpy.types.ID = None

    # get old data id
    for id in data_ids:
        if id.name != old_name:
            continue
        if id.library is None:
            continue
        if not myu.is_same_path(id.library.filepath, src_path):
            continue
        else:
            old_id = id
            break
    else:
        print(f"'{bpy.data.filepath}' does not use {data_s.type_name} '{old_name}'")
        return

    old_id.user_remap(new_id=new_id)
    data_ids.remove(old_id)
    return



def move_data_sync_project(data_id:bpy.types.ID, filepath:str):
    if not is_dst_filepath_valid_for_move(filepath):
        print(f"Given filepath is not valid for move. '{filepath}'")
        return 1
    
    print("WIP: move_data_sync_project run.")
    pass    
                
def move_linked_data_and_remap(src_path:str, id_type:str, old_name:str, new_name:str):
    pass

def rename_file_sync_project(src_path:str, dst_path:str):
    """Rename File and Sync Project
    """
    src_pathlib = Path(bpy.path.abspath(src_path)).resolve()

    if not is_dst_filepath_valid_for_rename(dst_filepath=dst_path):
        return 1

    bpy.ops.wm.save_mainfile() # Update .blend1. This will be a backup of src_pathlib.unlink().

    all_fpaths = myu.find_blend_files(search_path=get_cwd(), exclude_prefix=None)
    all_other_fpaths = [
        p for p in all_fpaths 
        if not (myu.is_same_path(p, src_path) or (myu.is_same_path(p, dst_path)))
    ]

    bpy.ops.wm.save_as_mainfile(filepath=dst_path)
    
    for p in all_other_fpaths:
        bpy.ops.wm.open_mainfile(filepath=p)
        change_linked_library_filepath(old_p=src_path, new_p=dst_path)
        bpy.ops.wm.save_as_mainfile()
    
    bpy.ops.wm.open_mainfile(filepath=dst_path)
    src_pathlib.unlink()
    return


def change_linked_library_filepath(old_p:str, new_p:str):
    """Change linked library filepath
    """
    for lib in bpy.data.libraries:
        if myu.is_same_path(old_p, lib.filepath):
            lib.filepath = bpy.path.relpath(new_p)
            lib.name = bpy.path.basename(new_p)
        else:
            continue

    return

def is_dst_filepath_valid_for_rename(dst_filepath:str, ensure_inside_project:bool=True, suppress_log:bool=False)->bool:
    """Check if dst_filepath is valid for rename.
    Empty dst_filepath, 
    """
    dst_pathlib = Path(bpy.path.abspath(dst_filepath)).resolve()
    if not dst_pathlib.parent.exists: # upper directory not found
        if not suppress_log: print("upper directory not found")
        return False
    if dst_pathlib.exists(): # given filepath is already taken
        if not suppress_log: print("given filepath is already taken")
        return False
    if dst_filepath == '' or dst_filepath is None: # invalid filepath
        if not suppress_log: print("Enpty filepath is given")
        return False
    
    if ensure_inside_project:
        project_root = str(Path(get_cwd()).resolve())
        if not str(dst_filepath).startswith(project_root):
            if not suppress_log: print("Outside of project folder.")
            return False
        else:
            return True
    else:
        return True

def is_dst_filepath_valid_for_move(dst_filepath:str)->bool:
    """Check if the destination filepath is valid for move.

    If dst_filepath is not exist or same with current, then return False
    """
    return Path(bpy.path.abspath(dst_filepath)).exists() and not myu.is_same_path(dst_filepath, bpy.data.filepath)
    

def update_data_holder_to(self, context):
    """callback for data_holder to"""
    wm = context.window_manager
    update_data_holder_collection(
        filepath=self.map_to_filepath, 
        data_type=DataAttrNameDict.get(self.data_type),
        data_holder=getattr(wm, ct.MD_REMAP_HOLDER_TO)
        )
    
def update_data_holder_from(self, context):
    """callback for data_holder to"""
    wm = context.window_manager
    update_data_holder_collection(
        filepath=self.map_from_filepath, 
        data_type=DataAttrNameDict.get(self.data_type),
        data_holder=getattr(wm, ct.MD_REMAP_HOLDER_FROM)
        )

def update_data_holder_data_type(self, context):
    """callback for remap data_type"""
    update_data_holder_from(self, context)
    update_data_holder_to(self, context)

def update_data_holder_collection(filepath:str, data_type:str, data_holder:bpy.types.CollectionProperty):
    """Update data holder collection.
    This will be used in remap data feature.
    """
    data_names = []
    if filepath == None or filepath == '' or data_type=='' or data_type==None:
        return data_names

    if myu.is_same_path(filepath, bpy.data.filepath):
        data_names = [d.name for d in getattr(bpy.data, data_type)]
    else:
        with bpy.data.libraries.load(filepath=filepath, link=True) as (data_from, data_to):
            data_names = [name for name in getattr(data_from, data_type)]


    for _ in range(len(data_holder)):
        data_holder.remove(0)
    
    for n in data_names:
        d = data_holder.add()
        d.name = n
    
    return



def remap_data_sync_project(
        data_type:str, 
        map_from_filepath:str, 
        map_to_filepath:str,
        map_from_data_name:str,
        map_to_data_name:str,
        exclude_f:bool,
        exclude_t:bool
        ):
    """Remap Data Sync Project.

    Args:
        data_type: Such that 'Collection', 'Object', etc.
        map_from_filepath: search data on this filepath 
        map_to_filepath: remap to data to this filepath
        map_from_data_name: Search data with this name
        map_to_data_name: Remap to data with this name
        exclude_f: If True, exclude search and remap operation on map_from_filepath blend file.
        exclude_t: If True, exclude search and remap operation on map_to_filepath blend file.
    """
    if not is_valid_argument_remap_data_sync_project(
        data_type=data_type, 
        map_from_filepath=map_from_filepath, 
        map_to_filepath=map_to_filepath,
        map_from_data_name=map_from_data_name,
        map_to_data_name=map_to_data_name):
        return 1

    data_name:str = DataAttrNameDict.get(data_type)
    current_filepath = bpy.data.filepath
    bpy.ops.wm.save_mainfile()
    
    all_fpaths = myu.find_blend_files(search_path=get_cwd(), exclude_prefix=None)
    all_other_fpaths = [
        p for p in all_fpaths 
        if not (myu.is_same_path(p, map_from_filepath) or (myu.is_same_path(p, map_from_filepath)))
    ]

    if not exclude_f:
        all_other_fpaths.append(map_from_filepath)
    if not exclude_t:
        all_other_fpaths.append(map_to_filepath)


    for p in all_other_fpaths:
        bpy.ops.wm.open_mainfile(filepath=p)
        remap_data(
            data_type=data_type, 
            map_from_filepath=map_from_filepath, 
            map_to_filepath=map_to_filepath,
            map_from_data_name=map_from_data_name,
            map_to_data_name=map_to_data_name
        )
        bpy.ops.wm.save_as_mainfile()



    bpy.ops.wm.open_mainfile(filepath=current_filepath)
    return


def remap_data(
        data_type:str, 
        map_from_filepath:str, 
        map_to_filepath:str,
        map_from_data_name:str,
        map_to_data_name:str
        ):
    data_name:str = DataAttrNameDict.get(data_type)
    is_current_file_map_from = myu.is_same_path(bpy.data.filepath, map_from_filepath)
    is_current_file_map_to = myu.is_same_path(bpy.data.filepath, map_to_filepath)

    # you have to exclude map_from_filepath because map_from_filepath itself uses corresponding data without library.
    if is_current_file_map_from:
        pass
    elif not is_filepath_in_libraries(map_from_filepath):
        print(f"'{bpy.data.filepath}' does not use library '{map_from_filepath}'")
        return
    
    #---------
    # Find 'map_from_data' in file. 'If branch' is used for current file == map_from_filepath
    #---------
    map_from_id:bpy.types.ID = None
    data_ids = getattr(bpy.data, data_name)
    if map_from_data_name not in data_ids:
        print(f"'{map_from_data_name}' not in '{map_from_filepath}'")
        return
    
    data_with_same_name:List[bpy.types.ID] = [d for d in data_ids if d.name == map_from_data_name]
    if not is_current_file_map_from:
        for d in data_with_same_name:
            if d.library is None:
                continue
            if myu.is_same_path(d.library.filepath, map_from_filepath):
                map_from_id = d
                break
        else:
            print(f"'{map_from_data_name}' is not used in '{bpy.data.filepath}'.")
            return
    else: # when bpy.data.filepath == map_from_filepath
        for d in data_with_same_name:
            if d.library is None:
                map_from_id = d
                break
        else:
            print(f"'{map_from_data_name}' is not used in '{bpy.data.filepath}'.")
            return
        
    #---------------
    # Find map_to_id.  'If branch' is used for current file == map_to_filepath
    #---------------
    map_to_id:bpy.types.ID = None
    if is_current_file_map_to: # when trying to update dependency on 'map_to' blend file.
        for d in data_ids:
            if d.name == map_to_data_name and d.library is None: # local data with name 'map_to_data_name'
                map_to_id = d
                break
    else:
        map_to_id = myu.load_from_lib_and_return(filepath=map_to_filepath, attr_name=data_name, name=map_to_data_name, link=True, relative=True)

    #---------------
    # remap.
    #---------------
    map_from_id.user_remap(new_id=map_to_id)

    if is_current_file_map_from: # ensure not to loss data. If modifying file 'map_from' itself
        map_from_id.use_fake_user = True
    return


def is_filepath_in_libraries(filepath:str):
    """Check if filepath exists in bpy.data.libraries.

    Args: 
        filepath: absolute path in string form usually bpy.data.filepath
    """
    return Path(bpy.path.abspath(filepath)) in [Path(bpy.path.abspath(lib.filepath)).resolve() for lib in bpy.data.libraries[:]]


def is_valid_argument_remap_data_sync_project(        
        data_type:str, 
        map_from_filepath:str, 
        map_to_filepath:str,
        map_from_data_name:str,
        map_to_data_name:str):
    
    if data_type == '' or data_type is None:
        print('data_type is invalid')
        return False
    if (not map_from_filepath.endswith('.blend')) or map_from_filepath == '' or map_from_filepath == None or (not Path(map_from_filepath).resolve().exists()):
        print('map_from_filepath is invalid.')
        return False
    if (not map_to_filepath.endswith('.blend')) or map_to_filepath == '' or map_to_filepath == None or (not Path(map_to_filepath).resolve().exists()):
        print('map_to_filepath is invalid')
        return False
    if map_from_data_name == '' or map_from_data_name is None:
        print('map_from_data_name is invalid')
        return False
    if map_to_data_name == '' or map_to_data_name is None:
        print('map_to_data_name is invalid')
        return False
    
    return True



#-------------------------------------------------------------------------------
# Rename part collection
#-------------------------------------------------------------------------------
def rename_part_collection(part_collection:bpy.types.Collection, new_name:str)->int:
    """Rename currently selected part col
    """
    current_name = part_collection.name

    # F-Part collection is designed to be shared among other files. It has to be synced inside project.
    # so treat separately
    f_collection = ut.PartManager.get_mk_reserved_collection_from_part(
                        part_collection=part_collection,
                        prefix=ct.FINAL_COLLECTION,
                        create=False
                        )
    
    # Check name existance. Avoid unintentional name change like foo.001.
    local_col_name_list = [c.name for c in bpy.data.collections if c.library is None]
    if f"{ct.FINAL_COLLECTION}-{new_name}" in local_col_name_list and (f_collection is not None):
        print("Given name is already taken.")
        return 1

    if new_name == current_name:
        print("Given name is same with the current one.")
        return 1
    elif not new_name:
        print("Given name is empty")
        return 1
    elif new_name.isspace():
        print("Given name only contains space")
        return 1


    part_collection.name = new_name
    # use different algorithm for final collection.
    reserved_collection = ut.PartManager.get_collections(part_collection=part_collection)
    for col in reserved_collection:
        if col.name.startswith(f"{ct.FINAL_COLLECTION}-"):
            continue
        col.name = f"{col.name.split('-', 1)[0]}-{new_name}"

    if f_collection is not None:
        rename_data_sync_project(data_id=f_collection, new_name=f"{ct.FINAL_COLLECTION}-{new_name}")

    print("rename part is called")
    return