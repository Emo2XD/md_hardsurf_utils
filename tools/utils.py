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


    if ct.DNT_NORMAL_TRANSFER_NAME not in modifier_names:
        mod_dnt_nromal = obj.modifiers.new(name=ct.DNT_NORMAL_TRANSFER_NAME, type="DATA_TRANSFER")
        mod_dnt_nromal.use_pin_to_last = True

        mod_dnt_nromal.use_object_transform = False
        mod_dnt_nromal.use_loop_data = True
        mod_dnt_nromal.data_types_loops = {'CUSTOM_NORMAL'}
        mod_dnt_nromal.loop_mapping = 'POLYINTERP_NEAREST'

    else:
        mod_dnt_nromal = obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME)

    if ct.DNT_BEVEL_NAME not in modifier_names:
        mod_dnt_bevel = obj.modifiers.new(name=ct.DNT_BEVEL_NAME, type="BEVEL")
        mod_dnt_bevel.use_pin_to_last = True

        mod_dnt_bevel.limit_method = 'WEIGHT'
        mod_dnt_bevel.loop_slide = False
        mod_dnt_bevel.use_clamp_overlap = False

    else:
        mod_dnt_bevel = obj.modifiers.get(ct.DNT_BEVEL_NAME)



    # Generate collection to store generated DNT normal source object.
    part_collection = get_parent_part_collection(obj)
    if part_collection is None:
        part_collection = context.scene.collection # use as fallback

    dnt_collection = get_mk_collection(name=f"{ct.DNT_COLLECTION}-{part_collection.name}", parent=part_collection)
    dnt_collection.hide_render = True
    dnt_collection.hide_viewport = True
    dnt_collection.color_tag = 'COLOR_05'



    # create normal transfer source object.

    # remove previously created DNT normal source object
    normal_ref_obj_name = f"{ct.DNT_NORMAL_TRANSFER_NAME}-{obj.name}"
    prev_normal_ref_obj = bpy.data.objects.get(normal_ref_obj_name) 
    if prev_normal_ref_obj is not None:
        bpy.data.objects.remove(prev_normal_ref_obj)

    normal_ref_obj = obj.copy()
    normal_ref_obj.name = normal_ref_obj_name
    normal_ref_obj.modifiers.remove(normal_ref_obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME))
    normal_ref_obj.modifiers.remove(normal_ref_obj.modifiers.get(ct.DNT_BEVEL_NAME))
    dnt_collection.objects.link(normal_ref_obj)


    # setup data transfer modifier rerference object
    mod_dnt_nromal.object = normal_ref_obj
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


    
def get_parent_part_collection(obj:bpy.types.Object)->bpy.types.Collection:
    """Get parent hard surface modeling part collection
    This searches which part collection does given object belong to.
    
    Args:
        obj: check if part collection contains this object

    Return:
        collection which has IS_MD_HARDSURF_PART_COLLECTION == True property, and it contains given object.
    """
    md_hard_surface_part_collections = [c for c in bpy.data.collections if getattr(c, ct.IS_MD_HARDSURF_PART_COLLECTION) == True]

    for c in md_hard_surface_part_collections:
        if obj in myu.get_objects_in_collection(c, recursive=True):
            return c
        else:
            continue

    return None
