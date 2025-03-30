import bpy
import bmesh
import os
from pathlib import Path
from typing import List
from ..myblendrc_utils import utils as myu
from ..myblendrc_utils import common_constants as cct
from . import constants as ct
from ..prefs import get_preferences
import numpy as np
from ..myblendrc_utils.common_constants import DataS


#-------------------------------------------------------------------------------
# Normal Transfer
#-------------------------------------------------------------------------------
def normal_transfer(target_obj:bpy.types.Object, normal_src_obj:bpy.types.Object):
    """Setup normal transfer from object.
    if normal_src_obj is None, then selected vertices will be removed from other normal transfer vertex groups
    """

    selected_v_indices = get_selected_vertex_indices_bmesh(target_obj)
    if len(selected_v_indices) == 0:
        print("No vertex is selected.")
        return 1

    remove_from_normal_transfer(target_obj, selected_v_indices)

    if normal_src_obj is None: # early out, just remove from exixsting normal transfer modifier.
        return

    # Setup Normal Transfer Modifier, reuse existing normal transfer if found.
    existing_normal_transfer_mods = [m for m in target_obj.modifiers if m.name.startswith(f"{ct.MD_NORMAL_TRANSFER_NAME}-")]
    for m in existing_normal_transfer_mods:
        if m.object == normal_src_obj:
            normal_transfer_mod = m
            break
    else:
        normal_transfer_mod = target_obj.modifiers.new(name=f"{ct.MD_NORMAL_TRANSFER_NAME}-{normal_src_obj.name}", type='DATA_TRANSFER')
        normal_transfer_mod.use_object_transform = False
        normal_transfer_mod.use_loop_data = True
        normal_transfer_mod.data_types_loops = {'CUSTOM_NORMAL'}
        normal_transfer_mod.loop_mapping = 'POLYINTERP_NEAREST'
        normal_transfer_mod.show_in_editmode = True
        normal_transfer_mod.object = normal_src_obj


    # Get vertex group and set as Normal transfer modifier vertex group.
    normal_transfer_vg_name = normal_transfer_mod.vertex_group # this is string property.
    if normal_transfer_vg_name == '':
        vg_name = f"{ct.MD_NORMAL_TRANSFER_NAME}-{normal_src_obj.name}"
        normal_transfer_vg = get_or_create_vertex_group(target_obj, vg_name)
        normal_transfer_mod.vertex_group = normal_transfer_vg.name # you should use generated name to handle digit like .001
    else:
        normal_transfer_vg = target_obj.vertex_groups.get(normal_transfer_vg_name)
    


    # Assign to vertex group
    bpy.ops.object.mode_set(mode='OBJECT')
    normal_transfer_vg.add(selected_v_indices, 1.0, 'REPLACE')
    bpy.ops.object.mode_set(mode='EDIT')


    # sync DNT if there is corresponding modifiers
    modifiers_name_list = [m.name for m in target_obj.modifiers]
    if (ct.DNT_NORMAL_TRANSFER_NAME in modifiers_name_list) or (ct.DNT_BEVEL_NAME in modifiers_name_list):
        sync_dnt()

    return


def get_or_create_vertex_group(obj:bpy.types.Object, name:str)->bpy.types.VertexGroup:
    """Get vertex group, if not found, then create new one.
    """
    vg = obj.vertex_groups.get(name)
    if vg is not None:
        return vg
    else:
        vg = obj.vertex_groups.new(name=name)
        return vg



def get_selected_vertex_indices_bmesh(obj:bpy.types.Object):
    """
    Returns a list of indices of selected vertices using bmesh. More efficient for large meshes.
    Returns an empty list if no mesh object is active or no vertices are selected.
    """
    if obj and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data) if bpy.context.object.mode == 'EDIT' else bmesh.new()

        if bpy.context.object.mode == 'OBJECT':
           bm.from_mesh(obj.data)

        selected_vertices = [v.index for v in bm.verts if v.select]

        if bpy.context.object.mode == 'OBJECT':
            bm.free() #free bmesh when mode is object.

        return selected_vertices
    else:
        return []
    

def get_selected_edge_indices_bmesh(obj:bpy.types.Object):
    """
    Returns a list of indices of selected edges using bmesh. More efficient for large meshes.
    Returns an empty list if no mesh object is active or no edges are selected.
    """
    if obj and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data) if bpy.context.object.mode == 'EDIT' else bmesh.new()

        if bpy.context.object.mode == 'OBJECT':
           bm.from_mesh(obj.data)

        selected_edges = [e.index for e in bm.edges if e.select]

        if bpy.context.object.mode == 'OBJECT':
            bm.free() #free bmesh when mode is object.

        return selected_edges
    else:
        return []


def poll_is_obj_in_part_collection(self, obj):
    """Poll function to filter object, only show when active object exist."""
    active_part_col = getattr(bpy.context.scene, ct.ACTIVE_PART_COLLECTION)
    # active_obj = bpy.context.active_object
    # if active_obj is None:
        # return False
    if active_part_col is None:
        return False
    
    # normal_collection = get_mk_reserved_collection_under_part(obj=active_obj, prefix=ct.NORMAL_COLLECTION, create=False)
    normal_collection = PartManager.get_mk_reserved_collection_from_part(part_collection=active_part_col, prefix=ct.NORMAL_COLLECTION, create=False)
    if normal_collection == None:
        return False
    else:
        return obj.type == 'MESH' and (obj in normal_collection.all_objects[:]) 



def poll_is_part_collection(self, col):
    """Poll function to filter collection, only show part collection
    """
    return getattr(col, ct.IS_MD_HARDSURF_PART_COLLECTION)



