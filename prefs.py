"""
TODO: Define preferences for this addon
"""
import bpy
from .setup_tools.register import register_wrap


@register_wrap
class MDHARD_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    default_bevel_width: bpy.props.FloatProperty(
        name = "Bevel Width",
        default = 0.01,
        description = "Default bevel width when using DNT",
        min=0.0,
        precision=4
    ) # type: ignore

    default_bevel_width_type: bpy.props.EnumProperty(
        name = "Width Type",
        description="Default bevel width type when using DNT",
        default='WIDTH',
        items=[
            ('OFFSET'  , 'OFFSET', ''),
            ('WIDTH'   , 'WIDTH', ''),
            ('DEPTH'   , 'DEPTH', ''),
            ('PERCENT' , 'PERCENT', ''),
            ('ABSOLUTE', 'ABSOLUTE', ''),
        ]
        
    ) #type: ignore
 
    def draw(self, context):
        layout = self.layout
        # layout.label(text='Custom Design Doll Directory:')
        layout.label(text="DNT Default Settings", icon='MOD_BEVEL')
        layout.prop(self, 'default_bevel_width', text="Width")
        layout.prop(self, 'default_bevel_width_type', text="Type")



def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences
