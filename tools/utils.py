import bpy
import bmesh
import os
from pathlib import Path
from typing import List
from ..myblendrc_utils import utils as myu
from . import constants as ct
from ..prefs import get_preferences
import numpy as np


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
    active_obj = bpy.context.active_object
    if active_obj is None:
        return False
    
    # normal_collection = get_mk_reserved_collection_under_part(obj=active_obj, prefix=ct.NORMAL_COLLECTION, create=False)
    normal_collection = PartManager.get_mk_reserved_collection_from_obj(obj=active_obj, prefix=ct.NORMAL_COLLECTION, create=False)
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
    
    part_collection = get_parent_part_collection(obj=active_obj)

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
    normal_collection = PartManager.get_mk_reserved_collection_from_obj(active_obj, ct.NORMAL_COLLECTION)
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



def regenerate_reserved_collection_under_part():
    """Regenerate reserved collection under part (when accidentally removed some of them)
    """
    part_collection = bpy.context.collection
    setup_reserved_part_collection(part_collection)
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
    part_collection = bpy.data.collections.new(name=part_name)
    part_collection.color_tag = 'COLOR_01'
    setattr(part_collection, ct.IS_MD_HARDSURF_PART_COLLECTION, True)
    bpy.context.scene.collection.children.link(part_collection)
    
    setup_reserved_part_collection(part_collection)
    print(f"given name is {part_name}, and {part_collection.name} was created")

    return

def setup_reserved_part_collection(part_collection:bpy.types.Collection):
    """Create Final-, Design-, Normal- collection under given part_collection
    Args:
        part_collection: Under this collection, final, design, normal collections will be created.
    """
    part_collection.use_fake_user = True # ensure keep even if part is not linked to any scene.

    final_collection      = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.FINAL_COLLECTION, create=True)
    dependency_collection = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.DEP_COLLECTION, create=True)
    design_collection     = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.DESIGN_COLLECTION, create=True)
    normal_collection     = PartManager.get_mk_reserved_collection_from_part(part_collection, ct.NORMAL_COLLECTION, create=True)



    final_collection.color_tag = 'COLOR_05'
    normal_collection.hide_render = True
    design_collection.hide_render = True
    dependency_collection.color_tag = 'COLOR_06'
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
            
    

#-------------------------------------------------------------------------------
# Show part collection
#-------------------------------------------------------------------------------
def show_part_collection(part_collection:bpy.types.Collection):
    """Show given_part_collection. Jump to scene. If not found, then link to current scene.
    It is similar consept with opening file in new tab.
    """
    scene = get_scene_which_has_this_part_collection(part_collection=part_collection, fallback=bpy.context.scene)
    bpy.context.window.scene = scene
    _isolate_part_collection_in_scene(part_collection, scene)

    return


def get_scene_which_has_this_part_collection(part_collection:bpy.types.Collection, fallback:bpy.types.Scene=None)->bpy.types.Scene:
    """Get scene which has given part collections in it. If None, returns fallback scene
    Known issue is, if there are more than two scene which have given part_collection, you cannot determin which scene to jump.

    Args:
        part_collection: Search Scene which has this part collection.
        fallback: If there is no scene which has given part collection, then return this fallback
    """
    # search is starting from this scene
    if part_collection in bpy.context.scene.collection.children[:]:
        return bpy.context.scene

    for s in bpy.data.scenes:
        if part_collection in s.collection.children[:]:
            return s
    
    return fallback
        


def _isolate_part_collection_in_scene(part_collection:bpy.types.Collection, scene:bpy.types.Scene):
    """Isolate Part Collection in Given Scene
    Args:
        part_collection: this collection will be isolated:
        scene: In this scene, part collection will be searched and linked.
    Returns:
        None
    """
    scene_col = scene.collection

    try:
        index = scene_col.children[:].index(part_collection) + 1
    except ValueError:
        scene_col.children.link(part_collection)
        index = len(scene_col.children) # last one is the target index index is start from 1
        
    
    bpy.ops.object.hide_collection(collection_index=index)


#-------------------------------------------------------------------------------
# Shade smooth anywhere
#-------------------------------------------------------------------------------
def shade_smooth_anywhere():
    """Shade smooth anywhere"""
    orig_mode = bpy.context.active_object.mode

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode=orig_mode)

    return