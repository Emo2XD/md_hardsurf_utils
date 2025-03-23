import bpy
from pathlib import Path
from ..setup_tools.register import register_wrap
from . import utils as ut
from . import constants as ct
from pprint import pprint
from . import navigation as nav
from . import md_project as mdp

@register_wrap
class MDHARD_OT_sync_dnt(bpy.types.Operator):
    """Setup Dual Normal Transfer (DNT)
    Setup modefier stack for DNT workflow. This includes
    - Weighted Normal
    - Bevel
    - Data transfer
    """
    bl_idname = "md_hard.setup_dnt"
    bl_label = "Setup DNT"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context:bpy.types.Context):
        active_obj = context.active_object
        if active_obj is None:
            return False
        else:
            return active_obj.type == 'MESH'

    def execute(self, context):
        ut.sync_dnt()
        self.report({"INFO"}, f"Setup DNT was called")
        

        return {"FINISHED"}


@register_wrap
class MDHARD_OT_toggle_dnt_visibility(bpy.types.Operator):
    """Toggle DNT visibility
    Toggles following two modifier visibility
    - DNT Bevel
    - DNT Data transfer
    """
    bl_idname = "md_hard.toggle_dnt_visibility"
    bl_label = "Toggle DNT Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context:bpy.types.Context):
        return context.active_object is not None

    def execute(self, context):
        obj = bpy.context.active_object
        result = ut.toggle_dnt_visibility(obj)
        
        if result == 1:
            self.report({"WARNING"}, f"This object does not have DNT modifiers.")
            return {"CANCELLED"}


        return {"FINISHED"}


@register_wrap
class MDHARD_OT_normal_transfer(bpy.types.Operator):
    """Add Normal Transfer Modifier along with DNT
    If there is no source object, then those vertices will be removed from normal transfer.
    Each vertex must be in only one normal transfer vertex group. This operator automatically
    cleans up vertex group.
    """
    bl_idname = "md_hard.normal_transfer"
    bl_label = "MD Normal Transfer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context:bpy.types.Context):
        active_obj = context.active_object
        if active_obj is None:
            return False
        else:
            return active_obj.type == 'MESH' and active_obj.mode == 'EDIT'
        
        
    def execute(self, context):

        target_obj = context.active_object
        # part_collection = ut.get_parent_part_collection(obj=target_obj, fallback=None)
        part_collection = getattr(bpy.context.scene, ct.ACTIVE_PART_COLLECTION)
        if part_collection is None:
            self.report({"WARNING"}, f"Please Setup Valid Part Collection.")
            return {"CANCELLED"}

        normal_src_obj = getattr(part_collection, ct.NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION, None)

        result = ut.normal_transfer(target_obj=target_obj, normal_src_obj=normal_src_obj)

        if result == 1:
            self.report({"WARNING"}, f"No vertex is selected")
            return {"CANCELLED"}
        
        self.report({"INFO"}, f"MD Normal transfer")
        return {"FINISHED"}



@register_wrap
class MDHARD_OT_separate_normal_source(bpy.types.Operator):
    """Separates selection as normal transfer source object 
    After separation, newly created object will be automatically moved to normal collection.
    If there are DNT modifiers, they will be removed.
    """
    bl_idname = "md_hard.separate_normal_source"
    bl_label = "MD Separate as Normal Source"
    bl_options = {'REGISTER', 'UNDO'}

    src_obj_name: bpy.props.StringProperty(name="Source", default=f'Normal_Source') #type: ignore
    set_as_normal_source: bpy.props.BoolProperty(name="Set As Source", default=True, description="If True, this separated object will be set as src object. You can then use this object in normal transfer") # type:ignore
    shade_smooth: bpy.props.BoolProperty(name="Shade Smooth", default=True, description="If True, force shade smooth on split.") # type: ignore

    @classmethod
    def poll(self, context:bpy.types.Context):
        active_obj = context.active_object
        if active_obj is None:
            return False
        else:
            return active_obj.type == 'MESH' and active_obj.mode == 'EDIT'
        
        
    def execute(self, context):

        target_obj = context.active_object
        # part_collection = ut.get_parent_part_collection(obj=target_obj, fallback=None)
        part_collection = getattr(bpy.context.scene, ct.ACTIVE_PART_COLLECTION)
        if part_collection is None:
            self.report({"WARNING"}, f"Please Setup Valid Part Collection.")
            return {"CANCELLED"}

        result = ut.separate_as_normal_source_object(self.src_obj_name, self.set_as_normal_source, self.shade_smooth)
        if result == 1:
            self.report({"WARNING"}, f"No vertex is selected")
            return {"CANCELLED"}
        
        self.report({"INFO"}, f"MD Normal transfer")
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_setup_part_collection(bpy.types.Operator):
    """Setup Part Collection for Hard Surface Modeling
    """
    bl_idname = "md_hard.setup_part_collection"
    bl_label = "Setup Part Collection"
    bl_options = {'REGISTER', 'UNDO'}

    part_name: bpy.props.StringProperty(name='Name', default='Part') # type: ignore

    def execute(self, context):
        ut.setup_part_collection(self.part_name)
        return {"FINISHED"}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.activate_init = True
        row.label(icon='COLLECTION_COLOR_01')
        row.prop(self, "part_name", text="")


