import bpy
from ..setup_tools.register import register_wrap
from . import constants as ct
from . import operators as ot
from . import utils as ut




@register_wrap
class MDHARD_PT_md_hard(bpy.types.Panel):
    """Collection shape key
    """
    bl_idname = "MDHARD_PT_md_hard" 
    bl_label = "Hard Surface Utils"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MD Hard" # tab name

    def draw(self, context):
        active_obj = context.active_object
        if active_obj is not None:
            part_collection = ut.get_parent_part_collection(active_obj)
            if part_collection is None:
                part_collection = context.scene.collection
        else:
            part_collection = context.scene.collection


        layout = self.layout
        layout.operator(ot.MDHARD_OT_test_x.bl_idname, text="Test X")
        layout.operator(ot.MDHARD_OT_setup_part_collection.bl_idname, text="Setup Part", icon="OUTLINER_COLLECTION")

        layout.prop(part_collection, ct.NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION, text="Source")
        layout.operator(ot.MDHARD_OT_normal_transfer.bl_idname, text="Normal Transfer", icon="MOD_DATA_TRANSFER")

        layout.separator()
        layout.label(text="Dual Normal Transfer")
        layout.operator(ot.MDHARD_OT_sync_dnt.bl_idname, text="Sync DNT", icon="FILE_REFRESH")
        # layout.operator(ot.MDHARD_OT_update_dnt.bl_idname, text="Update DNT", icon="FILE_REFRESH")



        return
