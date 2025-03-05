import bpy
import os
from pathlib import Path
from typing import List
from ..myblendrc_utils import utils as myu
from . import constants as ct



def sync_dnt():
    """Setup and sync DNT
    """
    context = bpy.context
    obj = context.active_object
        
    
    # TODO may be a better way
    orig_mode = obj.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    myu.select_only(obj)
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode=orig_mode)
    
    # Setup bevel and data transfer modifiers
    modifier_names = [m.name for m in obj.modifiers]

    if ct.DNT_WEIGHTED_NORMAL_NAME not in modifier_names:
        mod_w_norm = obj.modifiers.new(name=ct.DNT_WEIGHTED_NORMAL_NAME, type="WEIGHTED_NORMAL")
        mod_w_norm.mode = 'CORNER_ANGLE'
        mod_w_norm.keep_sharp = True
        mod_w_norm.use_face_influence = True
        mod_w_norm.show_in_editmode = True


    if ct.DNT_NORMAL_TRANSFER_NAME not in modifier_names:
        mod_dnt_nromal = obj.modifiers.new(name=ct.DNT_NORMAL_TRANSFER_NAME, type="DATA_TRANSFER")
        mod_dnt_nromal.use_pin_to_last = True

        mod_dnt_nromal.use_object_transform = False
        mod_dnt_nromal.use_loop_data = True
        mod_dnt_nromal.data_types_loops = {'CUSTOM_NORMAL'}
        mod_dnt_nromal.loop_mapping = 'POLYINTERP_NEAREST'
        mod_dnt_nromal.show_in_editmode = True

    else:
        mod_dnt_nromal = obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME)

    if ct.DNT_BEVEL_NAME not in modifier_names:
        mod_dnt_bevel = obj.modifiers.new(name=ct.DNT_BEVEL_NAME, type="BEVEL")
        mod_dnt_bevel.use_pin_to_last = True

        mod_dnt_bevel.limit_method = 'WEIGHT'
        mod_dnt_bevel.loop_slide = False
        mod_dnt_bevel.use_clamp_overlap = False
        mod_dnt_bevel.show_in_editmode = True

    else:
        mod_dnt_bevel = obj.modifiers.get(ct.DNT_BEVEL_NAME)


    # Generate collection to store generated DNT normal source object.
    dnt_collection = get_mk_reserved_collection_under_part(obj, ct.DNT_COLLECTION)
    dnt_collection.hide_render = True
    dnt_collection.hide_viewport = True
    dnt_collection.color_tag = 'COLOR_05'

    # remove previously created DNT normal source object
    prev_normal_ref_obj = obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME).object
    if prev_normal_ref_obj is not None:
        bpy.data.objects.remove(prev_normal_ref_obj)

    # create normal transfer source object.
    normal_ref_obj = obj.copy()
    normal_ref_obj.name = f"{ct.DNT_NORMAL_TRANSFER_NAME}-{obj.name}"
    normal_ref_obj.modifiers.remove(normal_ref_obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME))
    normal_ref_obj.modifiers.remove(normal_ref_obj.modifiers.get(ct.DNT_BEVEL_NAME))
    dnt_collection.objects.link(normal_ref_obj)


    # setup data transfer modifier rerference object
    mod_dnt_nromal.object = normal_ref_obj
    return


def regenerate_reserved_collection_under_part():
    """Regenerate reserved collection under part (when accidentally removed some of them)
    """
    part_collection = bpy.context.collection
    setup_reserved_part_collection(part_collection)
    return




def get_mk_collection(name:str, parent:bpy.types.Collection=None)->bpy.types.Collection:
    """Get collection and return. If not exists, create.
    Args:
        name: collection name
        parent: create under this parent collection
    """
    
    target_collection = bpy.data.collections.get(name)

    if target_collection is None:
        target_collection = bpy.data.collections.new(name)

        if parent == None:
            parent = bpy.context.scene.collection
        parent.children.link(target_collection)


    return target_collection


def get_mk_reserved_collection_under_part(obj:bpy.types.Object, prefix:str, create:bool=True)->bpy.types.Collection:
    """ Create or get reserved collection under part collection using prefix. (from given object) 
    Create: Just create using prefix. {prefix}-{part_name} e.g. NORMAL-{part.name} under part collection.
    Get: Get collection with specified prefix. Ignoring rest of the string.

    By specifying only prefix you don't have to worry about digit after collection name e.g. .001

    Args:
        obj: try to find parent part collection from this object
        prefix: Create or get collection, whose name starts with this prefix, under parent part collection.
        create: If False, suppress creation of new collection
    """
    part_collection = get_parent_part_collection(obj, fallback=bpy.context.scene.collection)

    # if already created, then return existing.
    for c in part_collection.children[:]:
        if c.name.startswith(f"{prefix}-"):
            return c
        else:
            continue

    # if there is no collection starts with prefix, then create new one.
    if create == True:
        new_collection = bpy.data.collections.new(name=f"{prefix}-{part_collection.name}")
        part_collection.children.link(new_collection)
        return new_collection
    else:
        return None



    
def get_parent_part_collection(obj:bpy.types.Object, fallback:bpy.types.Collection=None)->bpy.types.Collection:
    """Get parent hard surface modeling part collection
    This searches which part collection does given object belong to.
    
    Args:
        obj: check if part collection contains this object
        fallback: if there is no valid part collection found, then use this as fallback collection.

    Return:
        collection which has IS_MD_HARDSURF_PART_COLLECTION == True property, and it contains given object.
    """
    md_hard_surface_part_collections = [c for c in bpy.data.collections if getattr(c, ct.IS_MD_HARDSURF_PART_COLLECTION) == True]

    for c in md_hard_surface_part_collections:
        if obj in myu.get_objects_in_collection(c, recursive=True):
            return c
        else:
            continue

    return fallback


def setup_part_collection(part_name:str="Part"):
    """Setup Part Collection
    Create collections
    - F-Part: final cleaned up model will be stored
    - Design-Part: design and draft models will be stored
    - Normal-Part: Normal transfer reference objects will be stored
    - DNT-Part: DNT generated object will be stored
    """
    part_collection = bpy.data.collections.new(name=part_name)
    setattr(part_collection, ct.IS_MD_HARDSURF_PART_COLLECTION, True)
    bpy.context.scene.collection.children.link(part_collection)
    
    setup_reserved_part_collection(part_collection)
    print(f"given name is {part_name}, and {part_collection.name} was created")

    return

def setup_reserved_part_collection(part_collection:bpy.types.Collection):
    """Create Final-, Design-, Normal- collection under given part_collection
    """
    # you have to use get_mk_collection because you do not have object inside part collection at this point.
    final_collection  = get_mk_collection(name=f"{ct.FINAL_COLLECTION}-{part_collection.name}", parent=part_collection)
    design_collection = get_mk_collection(name=f"{ct.DESIGN_COLLECTION}-{part_collection.name}", parent=part_collection)
    normal_collection = get_mk_collection(name=f"{ct.NORMAL_COLLECTION}-{part_collection.name}", parent=part_collection) # needs to be generated because you need this before do normal transfer to put source object in it

    normal_collection.color_tag = 'COLOR_05'
    normal_collection.hide_render = True
    design_collection.color_tag = 'COLOR_06'
    design_collection.hide_render = True
    return