@register_wrap
class MDHARD_OT_regenerate_collections_under_part(bpy.types.Operator):
    """Regenerate reserved collection under active part collection
    """
    bl_idname = "md_hard.regenerate_collections_under_part"
    bl_label = "MD Regenerate Collection"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(self, context:bpy.types.Context):
        part_collection = getattr(context.scene, ct.ACTIVE_PART_COLLECTION)
        if part_collection is None:
            return False
        return getattr(part_collection, ct.IS_MD_HARDSURF_PART_COLLECTION)
        
    def execute(self, context):
        part_collection = getattr(context.scene, ct.ACTIVE_PART_COLLECTION)
        ut.setup_reserved_part_collection(part_collection)
        self.report({"INFO"}, f"Reserved collection regenerated")
        return {"FINISHED"}
    

@register_wrap
class MDHARD_OT_rename_part_collection(bpy.types.Operator):
    """Regenerate reserved collection under active part collection
    """
    bl_idname = "md_hard.rename_part_collection"
    bl_label = "MD Rename Collection"
    bl_options = {'REGISTER', 'UNDO'}

    new_part_name: bpy.props.StringProperty(
        name="Name",
        description="New part name, if the given name is empty or same, the name will not be changed.") # type: ignore

    @classmethod
    def poll(self, context:bpy.types.Context):
        part_collection = getattr(context.scene, ct.ACTIVE_PART_COLLECTION)
        if part_collection is None:
            return False
        return getattr(part_collection, ct.IS_MD_HARDSURF_PART_COLLECTION)
    
    def invoke(self, context, event):
        wm = context.window_manager
        self.new_part_name = getattr(context.scene, ct.ACTIVE_PART_COLLECTION).name
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        scene = context.scene
        part_collection = getattr(scene, ct.ACTIVE_PART_COLLECTION)
        if part_collection is not None:
            result = ut.rename_part_collection(part_collection, self.new_part_name)

            if result == 1:
                self.report({"WARNING"}, f"Part collection name was not changed: See system console for more detail.")
                return {"CANCELLED"}
        else:
            self.report({"WARNING"}, f"No Active Part Collection is selected")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Part collection renamed")
        return {"FINISHED"}
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.activate_init = True
        row.label(icon='COLLECTION_COLOR_01')
        row.prop(self, "new_part_name", text="")
    


