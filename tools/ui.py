import bpy
from ..setup_tools.register import register_wrap
from . import constants as ct
from . import operators as ot
from . import utils as ut




@register_wrap
class MDHARD_PT_md_hard(bpy.types.Panel):
    """Panel for MD hard surface modeling utils
    """
    bl_idname = "MDHARD_PT_md_hard" 
    bl_label = "Hard Surface Utils"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MD Hard" # tab name

    def draw(self, context):
        

        layout = self.layout
        # layout.operator(ot.MDHARD_OT_test_x.bl_idname, text="Test X")
        row = layout.row(align=True)
        split = row.split(factor=0.8, align=True)
        split.operator(ot.MDHARD_OT_setup_part_collection.bl_idname, text="Setup Part", icon="OUTLINER_COLLECTION")
        split.operator(ot.MDHARD_OT_regenerate_collections_under_part.bl_idname, text="", icon="FILE_REFRESH")

        

        
        # layout.operator(ot.MDHARD_OT_update_dnt.bl_idname, text="Update DNT", icon="FILE_REFRESH")



        return
@register_wrap
class MDHARD_PT_md_normal_transfer(bpy.types.Panel):
    """Panel for normal transfer
    """
    bl_idname = "MDHARD_PT_md_normal_transfer" 
    bl_label = "Part Operators"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MD Hard" # tab name



    def draw(self, context):
        active_obj = context.active_object
        if active_obj is not None:
            part_collection = ut.get_parent_part_collection(active_obj, fallback=None)
        else:
            part_collection = None

        layout = self.layout

        if part_collection is not None:
            layout.label(text=f"Active Part: {part_collection.name}", icon="OUTLINER_COLLECTION")
            layout.prop(part_collection, ct.NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION, text="Source")
            row = layout.row(align=True)
            split = row.split(factor=0.2)
            split.operator(ot.MDHARD_OT_separate_normal_source.bl_idname, text="", icon="MOD_EXPLODE")
            split.operator(ot.MDHARD_OT_normal_transfer.bl_idname, text="Normal Transfer", icon="MOD_DATA_TRANSFER")

        else:
            layout.label(text=f"Active Part: None")

        layout.separator()
        layout.operator(ot.MDHARD_OT_sync_dnt.bl_idname, text="Sync DNT", icon="FILE_REFRESH")    

        
        return
    



@register_wrap
class MDHARD_MT_md_hard_surface(bpy.types.Menu):
    bl_label = "MD Hard Surface Menu"
    bl_idname = "MDHARD_MT_md_hard_surface"

    def draw(self, context):
        layout = self.layout
        try:
            if context.area.type == 'VIEW_3D':
                layout.menu(MDHARD_MT_face_strength_submenu.bl_idname, text="F Face Strength...", icon="FACESEL")
                layout.menu(MDHARD_MT_edge_bevel_weight_submenu.bl_idname, text="B Bevel Weight...", icon="MOD_BEVEL")
                layout.menu(MDHARD_MT_toggle_submenu.bl_idname, text="T Toggle Vibility...")
            

        except AttributeError:
            # Exception when you have not selected anything.
            # When you have not selected mesh, you cannot check the line
            # "context.object.type"  but this error doesn't do anything so ignore it.
            pass


@register_wrap
class MDHARD_MT_face_strength_submenu(bpy.types.Menu):
    bl_label = "Face Strength Menu"
    bl_idname = "MDHARD_MT_face_strength_submenu"

    def draw(self, context):
        layout = self.layout
        try:
            if context.object.type == 'MESH':
                if context.active_object.mode=='EDIT':
                    ops_face_weak = layout.operator("mesh.mod_weighted_strength", text="W Weak")
                    ops_face_weak.set = True
                    ops_face_weak.face_strength = 'WEAK'

                    ops_face_medium = layout.operator("mesh.mod_weighted_strength", text="M Medium")
                    ops_face_medium.set = True
                    ops_face_medium.face_strength = 'MEDIUM'

                    ops_face_strong = layout.operator("mesh.mod_weighted_strength", text="S Strong")
                    ops_face_strong.set = True
                    ops_face_strong.face_strength = 'STRONG'

        except AttributeError:
            pass


@register_wrap
class MDHARD_MT_edge_bevel_weight_submenu(bpy.types.Menu):
    bl_label = "Edge Bevel Weight Menu"
    bl_idname = "MDHARD_MT_edge_bevel_weight_submenu"

    def draw(self, context):
        layout = self.layout
        try:
            if context.object.type == 'MESH':
                if context.active_object.mode=='EDIT':
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="Z set 0.00").weight = 0.0
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="A set 0.10").weight = 0.1
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="S set 0.25").weight = 0.25
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="D set 0.50").weight = 0.5
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="F set 0.75").weight = 0.75
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="G set 1.00").weight = 1.0
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="B Set Previous")

        except AttributeError:
            pass

      
@register_wrap
class MDHARD_MT_toggle_submenu(bpy.types.Menu):
    bl_label = "Hard Surface Toggle Menu"
    bl_idname = "MDHARD_MT_toggle_submenu"

    def draw(self, context):
        layout = self.layout
        try:
            if context.object.type == 'MESH':
                layout.operator(ot.MDHARD_OT_toggle_dnt_visibility.bl_idname, text="T Toggle DNT visibility")
                
        except AttributeError:
            pass

        
        # layout.menu("MYBLENDRC_MT_MIP_SUBMENU", text="M MIP/MTS operators...")