def remove_from_normal_transfer(obj:bpy.types.Object, v_indices:List[int]):
    """Remove from Normal Transfer Vertex Group
    This works only for normal tranfer generated by this addon 
    Selected vertex_group will be removed from normal transfer modifier vertex group.

    Args:
        obj: Target object. Whose vertices will be modified.
        v_indices: These vertices will be removed from normal transfer modifier vertex group.
    """

    existing_normal_transfer_mods = [m for m in obj.modifiers if m.name.startswith(f"{ct.MD_NORMAL_TRANSFER_NAME}-")]
    # All vertex groups which are used in normal transfer
    all_normal_transfer_vgs = []
    for m in existing_normal_transfer_mods:
        vg_name = m.vertex_group
        if vg_name != '':
            all_normal_transfer_vgs.append(vg_name)

    bpy.ops.object.mode_set(mode='OBJECT')
    for vg_name in all_normal_transfer_vgs:
        vg = obj.vertex_groups.get(vg_name)
        vg.remove(v_indices)
    
    bpy.ops.object.mode_set(mode='EDIT')

    return

#-------------------------------------------------------------------------------
# Separate As Normal Transfer
#-------------------------------------------------------------------------------
def separate_as_normal_source_object(name:str, assign_as_src:bool=True, shade_smooth:bool=True):
    """Separate as normal source object. Then you can use separated object in normal transfer.
    if there is DNT bevel and normal transfer modifier, then it will be removed.
    """
    active_obj = bpy.context.active_object
    if len(get_selected_vertex_indices_bmesh(active_obj)) == 0:
        print("No vertex is selected.")
        return 1
    
    # part_collection = get_parent_part_collection(obj=active_obj)
    part_collection = getattr(bpy.context.scene, ct.ACTIVE_PART_COLLECTION)

    # Separate
    object_set_before = set(bpy.context.selected_objects)
    if shade_smooth:
        bpy.ops.mesh.faces_shade_smooth() # Automatic shade smooth.
    bpy.ops.mesh.separate(type='SELECTED')
    object_set_after = set(bpy.context.selected_objects)

    separated_objects = list(object_set_after - object_set_before) # might be multiple object is separated. the last one will be used.

    # Set as normal transfer source object.
    if len(separated_objects) == 1 and assign_as_src == True:
        setattr(part_collection, ct.NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION, separated_objects[0])

    # normal_collection = get_mk_reserved_collection_under_part(active_obj, ct.NORMAL_COLLECTION)
    normal_collection = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.NORMAL_COLLECTION)
    for obj in separated_objects:
        obj.name = name
        clean_up_dnt_modifiers(obj)
        remove_normal_transfer_modifiers(obj)
        for col in  obj.users_collection:
            col.objects.unlink(obj)
        normal_collection.objects.link(obj)
        
    return


def remove_normal_transfer_modifiers(obj:bpy.types.Object):
    """Remove normal transfer modifiers from given object (remove only generated through this Addon.)
    """
    normal_transfer_modifiers:List[bpy.types.Object] = [m for m in obj.modifiers if m.name.startswith(f"{ct.MD_NORMAL_TRANSFER_NAME}-")]
    for m in normal_transfer_modifiers:
        obj.modifiers.remove(m)
    return


#-------------------------------------------------------------------------------
# Set bevel weight
#-------------------------------------------------------------------------------
def set_edge_bevel_weight_with_sharp(weight:float, modify_sharp:bool=True):
    """Set edge bevel weight with preset and shapr option for convenience

    Args:
        weight: edge_bevel_weight
        modify_sharp: If True, it automatically mark as sharp on bevel weight > 0, clear sharp from bevel weight == 0
    """
    obj = bpy.context.active_object

    mesh = obj.data

    # get edge bevel weight attribute
    edge_bevel_weight_attribute = mesh.attributes.get('bevel_weight_edge')
    if edge_bevel_weight_attribute is None:
        edge_bevel_weight_attribute = mesh.attributes.new(name="bevel_weight_edge", type="FLOAT", domain="EDGE")
    
    orig_attr = mesh.attributes.active
    mesh.attributes.active = edge_bevel_weight_attribute
    bpy.ops.mesh.attribute_set(value_float=weight)

    if modify_sharp and weight > 0.0:
        bpy.ops.mesh.mark_sharp()
    elif modify_sharp and weight == 0.0:
        bpy.ops.mesh.mark_sharp(clear=True)

    mesh.attributes.active = orig_attr
    return


#-------------------------------------------------------------------------------
# Set Modifier Bevel Width
#-------------------------------------------------------------------------------
def set_dnt_bevel_modifier_width(modifier_width:float, keep_visual_width:bool, orig_width:float):
    """Set DNT bevel modifier width with keep visual width option.
    Args:
        modifier_width: This value is set as bevel modifier 'Amount' paramete.
        keep_visual_width: If true, it tries to keep visual width of the bevel.
        orig_width: This is necessary in edit mode. It stores original modifier width through out 'Adjust last operation'.
    """
    obj = bpy.context.active_object
    mesh = obj.data
    orig_mode = obj.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    dnt_bevel_mod = obj.modifiers.get(ct.DNT_BEVEL_NAME)
    old_width = orig_width

    if keep_visual_width == True and modifier_width > 0.0: # zero division guard
        # get edge bevel weight attribute
        edge_bevel_weight_attribute = mesh.attributes.get('bevel_weight_edge')
        if edge_bevel_weight_attribute is None:
            edge_bevel_weight_attribute = mesh.attributes.new(name="bevel_weight_edge", type="FLOAT", domain="EDGE")

        edge_bevel_weights = np.full(len(obj.data.edges), 0.0)
        edge_bevel_weight_attribute.data.foreach_get("value", edge_bevel_weights)
        edge_bevel_weights = old_width/modifier_width * edge_bevel_weights
        edge_bevel_weight_attribute.data.foreach_set("value", edge_bevel_weights)
        
    dnt_bevel_mod.width = modifier_width

    bpy.ops.object.mode_set(mode=orig_mode)

    return


