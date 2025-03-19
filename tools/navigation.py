import bpy
import os
from pathlib import Path
from typing import List
from ..myblendrc_utils import utils as myu
from . import constants as ct
from ..prefs import get_preferences
from . import utils as ut


class Navigation:

    @classmethod
    def go_to_source_collection(cls, instance_obj:bpy.types.Object):
        """Go To Source Collection to given instance collection.
        """
        src_col = instance_obj.instance_collection

        src_col_name = src_col.name # TODO: maybe better way other than naive string. UUID?

        if src_col is None:
            print(f"This object is not collection instance.")
            return
        
        if not bpy.data.is_saved:
            print("Save before do this operation.")
            return 1

        if src_col.library is not None:
            filepath = bpy.path.abspath(src_col.library.filepath)
            bpy.ops.wm.save_mainfile()
            bpy.ops.wm.open_mainfile(filepath=filepath)
        
            src_col = bpy.data.collections[src_col_name, None] # ensure pick local one. if there are multiple collection with the same name.
        



        # TODO: you have to nest context override for newly opened file.  There may unecessary codes.
        # cleanup.
        window = bpy.context.window_manager.windows[0]
        with bpy.context.temp_override(window=window):
            scene = ut.get_scene_which_has_this_collection(collection=src_col, children_recursive=True, fallback=bpy.context.scene)
            bpy.context.window.scene = scene

            view_3d_context = ut.get_view_3d_context()
            with bpy.context.temp_override(**view_3d_context):
                scene_child_col = None # direct child collection under scene collection
                # for part
                for p_col in [c for c in bpy.data.collections if getattr(c, ct.IS_MD_HARDSURF_PART_COLLECTION)]:
                    if src_col in p_col.children[:]: # need [:] because CollectionProperty needs to be accessed by string.
                        scene_child_col = p_col
                        break

                # for non-Part
                if scene_child_col is None:
                    scene_child_col = ut.get_scene_child_collection_contains_this_collection(scene, src_col) # direct child collection under scene collection

                if scene_child_col is None: # collection is not in scene and currently in fallback scene,
                    scene_child_col = src_col

                # by specifying direct scene child collection, you can store information in jump history.
                ut.set_this_part_active_in_scene(scene_child_col, scene, create=True) 

                # if scene_child_col is not None: # for Part
                # else: # for other non-part_collection TODO: this doesn't update active index. Which cannot track jump history.
                #     if src_col not in bpy.context.scene.collection.children_recursive[:]:
                #         bpy.context.scene.collection.children.link(src_col)
                #     ut.isolate_collection_under_scene(src_col, extend=False)

        return
    

    
            


            
        


        



        