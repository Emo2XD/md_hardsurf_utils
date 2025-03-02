import bpy
from ..setup_tools.register import register_wrap
from . import utils as ut
from . import constants as ct
from pprint import pprint


@register_wrap
class MDHARD_OT_test_x(bpy.types.Operator):
    """Test"""
    bl_idname = "md_hard.test_x"
    bl_label = "Test X"
    

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
        self.report({"INFO"}, f"export script test X called")

        return {"FINISHED"}