#-------------------------------------------------------------------------------
# Toggle DNT Visibility
#-------------------------------------------------------------------------------

def toggle_dnt_visibility(obj:bpy.types.Object):
    """Toggle DNT modifier visibility.
    Specifics:
    -Only when all the DNT modifiers are visible, then hides all DNT modifiers.
    -If one or more DNT modifiers are hidden, then shows all DNT modifiers.
    """
    mod_dnt_bevel = obj.modifiers.get(ct.DNT_BEVEL_NAME)
    mod_dnt_nromal = obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME)

    # by using list, it is easy to manage toggle at once
    mods_to_toggle:List[bpy.types.Modifier] = [m for m in [mod_dnt_bevel, mod_dnt_nromal] if m is not None]

    if len(mods_to_toggle) == 0:
        print("No DNT modifiers to toggle")
        return 1
    
    is_visible_all = True
    for m in mods_to_toggle:
        is_visible_all &= m.show_viewport

    if is_visible_all:
        for m in mods_to_toggle:
            m.show_viewport = False
    else:
        for m in mods_to_toggle:
            m.show_viewport = True

    return

#-------------------------------------------------------------------------------
# Face Strength Material Override
#-------------------------------------------------------------------------------
def face_strength_material_override_update(self, context):
    """Callback function for material override property
    """
    current_face_strength_visibility = getattr(self, ct.IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE)
    print(f"face_strength_material_override_update called, value: {getattr(self, ct.IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE)}")

    fs_mat_manager = FaceStrengthMaterialOverrideManager()
    fs_mat_manager.initialize_material() # you have to check everytime to initialize.
    
    if current_face_strength_visibility == True:
        fs_mat_manager.setup()
    
    else:
        fs_mat_manager.restore()
    
    return


class FaceStrengthMaterialOverrideManager:
    """Face Strength Material Override Manager class
    Imports material and node tree, setup, restore original.

    For objects which have no materials:
        Face strength materials will be generated.
    For objects which have materials:
        For each existing material, material output node will be newlly generated and temprarilly make active.
    """
    face_strength_material:bpy.types.Material = None
    face_strength_node_tree:bpy.types.ShaderNodeTree = None
    
    @classmethod
    def initialize_material(cls):
        """import face strength material and node tree if not exist in current file.
        """
        cls.face_strength_material = bpy.data.materials.get(ct.FACE_STRENGTH_MAT_NAME)
        if cls.face_strength_material == None:
            cls.face_strength_material = myu.load_from_lib_and_return(ct.FACE_STRENGTH_MATERIAL_BLEND_PATH, 'materials', ct.FACE_STRENGTH_MAT_NAME, link=True)

        cls.face_strength_node_tree = bpy.data.node_groups.get(ct.FACE_STRENGTH_MAT_NAME)
        if cls.face_strength_node_tree == None:
            cls.face_strength_node_tree = myu.load_from_lib_and_return(ct.FACE_STRENGTH_MATERIAL_BLEND_PATH, 'node_groups', ct.FACE_STRENGTH_MAT_NAME, link=True)

        return

    
    @classmethod
    def setup(cls):
        all_mesh_obj = [o for o in bpy.data.objects if o.type == 'MESH']
        for obj in all_mesh_obj:
            if len(obj.data.materials) == 0:
                obj.data.materials.append(material=cls.face_strength_material)

        for m in bpy.data.materials:
            if not m.is_grease_pencil:
                cls._setup_node(m)


    @classmethod
    def restore(cls):
        all_mesh_obj = [o for o in bpy.data.objects if o.type == 'MESH'] # you have to check each time for removal of object etc. Might be changed.
        for obj in all_mesh_obj:
            generated_mat = obj.data.materials.get(cls.face_strength_material.name)
            if generated_mat is not None:
                obj.data.materials.pop(index=obj.material_slots[cls.face_strength_material.name].slot_index)
                if len(obj.data.materials) == 0 and len(obj.material_slots) == 1: # pop leaves empty slot. Clean up.
                    obj.data.materials.clear()

        for m in bpy.data.materials:
            if not m.is_grease_pencil:
                cls._restore_node(m)


    @classmethod
    def _setup_node(cls, mat:bpy.types.Material):
        """Set up face strength temporal material node
        """
        node_tree = mat.node_tree
        nodes = mat.node_tree.nodes

        fs_group_node = nodes.new("ShaderNodeGroup")
        fs_group_node.node_tree = cls.face_strength_node_tree
        fs_group_node.location=(0, 0)
        fs_group_node.name = ct.FACE_STRENGTH_MAT_NAME

        temp_mat_output = nodes.new("ShaderNodeOutputMaterial")
        temp_mat_output.name = ct.FACE_STRENGTH_TEMP_OUTPUT_NODE
        temp_mat_output.location=(+200,0)

        node_tree.links.new(fs_group_node.outputs[0], temp_mat_output.inputs[0])
        nodes.active = temp_mat_output


    @classmethod
    def _restore_node(cls, mat:bpy.types.Material):
        """Restore face strenth temporal material node
        """
        node_tree = mat.node_tree
        nodes = mat.node_tree.nodes

        fs_group_node = nodes.get(ct.FACE_STRENGTH_MAT_NAME)
        temp_mat_output = nodes.get(ct.FACE_STRENGTH_TEMP_OUTPUT_NODE)

        if fs_group_node is not None:
            nodes.remove(fs_group_node)
        if temp_mat_output is not None:
            nodes.remove(temp_mat_output)
        return


