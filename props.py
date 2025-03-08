import bpy
from .setup_tools.register import register_prop, register_wrap, register_other
from .tools import constants as ct
from .tools import utils as ut



register_prop(
        bpy.types.Collection,
        ct.NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION, bpy.props.PointerProperty(type=bpy.types.Object, description="Source object for normal transfer modifier defined per part collection.", poll=ut.poll_is_obj_in_part_collection)
        )

register_prop(
        bpy.types.Collection,
        ct.IS_MD_HARDSURF_PART_COLLECTION, bpy.props.BoolProperty(name=ct.IS_MD_HARDSURF_PART_COLLECTION, default = False, description="If True, then this collection is considered to be a 'MD Hard surface collection'")
        )

register_prop(
        bpy.types.Scene,
        ct.IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE, bpy.props.BoolProperty(
            name=ct.IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE, 
            default = False, 
            description="If True, then override current material with face strength",
            update=ut.face_strength_material_override_update
            )
        )

# def msgbus_callback(*arg):
#     # in console will be print selected_objects 
#     print(bpy.context.selected_objects)
#     # you can do something
        
# def subscribe_to_obj(): 
             
#     bpy.msgbus.subscribe_rna(
#         key=(bpy.types.LayerObjects, 'active'),
#         owner=bpy,
#         args=(),
#         notify=msgbus_callback
#         )
    
# def unsubscribe_to_obj():
#     bpy.msgbus.clear_by_owner(bpy)

# register_other(
# subscribe_to_obj,
# unsubscribe_to_obj
# )

# @register_wrap
# class ShapeKeyInterfaceCollection(bpy.types.PropertyGroup):
#     name: bpy.props.StringProperty(name="Name") # type: ignore
#     value: bpy.props.FloatProperty(name="Value", subtype='FACTOR', min=0.0, max=1.0, default=0.0, update=ut.set_shape_key_value_callback) # type: ignore
#     lock_shape: bpy.props.BoolProperty(name="lock_shape", set=ut.set_sk_interface_lock_shape_callback, get=ut.get_sk_interface_lock_shape_callback, default=False) # type: ignore