@register_wrap
class MDHARD_OT_set_bevel_weight(bpy.types.Operator):
    """Set bevel weight with prefix and mark as sharp option
    """
    bl_idname = "md_hard.set_bevel_weight"
    bl_label = "MD Set Bevel Weight"
    bl_options = {'REGISTER', 'UNDO'}

    weight: bpy.props.FloatProperty(name='Weight', description='Edge Bevel Weight', subtype='FACTOR', min=0.0, max=1.0) #type: ignore
    modify_sharp: bpy.props.BoolProperty(name='Modify sharp', default=True, description='If True, edge sharp will be automatically modified for DNT') # type: ignore

    @classmethod
    def poll(self, context:bpy.types.Context):
        active_object = bpy.context.active_object
        if active_object is None:
            return False
        else:
            return active_object.type == 'MESH' and active_object.mode == 'EDIT'
        
        
    def execute(self, context):
        ut.set_edge_bevel_weight_with_sharp(self.weight, self.modify_sharp)
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_set_dnt_bevel_modifier_width(bpy.types.Operator):
    """Set bevel modifier width with the option of keeping the visual thickness.
    This is effective only for DNT bevel.
    """
    bl_idname = "md_hard.set_dnt_bevel_modifier_width"
    bl_label = "Set DNT Bevel Modifier Width"
    bl_options = {'REGISTER', 'UNDO'}

    modifier_width: bpy.props.FloatProperty(name='Modifier Width', description='Bevel modifier width ', min=0.0, precision=5, unit='LENGTH') #type: ignore
    keep_visual_width: bpy.props.BoolProperty(name='Keep Visual Width', default=False, description='Bevel Modifier Width.') # type: ignore
    orig_width:float = 0.0

    @classmethod
    def poll(self, context:bpy.types.Context):
        active_object = bpy.context.active_object
        if active_object is None:
            return False
        else:
            return active_object.type == 'MESH'
    

    def invoke(self, context, event):
        wm = context.window_manager
        active_obj = context.active_object
        dnt_bevel_mod = active_obj.modifiers.get(ct.DNT_BEVEL_NAME) 
        if dnt_bevel_mod is None:
            self.report({"WARNING"}, f"'{active_obj.name}' does not have {ct.DNT_BEVEL_NAME} modifier. Create before use this operator.")
            return {"CANCELLED"}
        else:
            self.modifier_width = dnt_bevel_mod.width # use as initial value, this is updated during "Adjust last operator."
            self.orig_width = dnt_bevel_mod.width # this is constant through out "Adunst last operator".
        return wm.invoke_props_popup(self, event)
        

    def execute(self, context):
        ut.set_dnt_bevel_modifier_width(self.modifier_width, self.keep_visual_width, self.orig_width)
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_shade_smooth_anywhere(bpy.types.Operator):
    """shade smooth. it even works in edit mode.
    """
    bl_idname = "md_hard.shade_smooth_anywhere"
    bl_label = "MD Shade Smooth Anywhere"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context:bpy.types.Context):
        return context.active_object is not None
        
    def execute(self, context):
        result = ut.shade_smooth_anywhere()
        if result == 1:
            self.report({"WARNING"}, f"Cannot shade smooth. See system colsole for more detail.")
        return {"FINISHED"}


# TODO: rename to Go To this part.
@register_wrap
class MDHARD_OT_go_to_part(bpy.types.Operator):
    """Go to the Part Collection
    First go to scene which contains specified part, then,
    show and isolate given part collection in a scene. Making this part active
    """
    bl_idname = "md_hard.go_to_part"
    bl_label = "Go To Part"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context:bpy.types.Context):
    #     return context.active_object is not None

    def invoke(self, context, event):
        wm = context.window_manager
        setattr(wm, ct.OPEN_PART_COLLECTION_PLACEHOLDER, None)
        return wm.invoke_props_dialog(self)
        
    def execute(self, context):
        wm = context.window_manager
        part_col = getattr(wm, ct.OPEN_PART_COLLECTION_PLACEHOLDER)
        if part_col is not None:
            ut.go_to_part_collection(part_col)
        else:
            self.report({"WARNING"}, f"Part Collection is not selected.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Show Part Collection")
        return {"FINISHED"}
    

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        row = layout.row()
        row.activate_init = True
        row.prop(wm, ct.OPEN_PART_COLLECTION_PLACEHOLDER, text="")


@register_wrap
class MDHARD_OT_link_part_colleciton_to_scene(bpy.types.Operator):
    """Link Part to this Scene
    This function is similar concept of 'Open File' in text editor.
    """
    bl_idname = "md_hard.link_part_collection_to_scene"
    bl_label = "Link Part Collection to Scene"
    bl_options = {'REGISTER', 'UNDO'}


    def invoke(self, context, event):
        wm = context.window_manager
        setattr(wm, ct.OPEN_PART_COLLECTION_PLACEHOLDER, None)
        return wm.invoke_props_dialog(self)
        
    def execute(self, context):
        wm = context.window_manager
        part_col = getattr(wm, ct.OPEN_PART_COLLECTION_PLACEHOLDER)
        if part_col is not None:
            ut.link_ui_list_collection(part_col)
        else:
            self.report({"WARNING"}, f"Part Collection is not selected.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Part Collection Linked to this scene")
        return {"FINISHED"}
    
    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        row = layout.row()
        row.activate_init = True
        row.prop(wm, ct.OPEN_PART_COLLECTION_PLACEHOLDER, text="")