#-------------------------------------------------------------------------------
# Sync DNT
#-------------------------------------------------------------------------------
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
    prefs = get_preferences()

    if ct.DNT_WEIGHTED_NORMAL_NAME not in modifier_names:
        mod_w_norm = obj.modifiers.new(name=ct.DNT_WEIGHTED_NORMAL_NAME, type="WEIGHTED_NORMAL")
        mod_w_norm.mode = 'CORNER_ANGLE'
        mod_w_norm.keep_sharp = True
        mod_w_norm.use_face_influence = True
        mod_w_norm.show_in_editmode = True


    if ct.DNT_NORMAL_TRANSFER_NAME not in modifier_names:
        mod_dnt_nromal = obj.modifiers.new(name=ct.DNT_NORMAL_TRANSFER_NAME, type="DATA_TRANSFER")

        mod_dnt_nromal.use_object_transform = False
        mod_dnt_nromal.use_loop_data = True
        mod_dnt_nromal.data_types_loops = {'CUSTOM_NORMAL'}
        mod_dnt_nromal.loop_mapping = 'POLYINTERP_NEAREST'
        mod_dnt_nromal.show_in_editmode = True

    else:
        mod_dnt_nromal = obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME)

    if ct.DNT_BEVEL_NAME not in modifier_names:
        mod_dnt_bevel = obj.modifiers.new(name=ct.DNT_BEVEL_NAME, type="BEVEL")

        mod_dnt_bevel.limit_method = 'WEIGHT'
        mod_dnt_bevel.offset_type = prefs.default_bevel_width_type
        mod_dnt_bevel.width = prefs.default_bevel_width
        mod_dnt_bevel.loop_slide = False
        mod_dnt_bevel.use_clamp_overlap = False
        mod_dnt_bevel.show_in_editmode = True

    else:
        mod_dnt_bevel = obj.modifiers.get(ct.DNT_BEVEL_NAME)

    
    # by toggling False -> True, you can ensure the use_pin_to_last order
    mod_dnt_nromal.use_pin_to_last = False
    mod_dnt_bevel.use_pin_to_last = False

    mod_dnt_nromal.use_pin_to_last = True
    mod_dnt_bevel.use_pin_to_last = True



    # Generate collection to store generated DNT normal source object.
    dnt_collection = PartManager.get_mk_reserved_collection_from_obj(obj, ct.DNT_COLLECTION, fallback=bpy.context.scene.collection)
    dnt_collection.hide_render = True
    dnt_collection.hide_viewport = True

    # remove previously created DNT normal source object
    prev_normal_ref_obj = obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME).object
    if prev_normal_ref_obj is not None:
        bpy.data.objects.remove(prev_normal_ref_obj)

    # create normal transfer source object.
    normal_ref_obj = obj.copy()
    normal_ref_obj.name = f"{ct.DNT_NORMAL_TRANSFER_NAME}-{obj.name}"
    setattr(normal_ref_obj, ct.IS_DNT_NORMAL_OBJECT, True)
    clean_up_dnt_modifiers(normal_ref_obj)
    dnt_collection.objects.link(normal_ref_obj)


    # setup data transfer modifier rerference object
    mod_dnt_nromal.object = normal_ref_obj
    return



def clean_up_dnt_modifiers(obj:bpy.types.Object):
    """Remove DNT modifiers from given object
    Remove DNT bevel modifier and DNT normal transfer modifier from given object.
    
    Args:
        obj: DNT modifiers on this object is cleaned up.
    """
    dnt_bevel = obj.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME)
    dnt_normal_transfer = obj.modifiers.get(ct.DNT_BEVEL_NAME)

    if dnt_bevel is not None:
        obj.modifiers.remove(dnt_bevel)    
    if dnt_normal_transfer is not None:
        obj.modifiers.remove(dnt_normal_transfer)

    return


def remove_unused_dnt_normal_object(unused_objs:List[bpy.types.Object]):
    """Cleanup unused generated DNT Normal object
    Remove unused DNT Normal source objects.
    """
    for obj in unused_objs:
        bpy.data.objects.remove(obj)
    return


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
    users_collections = obj.users_collection

    if len(users_collections) != 1: # not assign to valid collection or multiple collection uses this this object
        return fallback
    else:
        user_collection = users_collections[0]

    # when object is directly under part collection
    if getattr(user_collection, ct.IS_MD_HARDSURF_PART_COLLECTION):
        return user_collection

    for c in md_hard_surface_part_collections:
        if user_collection in c.children_recursive:
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
    scene = bpy.context.scene
    part_collection = bpy.data.collections.new(name=part_name)
    part_collection.color_tag = 'COLOR_01'
    setattr(part_collection, ct.IS_MD_HARDSURF_PART_COLLECTION, True)
    scene.collection.children.link(part_collection)
    
    setup_reserved_part_collection(part_collection)
    setattr(scene, ct.SCENE_COLLECTION_CHILD_INDEX, len(scene.collection.children)-1) # activate after creation
    
    print(f"given name is {part_name}, and {part_collection.name} was created")

    return

def setup_reserved_part_collection(part_collection:bpy.types.Collection):
    """Create Final-, Design-, Normal- collection under given part_collection
    Args:
        part_collection: Under this collection, final, design, normal collections will be created.
    """
    final_collection      = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.FINAL_COLLECTION, create=True)
    dependency_collection = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.DEP_COLLECTION, create=True)
    design_collection     = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.DESIGN_COLLECTION, create=True)
    normal_collection     = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.NORMAL_COLLECTION, create=True)

    if getattr(part_collection, ct.IS_MD_HARDSURF_SUB_PART_COLLECTION) == True:
        final_collection.asset_clear()
    else:
        final_collection.asset_mark()

    part_collection.use_fake_user = True # ensure keep even if part is not linked to any scene.

    final_collection.color_tag = 'COLOR_05'
    normal_collection.hide_render = True
    design_collection.hide_render = True
    dependency_collection.color_tag = 'COLOR_06'
    return

