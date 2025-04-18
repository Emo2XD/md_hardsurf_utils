import bpy
from .setup_tools.register import register_prop, register_wrap, register_other
from .tools import constants as ct
from .tools import utils as ut
from .myblendrc_utils.common_constants import DataAttrNameDict


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

register_prop(
        bpy.types.Object,
        ct.IS_DNT_NORMAL_OBJECT, bpy.props.BoolProperty(
            name=ct.IS_DNT_NORMAL_OBJECT, 
            default = False, 
            description="If True, then this object is considered to be generated and automatically cleaned up when not referenced by DNT modifier",
            )
        )

register_prop(
        bpy.types.WindowManager,
        ct.OPEN_PART_COLLECTION_PLACEHOLDER, bpy.props.PointerProperty(type=bpy.types.Collection, description="Part Collection inside this Blender.", poll=ut.poll_is_part_collection)
        )



register_prop(
        bpy.types.Scene,
        ct.SCENE_COLLECTION_CHILD_INDEX,
        bpy.props.IntProperty(name=ct.SCENE_COLLECTION_CHILD_INDEX, default=-1, update=ut.update_scene_ui_list_active_part_collection)
        )


register_prop(
        bpy.types.Scene,
        ct.ACTIVE_PART_COLLECTION,
        bpy.props.PointerProperty(
            type=bpy.types.Collection, 
            description="Readonly active part collection", 
            )) # this returns None if collection is not Part

register_prop(
        bpy.types.Scene,
        ct.ACTIVE_UILIST_COLLECTION,
        bpy.props.PointerProperty(
            type=bpy.types.Collection, 
            description="Readonly active UIList collection", 
            )) # this return active collection.


register_prop(
        bpy.types.Collection,
        ct.TEMP_VISIBILITY, bpy.props.BoolProperty(name=ct.TEMP_VISIBILITY, default = True, description="Store Visibility (eye icon in the outliner)")
        )

register_prop(
        bpy.types.Collection,
        ct.IS_MD_HARDSURF_SUB_PART_COLLECTION, bpy.props.BoolProperty(
            name=ct.IS_MD_HARDSURF_SUB_PART_COLLECTION, 
            default=False, 
            description="Subpart. True when part is not complete part and no need to mark as asset.",
            update=ut.update_subpart_asset_status
            )
        )

register_prop(
        bpy.types.WindowManager,
        ct.MD_PROJECT_CWD, bpy.props.StringProperty(
            name=ct.MD_PROJECT_CWD, 
            default='', 
            description="Keep Track of currently opened project."
            )
        )


register_prop(
        bpy.types.WindowManager,
        ct.MD_HARPOON_INDEX,
        bpy.props.IntProperty(name=ct.MD_HARPOON_INDEX, default=-1)
        )

@register_wrap
class MDHarpoonCollection(bpy.types.PropertyGroup):
    name:bpy.props.StringProperty(name='name', default='') #type: ignore
    filepath:bpy.props.StringProperty(name='filepath', subtype='FILE_PATH') #type: ignore

register_prop(
        bpy.types.WindowManager,
        ct.MD_HARPOON_UILIST_COLLECTION,
        bpy.props.CollectionProperty(type=MDHarpoonCollection)
        )


# placeholder for rename data.
for d_type in DataAttrNameDict.keys():
    register_prop(
        bpy.types.WindowManager,
        f"{ct.MD_PREFIX}_{d_type}",
        bpy.props.PointerProperty(
            type=getattr(bpy.types, d_type),
            poll = ut.poll_only_local_data_id
        )
    )

def get_md_data_id_placeholder(d_type:str):
    """Return Data ID which is stored in window manager.
    Args:
       d_type: e.g. "Collection", "Object", etc. You can find by using dir(bpy.types) 
    """
    wm = bpy.context.window_manager
    data_id = getattr(wm, f"{ct.MD_PREFIX}_{d_type}")
    return data_id


@register_wrap
class MDRmapHolderGroup(bpy.types.PropertyGroup):
    name:bpy.props.StringProperty(name='name', default='') #type: ignore


register_prop(
        bpy.types.WindowManager,
        ct.MD_REMAP_HOLDER_FROM,
        bpy.props.CollectionProperty(type=MDRmapHolderGroup)
        )

register_prop(
        bpy.types.WindowManager,
        ct.MD_REMAP_HOLDER_TO,
        bpy.props.CollectionProperty(type=MDRmapHolderGroup)
        )



# register_prop(
#         bpy.types.Collection,
#         ct.DEP_COLLECTION, bpy.props.BoolProperty(name=ct.DEP_COLLECTION, default = False, description="Store Visibility of collection under part collection")
#         )
# register_prop(
#         bpy.types.Collection,
#         ct.DESIGN_COLLECTION, bpy.props.BoolProperty(name=ct.DESIGN_COLLECTION, default = False, description="Store Visibility of collection under part collection")
#         )
# register_prop(
#         bpy.types.Collection,
#         ct.NORMAL_COLLECTION, bpy.props.BoolProperty(name=ct.NORMAL_COLLECTION, default = False, description="Store Visibility of collection under part collection")
#         )
# @register_wrap
# class ReservedPartCollectionVisibility(bpy.types.PropertyGroup):
#     final: bpy.props.BoolProperty(name=ct.FINAL_COLLECTION, default=True) # type: ignore
#     dependency:bpy.props.BoolProperty(name=ct.DEP_COLLECTION, default=False) # type: ignore
#     design:bpy.props.BoolProperty(name=ct.DESIGN_COLLECTION, default=False) # type: ignore
#     normal:bpy.props.BoolProperty(name=ct.NORMAL_COLLECTION, default=False) # type: ignore

#     # TODO: init method not work so you have to construct dictionary here.
#     def get_props(self):
#         """get current visibility"""
#         visibility_dict = {
#         ct.FINAL_COLLECTION : self.final, 
#         ct.DEP_COLLECTION : self.dependency, 
#         ct.DESIGN_COLLECTION : self.design, 
#         ct.NORMAL_COLLECTION : self.normal
#         }
#         return visibility_dict
    
#     def set_props(self, prop_dict:dict):
#         visibility_dict = self.get_props()
#         for key, value in prop_dict.items():
#             visibility_dict[key] = value
#         return


# register_prop(
#         bpy.types.Collection,
#         ct.RESERVED_PART_COLLECTION_VISIBILITY,
#         bpy.props.PointerProperty(
#             type=ReservedPartCollectionVisibility, 
#             description="Store Visibility of reserved collection under Part collection", 
#             ))




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