@register_wrap
class MDHARD_OT_unlink_part_collection_to_scene(bpy.types.Operator):
    """Unlink Part to this Scene
    This function is similar concept of 'Close File' in tex editor.
    """
    bl_idname = "md_hard.unlink_part_collection_to_scene"
    bl_label = "Unlink Part Collection to Scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context:bpy.types.Context):
        # window = bpy.context.area
        return getattr(context.scene, ct.ACTIVE_UILIST_COLLECTION) is not None


        
    def execute(self, context):
        ui_list_collection = getattr(context.scene, ct.ACTIVE_UILIST_COLLECTION)
        ut.unlink_ui_list_collection(ui_list_collection)
        self.report({"INFO"}, f"Unlink part was called, you can still find collection in blend file outliner")
        return {"FINISHED"}
    

@register_wrap
class MDHARD_OT_remove_part_collection(bpy.types.Operator):
    """Remove Part Collection
    TODO: Implement a check function to ensure part collection is not referenced anywhere including external file.
    """
    bl_idname = "md_hard.remove_part_collection"
    bl_label = "Remove Part Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({"WARNING"}, f"Under Development, Nothing is done. : Remove part was called")
        return {"FINISHED"}
    


@register_wrap
class MDHARD_OT_move_scene_collection_ui_list(bpy.types.Operator):
    """Move Scene Collection Active Collection inside UI List
    """
    bl_idname = "md_hard.move_scene_collection_ui_list"
    bl_label = "Move Active Collection in UI List"
    bl_options = {'REGISTER', 'UNDO'}

    move_type: bpy.props.EnumProperty(name='Type', items=[('UP', 'UP', ''), ('DOWN', 'DOWN', '')]) # type: ignore

    @classmethod
    def poll(self, context):
        return len(context.scene.collection.children) > 0
        
    def execute(self, context):
        ut.move_active_collection_in_ui_list(context.scene, self.move_type)
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_part_children_visibility_toggle(bpy.types.Operator):
    """Toggle Visibility of Children Collection Under Part.
    This acts as same with the outliner as possible.
    """
    bl_idname = "md_hard.part_children_visibility_toggle"
    bl_label = "Toggle Visibility of Child Collection Under Part"
    bl_options = {'REGISTER', 'UNDO'}

    collection_prefix: bpy.props.EnumProperty(
            name='Prefix', 
            items=[(prefix, prefix, '') for prefix in ut.PartManager.reserved_collection_prefix]) # type: ignore
    extend:bpy.props.BoolProperty(
        name='Extend',
        description="If True, The visibility will be extended, else, isolate given collection starts with prefix",
        default=False
    ) # type: ignore

    @classmethod
    def poll(self, context):
        return ut.poll_is_ui_list_active_collection_part(self, context)
    
    def invoke(self, context, event):
        shift_pressed = event.shift
        if shift_pressed:
            self.extend = True
        else:
           self.extend = False
        return self.execute(context)


    def execute(self, context):
        sn = context.scene
        part_collection = getattr(sn, ct.ACTIVE_PART_COLLECTION)
        ut.part_children_visibility_toggle(part_collection, self.collection_prefix, extend=self.extend)
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_md_remove_unused_dnt_normal_objects(bpy.types.Operator):
    """Remove unused DNT normal objects in DNT-{Part.name} collection
    """
    bl_idname = "md_hard.md_remove_unused_dnt_normal_objects"
    bl_label = "Remove Unused DNT Normal Objects"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context:bpy.types.Context):
    #     return context.active_object is not None
    unused_dnt_objs = []
    used_dnt_objs = []


    def invoke(self, context, event):
        wm = context.window_manager
        self.unused_dnt_objs = []
        self.used_dnt_objs = []
        dnt_normal_objs = [o for o in context.scene.objects if getattr(o, ct.IS_DNT_NORMAL_OBJECT)]



        scene_mesh_objs = [o for o in context.scene.objects if o.type == 'MESH']
        for o in scene_mesh_objs:
            dnt_normal_mod = o.modifiers.get(ct.DNT_NORMAL_TRANSFER_NAME)
            if dnt_normal_mod is not None:
                self.used_dnt_objs.append(dnt_normal_mod.object)
        
        
        self.unused_dnt_objs = list(set(dnt_normal_objs) - set(self.used_dnt_objs))
        return wm.invoke_props_dialog(self)
        
    def execute(self, context):
        ut.remove_unused_dnt_normal_object(self.unused_dnt_objs)
        self.report({"INFO"}, "Remove Unused DNT Normal Objects Excecuted")
        return {"FINISHED"}
    
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Remove Following Objects.")
        for o in self.unused_dnt_objs:
            try:
                layout.label(text=f"{o.name}", icon="OBJECT_DATA")
            except ReferenceError:
                print("Already cleanedup unused DNT Normal Source")

        