def update_subpart_asset_status(self, context):
    """callback function for subpart bool update.
    If True, then clear asset, if False, then mark asset.
    """
    if getattr(self, ct.IS_MD_HARDSURF_PART_COLLECTION, None) is not None:
        final_collection = PartManager.get_mk_reserved_collection_from_part(self, ct.FINAL_COLLECTION, create=False)
        if final_collection is None:
          return
    
    if getattr(self, ct.IS_MD_HARDSURF_SUB_PART_COLLECTION) == True:
        final_collection.asset_clear()
    else:
        final_collection.asset_mark()
    return


#-------------------------------------------------------------------------------
# Rename part collection
#-------------------------------------------------------------------------------
def rename_part_collection(part_collection:bpy.types.Collection, new_name:str)->int:
    """Rename currently selected part col
    """
    current_name = part_collection.name

    if new_name == current_name:
        print("Given name is same with the current one.")
        return 1
    elif not new_name:
        print("Given name is empty")
        return 1
    elif new_name.isspace():
        print("Given name only contains space")
        return 1

    reserved_collection = PartManager.get_collections(part_collection=part_collection)

    part_collection.name = new_name
    for col in reserved_collection:
        col.name = f"{col.name.split('-', 1)[0]}-{new_name}"

    print("rename part is called")
    return

def poll_is_ui_list_active_collection_part(self, context:bpy.types.Context)->bool:
    """Poll function for operator to check if the active collection in UIList is part collection.

    """
    part_collection = getattr(context.scene, ct.ACTIVE_PART_COLLECTION)
    if part_collection is None:
        return False
    return getattr(part_collection, ct.IS_MD_HARDSURF_PART_COLLECTION)


class PartManager:
    """Manages Part Collection"""
    reserved_collection_prefix = [
        ct.FINAL_COLLECTION,
        ct.DEP_COLLECTION,
        ct.DESIGN_COLLECTION,
        ct.NORMAL_COLLECTION,
        ct.DNT_COLLECTION,
    ]

    @classmethod
    def get_collections(cls, part_collection:bpy.types.Collection)->List[bpy.types.Collection]:
        """Get reserved collections under part collection
        It returns final collection, design collection, normal collections etc. Under given part collection.
        It assumes part collection contains no duplicate collection with reserved collection prefix.

        Args:
            part_collection: Under this part collection, reserved collection will be searched and returned

        Returns:
            reserved_collections: Returns reserved collections if found, else, returns empty list. []
        """
        reserved_collections = []
        child_collections = part_collection.children

        for prefix in cls.reserved_collection_prefix:
            for key, value in child_collections.items():
                if key.startswith(f"{prefix}-"):
                    reserved_collections.append(value)
        
        return reserved_collections
    
    @classmethod
    def get_collection_dict(cls, part_collection:bpy.types.Collection):
        """Returns collection dictionary. Basically same with get_collections but it returns dictionary.
        you can access by using key.
        """
        collection_dict = {}
        child_collections = part_collection.children
        for prefix in cls.reserved_collection_prefix:
            for key, col in child_collections.items():
                if key.startswith(f"{prefix}-"):
                    collection_dict[prefix] = col
        return collection_dict
    
    @classmethod
    def get_collection_visibility_dict(cls, part_collection:bpy.types.Collection):
        """Returns dictionary of visibility. You can retrieve visibility of collections under given part.
        This function only consider reserved collection. Prefix can be used as key.

        typically you use with dict.get(key, default) to avoid key error.
        """
        collection_visibility_dict = {}
        child_collections = part_collection.children
        for prefix in cls.reserved_collection_prefix:
            for key, col in child_collections.items():
                if key.startswith(f"{prefix}-"):
                    collection_visibility_dict[prefix] = getattr(col, ct.TEMP_VISIBILITY)
    

        return collection_visibility_dict


    @classmethod
    def get_mk_reserved_collection_from_part(
        cls, 
        part_collection:bpy.types.Collection, 
        prefix:str, 
        create:bool=True,
        )->bpy.types.Collection:
        """ Create or get reserved collection under part collection using prefix.
        Create: Just create using prefix. {prefix}-{part_name} e.g. NORMAL-{part.name} under part collection.
        Get: Get collection with specified prefix. Ignoring rest of the string.

        By specifying only prefix you don't have to worry about digit after collection name e.g. .001

        Args:
            part_collection: under this part collection, reserved collectioon will be created.
            prefix: Create or get collection, whose name starts with this prefix, under parent part collection.
            create: If False, suppress creation of new collection
        """
        for c in part_collection.children[:]:
            if c.name.startswith(f"{prefix}-") and c.library is None: # Ensure collection to be returned is local one. Not externally appended one.
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


    @classmethod
    def get_mk_reserved_collection_from_obj(
        cls, 
        obj:bpy.types.Object, 
        prefix:str, 
        create:bool=True, 
        fallback:bpy.types.Collection=None
        )->bpy.types.Collection:
        """ Create or get reserved collection under part collection using prefix.
        Create: Just create using prefix. {prefix}-{part_name} e.g. NORMAL-{part.name} under part collection.
        Get: Get collection with specified prefix. Ignoring rest of the string.

        By specifying only prefix you don't have to worry about digit after collection name e.g. .001

        Args:
            obj: from this active object, part collection will be searched and reserved collectioon will be created.
            prefix: Create or get collection, whose name starts with this prefix, under parent part collection.
            create: If False, suppress creation of new collection
        """
        part_collection = get_parent_part_collection(obj, fallback=fallback)
        if part_collection == None:
            print("This object is not under part collection, abort.")
            return None

        reserved_collection = cls.get_mk_reserved_collection_from_part(part_collection=part_collection, prefix=prefix, create=create)
        return reserved_collection
            

    @classmethod
    def fix_part_visibility(cls, part_collection:bpy.types.Collection):
        """fix part render and viewport visibility of given part collection.
        """
        cols_under_part_dict = cls.get_collection_dict(part_collection)

        final_collection = cols_under_part_dict.get(ct.FINAL_COLLECTION, None)
        dep_collection = cols_under_part_dict.get(ct.DEP_COLLECTION, None)
        design_collection = cols_under_part_dict.get(ct.DESIGN_COLLECTION, None)
        normal_collection = cols_under_part_dict.get(ct.NORMAL_COLLECTION, None)
        dnt_collection = cols_under_part_dict.get(ct.DNT_COLLECTION, None)


        cls._set_hide_state(col=final_collection,  render=False, viewport=False)
        cls._set_hide_state(col=dep_collection,    render=False, viewport=False)
        # cls._set_visibility(col=design_collection, render=False, viewport=True)
        # cls._set_visibility(col=normal_collection, render=False, viewport=True)
        # cls._set_visibility(col=dnt_collection,    render=True, viewport=True)


    @classmethod
    def _set_hide_state(cls, col:bpy.types.Collection, render:bool=None, viewport:bool=None):
        """Set render and viewport visiblity of given collection. Checks collection validity.
        It also set visibility under all nested object and collection.
        """
        if col is not None:
            if render is not None:
                col.hide_render = render
                for c in col.children_recursive:
                    c.hide_render = render
                for o in col.all_objects:
                    o.hide_render = render
            
            if viewport is not None:
                col.hide_viewport = viewport
                for c in col.children_recursive:
                    c.hide_viewport = render
                for o in col.all_objects:
                    o.hide_viewport = render

    


