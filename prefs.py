"""
TODO: Define preferences for this addon
"""
import bpy
from .setup_tools.register import register_wrap


# @register_wrap
# class PAINTWORKFLOW_Preferences(bpy.types.AddonPreferences):
#     bl_idname = __package__

#     user_mts_path: bpy.props.StringProperty(
#         name = "User MTS Folder",
#         default = "",
#         description = "Specify the directory of user created Mask Texture Paint folder path",
#         subtype = 'DIR_PATH'
#     ) # type: ignore
 
#     def draw(self, context):
#         layout = self.layout
#         # layout.label(text='Custom Design Doll Directory:')
#         row = layout.row()
#         row.prop(self, 'user_mts_path', expand=True)


# def get_preferences():
#     return bpy.context.preferences.addons[__package__].preferences