@register_wrap
class MDHARD_OT_face_strength_material_override_toggle(bpy.types.Operator):
    """Toggle Face Strength Material Override"""
    bl_idname = "md_hard.face_strength_material_override_toggle"
    bl_label = "Toggle Face Strength Material Override"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        is_fs_mat_override = getattr(context.scene, ct.IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE)
        
        setattr(context.scene, ct.IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE, not is_fs_mat_override)


        return {"FINISHED"}


@register_wrap
class MDHARD_OT_fix_all_part_render_viewport_visibilities(bpy.types.Operator):
    """Fix Render and Viewport Visibility of All Part collection."""
    bl_idname = "md_hard.fix_all_part_render_viewport_visibilities"
    bl_label = "Fix Render and Viewport Visibility of All Part collections."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ut.fix_part_render_and_viewport_visibilities()
        self.report({"INFO"}, f"Fix Render and Viewport Visibility of All Part collections called.")
        return {"FINISHED"}



#-------------------------------------------------------------------------------
# Navigations
#-------------------------------------------------------------------------------

@register_wrap
class MDHARD_OT_go_to_source_collection(bpy.types.Operator):
    """Go To source of this collection instance.
    It can be used both internal / external collection.
    """
    bl_idname = "md_hard.go_to_source_collection"
    bl_label = "Go To Source Collection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return active_obj is not None and (active_obj.instance_collection is not None)

    def execute(self, context):
        ins_obj = context.active_object
        result = nav.Navigation.go_to_source_collection(ins_obj)
        if result == 1:
            self.report({"WARNING"}, f"Save Before using this operation")

            return {"CANCELLED"}
        self.report({"INFO"}, f"Go To Source Collection Called")
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_navigate_forward(bpy.types.Operator):
    """Navigate Forward.
    This is similar concept to navigation in the code editor.
    You can jump forward to next history which is generated by go_to_source_collection
    """
    bl_idname = "md_hard.navigate_forward"
    bl_label = "MD Navigate Forward"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def execute(self, context):
        result = nav.Navigation.nav_forward()
        if result == 1:
            self.report({"WARNING"}, f"No More Forward Navigation History.")
            return {"CANCELLED"}
        elif result == 2:
            self.report({"WARNING"}, f"History not found, removed. Abort Forward Navigation.")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Navigation Forward")
        return {"FINISHED"}
    

@register_wrap
class MDHARD_OT_navigate_back(bpy.types.Operator):
    """Navigate Back.
    This is similar concept to navigation in the code editor.
    You can jump back to previous history which is generated by go_to_source_collection
    """
    bl_idname = "md_hard.navigate_back"
    bl_label = "MD Navigate Forward"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def execute(self, context):
        result = nav.Navigation.nav_back()
        if result == 1:
            self.report({"WARNING"}, f"No More Backward Navigation History.")
            return {"CANCELLED"}
        elif result == 2:
            self.report({"WARNING"}, f"History not found, removed. Abort Backward Navigation.")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Navigation Backward")
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_open_project(bpy.types.Operator):
    """Open Project
    This is similar concept to 'Open Folder' in VSCode or setting working directory
    in text editor

    The Concept and specification:
        -Only one asset folder is opened as local asset folder
        -You can load multiple asset library.
        -When you want to open/close local asset folder, you have to explicitly call open or close (like VSCode).
        -When open local asset folder, it will be loaded as standard asset library.
        -If Addon loads the asset folder, then this is the local asset folder and will be unloaded on close folder.
        -If Blender loads the asset folder, then this will stay as asset when close local asset folder.
        -closing/opening blender instance won't close/open local asset folder.
    """
    bl_idname = "md_hard.open_project"
    bl_label = "MD Open Project"

    directory: bpy.props.StringProperty( # must be the name of 'directory'. This is required by wm.fileselect_add()
        name='directory', 
        default=str(Path.home()),
        subtype='DIR_PATH') #type: ignore
    
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        mdp.open_project(proj_root_dir=self.directory)
        self.report({"INFO"}, f"Opened Project Folder")
        return {"FINISHED"}
    