def get_scene_child_collection_contains_this_collection(scene:bpy.types.Scene, collection:bpy.types.Collection)->bpy.types.Collection:
    """Get direct scene child collection which contains given colleciton.
    Args:
        scene: from this scene.collection.children, given collection will be searched
        collection: Find which scene.collection contains this collection. If this collection is the direct child of scene collection, then return this.

    Returns:
        scene_col: This is the collection which contains given collection. None for not found.
    """

    # if given colection is the direct children of the scene.
    if collection in scene.collection.children[:]:
        return collection
    
    for c in scene.collection.children:
        if collection in c.children_recursive[:]:
            return c
    else:
        return None
    





    
    

#-------------------------------------------------------------------------------
# Show part collection
#-------------------------------------------------------------------------------
def go_to_part_collection(part_collection:bpy.types.Collection):
    """Show given_part_collection. Jump to scene. If not found, then link to current scene.
    It is similar consept with opening file in new tab.
    """
    scene = get_scene_which_has_this_collection(collection=part_collection, fallback=bpy.context.scene)
    bpy.context.window.scene = scene
    set_this_part_active_in_scene(part_collection, scene)

    return


#-------------------------------------------------------------------------------
# Link Part Collection
#-------------------------------------------------------------------------------
def link_ui_list_collection(part_collection:bpy.types.Collection):
    """Link given ui_list collection from current scene.
    Difference between go_go_part is that, This function stays the current scene no matter
    other scene already contains the same part.
    """
    scene = bpy.context.scene
    set_this_part_active_in_scene(part_collection, scene)
    return


#-------------------------------------------------------------------------------
# Unlink Part Collection
#-------------------------------------------------------------------------------
def unlink_ui_list_collection(ui_list_collection:bpy.types.Collection):
    """Unlink given ui_list collection from current scene.
    Unlink but before do this operation, ensure collection has fake user from loss of data.
    """
    sn = bpy.context.scene
    sn_col_children = sn.collection.children
    active_index = getattr(sn, ct.SCENE_COLLECTION_CHILD_INDEX)

    ui_list_collection.use_fake_user = True
    sn_col_children.unlink(ui_list_collection)
    
    new_index = max(min(len(sn_col_children)-1, active_index), 0) # try active index stay the same. but les than length and more than zero.
    setattr(sn, ct.SCENE_COLLECTION_CHILD_INDEX, new_index)
    return

def get_scene_which_has_this_collection(collection:bpy.types.Collection, children_recursive:bool=False, fallback:bpy.types.Scene=None)->bpy.types.Scene:
    """Get scene which has given collections in it. If None, returns fallback scene
    Known issue is, if there are more than two scene which have given part_collection, you cannot determin which scene to jump.

    Args:
        collection: Search Scene which has this part collection.
        children_recursive: If True, search all collections even nested collections.
        fallback: If there is no scene which has given part collection, then return this fallback
    """
    # search is starting from this scene
    if children_recursive == True:
        if collection in bpy.context.scene.collection.children_recursive[:]:
            return bpy.context.scene

        for s in bpy.data.scenes:
            if collection in s.collection.children_recursive[:]:
                return s
        else:
            print(f"no collection found in scenes (check children_recursive). Fallback to default {fallback}")
    else:
        if collection in bpy.context.scene.collection.children[:]:
            return bpy.context.scene

        for s in bpy.data.scenes:
            if collection in s.collection.children[:]:
                return s
        else:
            print(f"no collection found in scenes (only top level children). Fallback to default {fallback}")

    
    return fallback
        


def set_this_part_active_in_scene(part_collection:bpy.types.Collection, scene:bpy.types.Scene, create:bool=True):
    """Set given part_collection active in scene. 
    Args:
        part_collection: this collection will be activated:
        scene: In this scene, part collection will be searched and linked.
        create: If True and given part is not found in the scene, then create a new link between the part_collection and scene
    Returns:
        None
    """
    scene_col = scene.collection

    try:
        index = scene_col.children[:].index(part_collection)
    except ValueError:
        if not create:
            return
        scene_col.children.link(part_collection)
        index = len(scene_col.children) - 1
        
    setattr(scene, ct.SCENE_COLLECTION_CHILD_INDEX, index)
    


