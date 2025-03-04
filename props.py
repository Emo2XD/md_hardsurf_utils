import bpy
from .setup_tools.register import register_prop, register_wrap
from .tools import constants as ct
from .tools import utils as ut

# TODO: Add filter funciton to only show objects in active part collection?
def poll_is_obj_in_part_collection(self, obj):
    return obj.type == 'MESH'

register_prop(
        bpy.types.Collection,
        ct.NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION, bpy.props.PointerProperty(type=bpy.types.Object, description="Source object for normal transfer modifier defined per part collection.", poll=poll_is_obj_in_part_collection)
        )

register_prop(
        bpy.types.Collection,
        ct.IS_MD_HARDSURF_PART_COLLECTION, bpy.props.BoolProperty(name=ct.IS_MD_HARDSURF_PART_COLLECTION, default = False, description="If True, then this collection is considered to be a 'MD Hard surface collection'")
        )

# @register_wrap
# class ShapeKeyInterfaceCollection(bpy.types.PropertyGroup):
#     name: bpy.props.StringProperty(name="Name") # type: ignore
#     value: bpy.props.FloatProperty(name="Value", subtype='FACTOR', min=0.0, max=1.0, default=0.0, update=ut.set_shape_key_value_callback) # type: ignore
#     lock_shape: bpy.props.BoolProperty(name="lock_shape", set=ut.set_sk_interface_lock_shape_callback, get=ut.get_sk_interface_lock_shape_callback, default=False) # type: ignore