@register_wrap
class MDHARD_OT_close_project(bpy.types.Operator):
    """Close Local Asset Folder
    This is similar concept to 'Close Folder' in VSCode
    """
    bl_idname = "md_hard.close_project"
    bl_label = "MD Close Project"

    @classmethod
    def poll(cls, context):
        wm = bpy.context.window_manager
        return getattr(wm, ct.MD_PROJECT_CWD) != ''

    def execute(self, context):
        mdp.close_project()
        self.report({"INFO"}, f"Closed Project Folder")
        return {"FINISHED"}
    



@register_wrap
class MDHARD_OT_rescent_local_asset_folder(bpy.types.Operator):
    """Open Recent Local Asset Folder
    This is similar concept to 'Open Recent Folder' in VSCode or setting working directory
    in text editor
    """
    bl_idname = "md_hard.recent_local_asset_folder"
    bl_label = "MD Recent Local Asset Folder"

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def execute(self, context):
        # result = 
        # if result == 1:
            # self.report({"WARNING"}, f"Save on disk before using this operation")

            # return {"CANCELLED"}
        self.report({"INFO"}, f"Open Recent Local Asset Folder")
        return {"FINISHED"}
    

@register_wrap
class MDHARD_OT_harpoon_go_to_file_slot(bpy.types.Operator):
    """Harpoon.
    This is similar concept to Neovim Harpoon. The file hopper.
    """
    bl_idname = "md_hard.harpoon_go_to_file_slot"
    bl_label = "MD Harpoon Go To File Slot"

    index: bpy.props.IntProperty(name='harpoon_index', default=0, min=0) # type: ignore

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return getattr(wm, ct.MD_PROJECT_CWD) != ''

    def execute(self, context):
        result = mdp.harpoon_go_to_file_slot(self.index)
        # result = 
        if result == 1:
            self.report({"WARNING"}, f"Harpoon Failed to open slot {self.index}")
            return {"CANCELLED"}
        elif result == 2:
            self.report({"WARNING"}, f"Harpoon: Save before operation")
            return {"CANCELLED"}

        
        self.report({"INFO"}, f"MD Harpoon: Go To slot {self.index}")
        return {"FINISHED"}



@register_wrap
class MDHARD_OT_harpoon_add_slot(bpy.types.Operator):
    """Harpoon.
    -LMB: Add this file. 
    -Shift LMB: Add Empty, 
    -Ctrl LMB: Search in file browser
    """
    bl_idname = "md_hard.harpoon_add_slot"
    bl_label = "MD Harpoon Add Slot"

    filepath: bpy.props.StringProperty(name='filepath', default=str(Path.home()), subtype='FILE_PATH') # type: ignore
    filter_glob: bpy.props.StringProperty(
        default="*.blend",
        options={'HIDDEN'},
        )#type: ignore

    def invoke(self, context, event):
        if event.shift and not event.ctrl:
            self.filepath=''
            return self.execute(context)
        elif event.ctrl and not event.shift:
            cwd = mdp.get_cwd()
            if cwd is not None:
                self.filepath = cwd
            wm = context.window_manager
            wm.fileselect_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.filepath = bpy.data.filepath
            return self.execute(context)

    def execute(self, context):
        mdp.harpoon_add_file_slot(self.filepath)
        self.report({"INFO"}, f"MD Harpoon: add_slot {self.filepath}")
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_harpoon_remove_slot(bpy.types.Operator):
    """Harpoon.
    -LMB: Remove slot, 
    
    """
    bl_idname = "md_hard.harpoon_remove_slot"
    bl_label = "MD Harpoon Remove Slot"

    def execute(self, context):
        mdp.harpoon_remove_file_slot()
        self.report({"INFO"}, f"MD Harpoon: remove_slot")
        return {"FINISHED"}


