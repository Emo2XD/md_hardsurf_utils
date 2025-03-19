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
                # print(f"currently in scene '{scene.name}' in '{bpy.path.relpath(bpy.data.filepath)}'")
            # for s in bpy.data.scenes:
            #         print(f"scene_name = {s.name}") # OK. src_col is bad
            area_type = 'VIEW_3D'
            areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
            override = {
                'screen': bpy.context.window.screen,
                'area': areas[0],
                'region': [region for region in areas[0].regions if region.type == 'WINDOW'][0],
            }

            context_override = bpy.context.copy()
            for key, value in override.items():
                context_override[key] = value



            with bpy.context.temp_override(**context_override):
                
                

                parent_part_col = None
                for p_col in [c for c in bpy.data.collections if getattr(c, ct.IS_MD_HARDSURF_PART_COLLECTION)]:
                    if src_col in p_col.children[:]: # need [:] because CollectionProperty needs to be accessed by string.
                        parent_part_col = p_col
                        break
                
                

                if parent_part_col is not None: # for Part
                    ut.set_this_part_active_in_scene(parent_part_col, scene)
                else: # for other non-part_collection
                    if src_col not in bpy.context.scene.collection.children_recursive[:]:
                        bpy.context.scene.collection.children.link(src_col)
                    ut.isolate_collection_under_scene(src_col, extend=False)

        return
            


            
        


        



        