import bpy
from ..setup_tools.register import register_wrap
from . import utils as ut
from . import constants as ct
from pprint import pprint



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
        part_collection = ut.get_parent_part_collection(obj=target_obj, fallback=None)
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
        part_collection = ut.get_parent_part_collection(obj=target_obj, fallback=None)
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
        layout.use_property_split = True
        
        col = layout.column()
        col.prop(self, "part_name")


@register_wrap
class MDHARD_OT_regenerate_collections_under_part(bpy.types.Operator):
    """Regenerate reserved collection under active part collection
    """
    bl_idname = "md_hard.regenerate_collections_under_part"
    bl_label = "MD Regenerate Collection"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(self, context:bpy.types.Context):
        return getattr(context.collection, ct.IS_MD_HARDSURF_PART_COLLECTION)
        
    def execute(self, context):
        ut.regenerate_reserved_collection_under_part()
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
        name="New Part Name",
        description="New part name, if the given name is empty or same, the name will not be changed.") # type: ignore

    @classmethod
    def poll(self, context:bpy.types.Context):
        return getattr(context.collection, ct.IS_MD_HARDSURF_PART_COLLECTION)
    
    def invoke(self, context, event):
        wm = context.window_manager
        self.new_part_name = context.collection.name
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        result = ut.rename_part_collection(context.collection, self.new_part_name)

        if result == 1:
            self.report({"WARNING"}, f"Part collection name was not changed: See system console for more detail.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Part collection renamed")
        return {"FINISHED"}
    


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
        return wm.invoke_props_dialog(self)
        

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
        ut.shade_smooth_anywhere()
        return {"FINISHED"}


# TODO: rename to Go To this part.
@register_wrap
class MDHARD_OT_md_show_only_this_part(bpy.types.Operator):
    """Show and Isolate given part collection in a scene.
    """
    bl_idname = "md_hard.md_show_only_this_part"
    bl_label = "Show Only This Part"
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
            ut.show_part_collection(part_col)
        else:
            self.report({"WARNING"}, f"Part Collection is not selected.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Show Part Collection")
        return {"FINISHED"}
    

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout

        layout.prop(wm, ct.OPEN_PART_COLLECTION_PLACEHOLDER, text="Part Collection")


@register_wrap
class MDHARD_OT_link_part_colleciton_to_scene(bpy.types.Operator):
    """Link Part to this Scene
    This function is similar concept of 'Open File' in tex editor.
    """
    bl_idname = "md_hard.link_part_collection_to_scene"
    bl_label = "Link Part Collection to Scene"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context:bpy.types.Context):
    #     # window = bpy.context.area
    #     return bpy.context.area.type == 'OUTLINER' 

    def invoke(self, context, event):
        wm = context.window_manager
        setattr(wm, ct.OPEN_PART_COLLECTION_PLACEHOLDER, None)
        return wm.invoke_props_dialog(self)
        
    def execute(self, context):
        # ut.unlink_part_collection()
        
        self.report({"INFO"}, f"Link part was called")


        return {"FINISHED"}      


@register_wrap
class MDHARD_OT_unlink_part_collection_to_scene(bpy.types.Operator):
    """Unlink Part to this Scene
    This function is similar concept of 'Close File' in tex editor.
    """
    bl_idname = "md_hard.unlink_part_collection_to_scene"
    bl_label = "Unlink Part Collection to Scene"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context:bpy.types.Context):
    #     # window = bpy.context.area
    #     return bpy.context.area.type == 'OUTLINER' 

        
    def execute(self, context):
        self.report({"INFO"}, f"Unlink part was called")
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

