import bpy
import os
from pathlib import Path
from typing import List
from ..myblendrc_utils import utils as myu
from . import constants as ct
from ..prefs import get_preferences
from . import utils as ut



class NavElement:
    """Store navigation point in the history."""    
    def __init__(self, filepath:str='', scene:str='', active_part_index:int=0):
        self.filepath:str = None
        self.scene:str = None # TODO: Using pointer is preferable but not work for external file. So naively use string
        self.active_index:int = None # index of current direct scene collection child index.


class Navigation:
    nav_history:List[NavElement] = [NavElement()]
    nav_current_index:int = 0
    MAX_HISTORY:int = 8

    @classmethod
    def add_nav_history(cls):
        """Add new NavElement and set new element as current.
        All forwarding history will be removed.
        """
        cls._update_current_nav_element()
        
        #remove forwarding history branch before add
        if cls.nav_current_index < len(cls.nav_history) - 1:
            del cls.nav_history[cls.nav_current_index+1:]

        cls.nav_history.append(NavElement())
        
        # If length of history is exceeding max count, then remove it from front.
        cls.MAX_HISTORY = get_preferences().max_nav_history
        del cls.nav_history[:max(len(cls.nav_history)-cls.MAX_HISTORY, 0)]


        cls.nav_current_index = len(cls.nav_history) - 1 # last index of nav_history
        return

    @classmethod
    def _update_current_nav_element(cls):
        """Update current scene and active index of nav element"""
        current = cls.nav_history[cls.nav_current_index]
        current.filepath = bpy.data.filepath
        current.scene = bpy.context.scene.name
        current.active_index = getattr(bpy.context.scene, ct.SCENE_COLLECTION_CHILD_INDEX)
        

    @classmethod
    def nav_forward(cls):
        """Navigate forward to next navigation point in history. Do nothing when out of history range."""
        cls._update_current_nav_element()
        orig_index = cls.nav_current_index
        next_index, next_nav_element = cls._get_nav_element_clamped(index=orig_index + 1)
        cls.go_to_history_point(next_nav_element)
        cls.nav_current_index = next_index

        if orig_index == next_index: # navigation not taken.
            return 1

    @classmethod
    def nav_back(cls):
        """Navigate back to previous navigation point in history. Do nothing when out of history range."""
        cls._update_current_nav_element()
        orig_index = cls.nav_current_index
        prev_index, prev_nav_element = cls._get_nav_element_clamped(index=orig_index - 1)
        cls.go_to_history_point(prev_nav_element)
        cls.nav_current_index = prev_index

        if orig_index == prev_index: # navigation not taken.
            return 1


    @classmethod
    def _get_nav_element_clamped(cls, index:int):
        """Get NavElement form cls.nav_history. Index will be clamped to fit history length
        Args:
            index: try to get this element in nav_history.
        Returns:
            clamped_index: if the given index is out of range, clamped to 0 to length of nav_history
            nav_history_element:
        """
        clamped_index = cls._clamped_index(index)
        return clamped_index, cls.nav_history[clamped_index]

    @classmethod
    def _clamped_index(cls, index):
        return max(0, min(len(cls.nav_history)-1, index))


    @classmethod
    def go_to_history_point(cls, nav_element:NavElement):
        if nav_element.filepath != bpy.data.filepath:
            bpy.ops.wm.save_mainfile()
            bpy.ops.wm.open_mainfile(filepath=nav_element.filepath)

        nav_scene = bpy.data.scenes.get(nav_element.scene)
        if nav_scene is None:
            return
        
        if nav_element.active_index is None: # TODO: maybe redundant check?
            return
        
        window = bpy.context.window_manager.windows[0]
        with bpy.context.temp_override(window=window):
            bpy.context.window.scene = nav_scene
            view_3d_context = ut.get_view_3d_context()
            with bpy.context.temp_override(**view_3d_context):
                setattr(bpy.context.scene, ct.SCENE_COLLECTION_CHILD_INDEX, nav_element.active_index)


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

        cls.add_nav_history()

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
                # else:
                #     if src_col not in bpy.context.scene.collection.children_recursive[:]:
                #         bpy.context.scene.collection.children.link(src_col)
                #     ut.isolate_collection_under_scene(src_col, extend=False)

        return