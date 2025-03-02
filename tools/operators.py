import bpy
from ..setup_tools.register import register_wrap
from . import utils as ut
from . import constants as ct
from pprint import pprint



@register_wrap
class MDHARD_OT_sync_dnt(bpy.types.Operator):
    """Setup Dual Normal Transfer (DNT)
    Setup modefier stack for DNT workflow. This includes
    - Weighted Normal
    - Bevel
    - Data transfer
    """
    bl_idname = "md_hard.setup_dnt"
    bl_label = "Setup DNT"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ut.sync_dnt()
        self.report({"INFO"}, f"Setup DNT was called")
        

        return {"FINISHED"}



# @register_wrap
# class MDHARD_OT_update_dnt(bpy.types.Operator):
#     """Update Dual Normal Transfer Counterpart Object
#     """
#     bl_idname = "md_hard.update_dnt"
#     bl_label = "Update DNT"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         self.report({"INFO"}, f"Update DNT called")

#         return {"FINISHED"}



@register_wrap
class MDHARD_OT_normal_transfer(bpy.types.Operator):
    """Add Normal Transfer Modifier along with DNT
    """
    bl_idname = "md_hard.normal_transfer"
    bl_label = "MD Normal Transfer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({"INFO"}, f"Add normal transfer modefier along with DNT")
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_setup_part_collection(bpy.types.Operator):
    """Setup Part Collection for Hard Surface Modeling
    """
    bl_idname = "md_hard.setup_part_collection"
    bl_label = "Setup Part Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({"INFO"}, f"setup part collection was called")
        return {"FINISHED"}





@register_wrap
class MDHARD_OT_test_x(bpy.types.Operator):
    """Test"""
    bl_idname = "md_hard.test_x"
    bl_label = "Test X"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context):
    #     return True

    # def invoke(self, context, event):

    #         shift_pressed = event.shift

    #     if shift_pressed:
    #         self.exclude_active = True
    #     else:
    #         self.exclude_active = False

    #     return self.execute(context)

    def execute(self, context):
        # objs = get_mesh_object_in_collection(getattr(context.scene, ct.TARGET_COLLECTION), recursive=True)
        # pprint(objs)
        # pprint(get_unique_key_block_name_in_collection(getattr(context.scene, ct.TARGET_COLLECTION), recursive=True))
        bpy.data.materials.new("new1")
        print("material created")
        self.report({"INFO"}, f"MD Hard surface utils 'test' X called")

        return {"FINISHED"}
        # return {"CANCELLED"}