#-------------------------------------------------------------------------------
# Organize Part
#-------------------------------------------------------------------------------
# pinter property cannot take getter/setter
def update_scene_ui_list_active_part_collection(self, context):
    """Callback for update active scene collection children.
    """
    scene = bpy.context.scene
    active_index = getattr(self, ct.SCENE_COLLECTION_CHILD_INDEX)
    active_col = get_ui_list_active_collection_from_index(scene=scene, active_index=active_index) # might be none, if there is no collection in scene.

    setattr(scene, ct.ACTIVE_UILIST_COLLECTION, active_col) # This Alwarys returns active collection in the UIList.

    if active_col is not None:
        if getattr(active_col, ct.IS_MD_HARDSURF_PART_COLLECTION) == False:
            active_col = None

    
    setattr(scene, ct.ACTIVE_PART_COLLECTION, active_col) # update readonly property. This returns None when collection is not Part
    bpy.ops.object.hide_collection(collection_index=active_index+1) # collection_index is stargint from 1.

    if active_col is not None: # only apply this code to valid part collection
        restore_child_collection_visibility_under_part(active_col) # you need to restore visibility, because, hide_collection automatically enable visibility of all child collection.

    return

def restore_child_collection_visibility_under_part(part_collection:bpy.types.Collection):
    """Restore child collection visibility under Part.
    After the use of bpy.ops.object.hide_collection, All of the child collection visibilities
    will be automatically updated as True. With this function, you can restore original visibility after the hide_correction
    This function works only for Part Collection.

    TODO:
        make this work other than part collection. This function uses custom visibility property on collection.
        this property is managed only through toggle part child collection visibility toggle operator. Thus visibility property on non-part collection
        won't be updated so its not possible to restore visibility.
    """
    visibilities = PartManager.get_collection_visibility_dict(part_collection)
    part_child_collection_dict = PartManager.get_collection_dict(part_collection)

    
    if len(part_collection.children) > 0: # hide all before restoration.
        # by toggling on and off, you can hide everything in the part collection.
        isolate_collection_under_scene(part_collection.children[0], extend=False)
        isolate_collection_under_scene(part_collection.children[0], extend=True)

    # starting from zero visibility is easy.
    for key, col in part_child_collection_dict.items():
        if visibilities.get(key, False):
            isolate_collection_under_scene(col, extend=True)

    return

def get_ui_list_active_collection_from_index(scene:bpy.types.Scene, active_index:int):
    """Get Scene UIList active collection safely. index out of range is treated.
    """
    try:
        active_col = scene.collection.children[active_index]
    except IndexError: # when collection length is zero. You don't have to update active collection.
        print(f"in get_ui_list_active_collection_from_index: There is no collection in scene.collection. Return None.")
        return None
    except Exception as e:
        print(f"No valid collection found in getter_scene_ui_list_active_collection: {e}")
        return None
    
    return active_col



def move_active_collection_in_ui_list(sn:bpy.types.Scene, move_type:str='UP'):
    """Move Active Collection in UI List on scene collection.
    """
    scene_collection_children = list(sn.collection.children)
    active_slot_index = getattr(sn, ct.SCENE_COLLECTION_CHILD_INDEX)
    collection_len = len(scene_collection_children)
    

    move_from = active_slot_index
    if move_type == 'UP':
        move_to = (active_slot_index - 1) % collection_len
        
    elif move_type == 'DOWN':
        move_to = (active_slot_index + 1) % collection_len
    else:
        print(f"WARNING: move_type must be 'UP' or 'DOWN', but {move_type} was given")
        return
    

    # scene_collection doesn't have 'move()' method which exists in collection property. so you have to manually re construct collection.
    for c in scene_collection_children:
        sn.collection.children.unlink(c)

    active_col = scene_collection_children.pop(move_from)
    scene_collection_children.insert(move_to, active_col)

    for c in scene_collection_children:
        sn.collection.children.link(c)

    setattr(sn, ct.SCENE_COLLECTION_CHILD_INDEX, move_to)
    return


def set_collection_visibility_property_under_part(part_collection:bpy.types.Collection, child_collection:bpy.types.Collection, extend:bool=False):
    """Set Collection Visibility Property Under Part.
    This stores the state of collection visibility under part. When using 'hide collection' operator, resets the visibility.
    Through this function, it stores the visibility state.
    """
    if extend == False:
        for c in part_collection.children:
            setattr(c, ct.TEMP_VISIBILITY, False)

        setattr(child_collection, ct.TEMP_VISIBILITY, True)
    
    else:
        # toggle when extend == True.
        setattr(child_collection, ct.TEMP_VISIBILITY, not getattr(child_collection, ct.TEMP_VISIBILITY))


    return


def part_children_visibility_toggle(part_collection:bpy.types.Collection, child_prefix:str, extend:bool=False):
    """Toggle Visibility of given collection udner part collection.

    Args:
        part_collection: Visibility of Children under this collection will be modified
        child_prefix: prefix is either F, D, DEP, NORMAL, etc. defined in PartManager. 
        The collection starts with given prefix will be used as primary collection to toggle visibility

    """
    reserved_collection = PartManager.get_mk_reserved_collection_from_part(part_collection, child_prefix, create=False)

    if reserved_collection is None:
        print(f"This part collection does not have child collection starts with prefix {child_prefix}-")
        return
    
    isolate_collection_under_scene(reserved_collection, extend)
    set_collection_visibility_property_under_part(part_collection, reserved_collection, extend)
    return


