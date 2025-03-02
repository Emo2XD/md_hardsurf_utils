import bpy
from .setup_tools.register import register_prop, register_wrap
from .tools import constants as ct
from .tools import utils as ut


# def poll_is_collection_in_active_scene(self, collection):
#     return collection in bpy.context.scene.collection.children_recursive

# register_prop(
#         bpy.types.Scene,
#         ct.DEPENDENCY_COLLECTION, bpy.props.PointerProperty(type=bpy.types.Collection, description="Collection which contains dependency objects e.g. objects for normal transfer.")
#         )

register_prop(
        bpy.types.Collection,
        ct.IS_MD_HARDSURF_PART_COLLECTION, bpy.props.BoolProperty(name=ct.IS_MD_HARDSURF_PART_COLLECTION, default = False, description="If True, then this collection is considered to be a 'MD Hard surface collection'")
        )

# @register_wrap
# class ShapeKeyInterfaceCollection(bpy.types.PropertyGroup):
#     name: bpy.props.StringProperty(name="Name") # type: ignore
#     value: bpy.props.FloatProperty(name="Value", subtype='FACTOR', min=0.0, max=1.0, default=0.0, update=ut.set_shape_key_value_callback) # type: ignore
#     lock_shape: bpy.props.BoolProperty(name="lock_shape", set=ut.set_sk_interface_lock_shape_callback, get=ut.get_sk_interface_lock_shape_callback, default=False) # type: ignore