@register_wrap
class MDHARD_OT_harpoon_assign_to_slot(bpy.types.Operator):
    """Harpoon.
    -LMB: Assign This File to Slot.
    -Ctrl LMB: Invoke File Browser
    -Shift LMB: Clear name and filepath.
    """
    bl_idname = "md_hard.harpoon_assign_to_slot"
    bl_label = "MD Harpoon Assign To Slot"

    filepath: bpy.props.StringProperty(name='filepath', default=str(Path.home()), subtype='FILE_PATH') # type: ignore
    filter_glob: bpy.props.StringProperty(
        default="*.blend",
        options={'HIDDEN'},
        )#type: ignore
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return len(getattr(wm, ct.MD_HARPOON_UILIST_COLLECTION)) > 0

    def invoke(self, context, event):
        if event.shift and not event.ctrl:
            self.filepath = ''
            return self.execute(context)
        elif event.ctrl and not event.shift:
            cwd = mdp.get_cwd()
            if cwd is not None:
                self.filepath = cwd
            wm = context.window_manager
            wm.fileselect_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.filepath = bpy.data.filepath
            return self.execute(context)


    def execute(self, context):
        mdp.harpoon_assign_to_slot(self.filepath)
        self.report({"INFO"}, f"MD Harpoon: assign to slot")
        return {"FINISHED"}



@register_wrap
class MDHARD_OT_harpoon_move_ui_list(bpy.types.Operator):
    """Harpoon.
    """
    bl_idname = "md_hard.harpoon_move_ui_list"
    bl_label = "MD Harpoon Move Slot"

    move_type: bpy.props.EnumProperty(name='Type', items=[('UP', 'UP', ''), ('DOWN', 'DOWN', '')]) # type: ignore

    def execute(self, context):
        mdp.harpoon_move_file_slot(self.move_type)
        return {"FINISHED"}
    






@register_wrap
class MDHARD_OT_open_file_in_project(bpy.types.Operator):
    """Open File in Project.
    - If Project is Opened Popup search menu
    - If Project is not Opened, Open with file browser
    - If Current File is saved on disk, then automatically saved on opening new file.
    - If Current File is not saved on disk, save popup will be shown before opening new file.
    """
    bl_idname = "md_hard.open_file_in_project"
    bl_label = "MD Open File in Project"
    bl_property = "filepath"

    filepath: bpy.props.EnumProperty(name='File Path', items=mdp.search_file_in_project_callback) # type: ignore

    def invoke(self, context, event):
        wm = context.window_manager
        if (bpy.data.is_saved == False) and (bpy.data.is_dirty):
            self.report({"WARNING"}, f"Save To Disk Before Opening File")
            return {'CANCELLED'}
        
        if mdp.get_cwd() is None:
            self.report({"WARNING"}, f"MD Project not opened, fallback to default wm.open_mainfile()")
            nav.Navigation.add_nav_history()
            return bpy.ops.wm.open_mainfile('INVOKE_DEFAULT')
        else:
            wm.invoke_search_popup(self)
            return {'FINISHED'}
    
    def execute(self, context):
        print(f"filepath = '{self.filepath}'")
        nav.Navigation.add_nav_history()
        try:
            bpy.ops.wm.open_mainfile(filepath=self.filepath)
            self.report({"INFO"}, f"Open file in project")
        except Exception as e:
            print(f"Failed to open file '{self.filepath}': {e}")
            self.report({"WARNING"}, "Failed to open file. See system console for more detail.")

        return {"FINISHED"}
    
    



@register_wrap
class MDHARD_OT_test_x(bpy.types.Operator):
    """Test"""
    bl_idname = "md_hard.test_x"
    bl_label = "Test X"
    bl_options = {'REGISTER', 'UNDO'}

    x: bpy.props.FloatProperty(name='x', default=0.0) #type: ignore

    # @classmethod
    # def poll(self, context):
    #     return True

    # def invoke(self, context, event):

    #         shift_pressed = event.shift

    #     if shift_pressed:
    #         self.exclude_active = True
    #     else:
    #         self.exclude_active = False

    #     return self.execute(context)

    def execute(self, context):
        # objs = get_mesh_object_in_collection(getattr(context.scene, ct.TARGET_COLLECTION), recursive=True)
        # pprint(objs)
        # pprint(get_unique_key_block_name_in_collection(getattr(context.scene, ct.TARGET_COLLECTION), recursive=True))
        bpy.data.materials.new("new1")
        print("material created")
        self.report({"INFO"}, f"self: print x={self.x}: MD Hard surface utils 'test' X called")

        return {"FINISHED"}
        # return {"CANCELLED"}

