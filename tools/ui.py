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
        layout.operator(ot.MDHARD_OT_test_x.bl_idname, text="Test X")
        row = layout.row(align=True)
        split = row.split(factor=0.8, align=True)
        split.operator(ot.MDHARD_OT_setup_part_collection.bl_idname, text="Setup Part", icon="OUTLINER_COLLECTION")
        split.operator(ot.MDHARD_OT_regenerate_collections_under_part.bl_idname, text="", icon="FILE_REFRESH")

        

        layout.separator()
        layout.label(text="Dual Normal Transfer")
        layout.operator(ot.MDHARD_OT_sync_dnt.bl_idname, text="Sync DNT", icon="FILE_REFRESH")
        # layout.operator(ot.MDHARD_OT_update_dnt.bl_idname, text="Update DNT", icon="FILE_REFRESH")



        return
@register_wrap
class MDHARD_PT_md_normal_transfer(bpy.types.Panel):
    """Panel for normal transfer
    """
    bl_idname = "MDHARD_PT_md_normal_transfer" 
    bl_label = "Normal Transfer"
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
            layout.label(text=f"Active Part: {part_collection.name}")
            layout.prop(part_collection, ct.NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION, text="Source")
            layout.operator(ot.MDHARD_OT_normal_transfer.bl_idname, text="Normal Transfer", icon="MOD_DATA_TRANSFER")
        else:
            layout.label(text=f"Active Part: None")
            
            

        return