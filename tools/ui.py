import bpy
from ..setup_tools.register import register_wrap
from . import constants as ct
from . import operators as ot




@register_wrap
class MDHARD_PT_md_hard(bpy.types.Panel):
    """Collection shape key
    """
    bl_idname = "MDHARD_PT_md_hard" 
    bl_label = "Hard Surface Utils"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MDHard" # tab name

    def draw(self, context):
        layout = self.layout
        layout.operator(ot.MDHARD_OT_test_x.bl_idname, text="Test X")



        return