def isolate_collection_under_scene(collection:bpy.types.Collection, extend:bool=False):
    """Isolate collection visibility under current scene.
    """
    # scene_col = bpy.context.scene.collection
    try:
        # index = scene_col.children_recursive.index(collection)
        index = get_index_for_hide_collection_ops(bpy.context.scene, collection)
    except ValueError:
        print("Given collection is not children of this scene collection (recursively checked).")
        return


    bpy.ops.object.hide_collection(collection_index=index, extend=extend)
    return


def get_index_for_hide_collection_ops(scene:bpy.types.Scene, target_collection:bpy.types.Collection):
    """Return index of collection for bpy.ops.object.hide_collection.
    Return Index is already added one for used in oeprator.
    """
    scene_col = scene.collection
    index = _find_index_of_collection_in_scene(collection_list=list(scene_col.children), target_col=target_collection, index=0)
    return index


def _find_index_of_collection_in_scene(collection_list:List[bpy.types.Collection], target_col:bpy.types.Collection, index:int):
    """Recursively search index of given collection in collection list. Count is done according to the bpy.ops.hide_collection collection_index.
    """
    if collection_list == []: # if collection is empty, then no more collections to search. Not found.
        return None
    
    next_collection_list = []
    for c in collection_list:
        index += 1
        if c == target_col:
            return index
        next_collection_list += list(c.children)

    else:
        index = _find_index_of_collection_in_scene(next_collection_list, target_col, index)
        return index
            
        
    
            
def get_view_3d_context()->bpy.types.Context:
    """Get view 3d context for context.temp_override.
    With this, you can get View 3D context to run bpy.ops.object.foo()
    """
    area_type = 'VIEW_3D'
    areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
    override = {
        'screen': bpy.context.window.screen,
        'area': areas[0],
        'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
    }

    context_override = bpy.context.copy()
    for key, value in override.items():
        context_override[key] = value
    
    return context_override



# def get_scene_active_part_collection(scene:bpy.types.Scene)->bpy.types.Collection:
#     """Get Active Part Collection in Given Scene.
#     """
#     active_part_collection = getattr(scene, ct.ACTIVE_PART_COLLECTION)
#     return
# def setter_scene_ui_list_active_collection(self, value):
#     """scene active part collection is read only. You can only set active collection through UI List"""
#     return


#-------------------------------------------------------------------------------
# Shade smooth anywhere
#-------------------------------------------------------------------------------
def shade_smooth_anywhere():
    """Shade smooth anywhere"""
    orig_mode = bpy.context.active_object.mode
    result = 0

    bpy.ops.object.mode_set(mode='OBJECT')
    try:
        bpy.ops.object.shade_smooth()
    except Exception as e:
        print(f"Error on shade_smooth_anywhere. {e}")
        result = 1
        
    bpy.ops.object.mode_set(mode=orig_mode)

    return result


#-------------------------------------------------------------------------------
# Fix Part Render and Viewport Visibilities
#-------------------------------------------------------------------------------
def fix_part_render_and_viewport_visibilities():
    """Fix Part Render and Viewport Visibilities
    This function fixes hide_render and hide_viewport property on collections
    under every part collections.
    """
    parts_collections = [c for c in bpy.data.collections if getattr(c, ct.IS_MD_HARDSURF_PART_COLLECTION)]
    
    for part_col in parts_collections:
        PartManager.fix_part_visibility(part_col)

    return

#-------------------------------------------------------------------------------
# Rename Move File and Data and Sync Project
#-------------------------------------------------------------------------------
def poll_only_local_data_id(self, data):
    """Poll function for checking id is local.
    """
    return data.library is None

def get_data_dir_callback(self, context):
    """Get Data Enum Property
    """
    # following list is data atrribute name which is tested
    data_types = cct.DataAttrNameDict.keys()

    return [(d, d, "") for d in data_types]

def get_data_list_callack(self, context):
    """Callback for list all of get data for enum property
    """
    data_type = self.data_type
    data_list = []
    if data_type is not None:
        data_list = [d.name for d in getattr(bpy.data, data_type)[:] if d.library is None] # Local Only.
    return [(d, d, "") for d in data_list]


def getter_rename_new_name_callback(self):
    """Getter function for determin new name. It avoids Name Collision.
    """
    return self.get('old_name', self.bl_rna.properties['old_name'].default) # to avoid value not assigned error.

def setter_rename_new_name_callback(self, value):
    """Setter function for determin new name. It avoids name collision"""
    pass


def getter_blend_filepath_callback(self):
    return self.get('filepath', self.bl_rna.properties['filepath'].default)

def setter_blend_filepath_callback(self, value:str):
    
    if value.endswith('.blend'):
        filepath_with_ext = value
    else:
        if value.endswith('.'):
            filepath_with_ext = f"{value}blend"
        else:
            filepath_with_ext = f"{value}.blend"

    self['filepath'] = filepath_with_ext


def is_name_exists(id_type:str, new_name:str, only_local:bool=True)->bool:
    """Check if the name is used in current file, given data type.

    Args:
        id_type: such that bpy.types.ID.id_type. E.g. 'CAMERA', 'COLLECTION', 'OBJECT' etc.
        new_name: this name is checked if it is available.
        only_local: If True, 'Check-scope' of the name existance is only local data.
        This means, it allows the existance of  ['foo', ''] and ['foo', 'bar/lib.blend']...  in the same file.
    """

    data_ids = getattr(bpy.data, getattr(DataS, id_type).data_name)
    new_data_id = data_ids.get(new_name, None)

    if only_local:
        return (new_data_id is not None) and (new_data_id.library is None) # only local
    else:
        return (new_data_id is not None) # include externally linked library


