import bpy
from ..setup_tools.register import register_wrap
from . import constants as ct
from . import operators as ot
from . import utils as ut


@register_wrap
class MDHARD_PT_md_hard(bpy.types.Panel):
    """Panel for MD hard surface modeling utils
    """
    bl_idname = "MDHARD_PT_md_hard" 
    bl_label = "Hard Surface Utils"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MD Hard" # tab name

    def draw(self, context):
        layout = self.layout
        current_project = getattr(context.window_manager, ct.MD_PROJECT_CWD)
        layout.label(text=f"Project: {current_project}" if current_project!='' else "Project: Not Opened", icon='FILE_FOLDER')
        sn = context.scene
        row = layout.row(align=True)
        row.scale_y = 1.7
        split = row.split(factor=0.8, align=True)
        split.operator(ot.MDHARD_OT_setup_part_collection.bl_idname, text="Setup Part", icon="COLLECTION_COLOR_01")
        split.operator(ot.MDHARD_OT_regenerate_collections_under_part.bl_idname, text="", icon="FILE_REFRESH")
        row = layout.row()
        row.operator(ot.MDHARD_OT_rename_part_collection.bl_idname, text="Rename Part")
        row.operator(ot.MDHARD_OT_fix_part_render_viewport_visibilities.bl_idname, text="Fix Visibility")

        layout.separator(factor=2.0)
        layout.prop(bpy.context.scene, ct.IS_MD_FACE_STRENGTH_MATERIAL_OVERRIDE, text="Face Strength Override", icon="MATERIAL", expand=True)

        layout.separator()
        active_uilist_collection = getattr(sn, ct.ACTIVE_UILIST_COLLECTION)
        active_collection_name = ''
        if active_uilist_collection is not None:
           active_collection_name = active_uilist_collection.name
            
        # UIList
        row = layout.row()
        row.label(text=f"Active: {active_collection_name}")
        if active_uilist_collection is not None:
            row.prop(active_uilist_collection, ct.IS_MD_HARDSURF_SUB_PART_COLLECTION, text="Sub Part")
            if getattr(active_uilist_collection, ct.IS_MD_HARDSURF_PART_COLLECTION) == False:
                row.enabled = False
                

        
        row = layout.row()
        row.template_list(MDHARD_UL_scene_part.__name__, "", sn.collection, "children", sn, ct.SCENE_COLLECTION_CHILD_INDEX)
        col = row.column(align=True)
        col.operator(ot.MDHARD_OT_move_scene_collection_ui_list.bl_idname, text="", icon='TRIA_UP').move_type = 'UP'
        col.operator(ot.MDHARD_OT_move_scene_collection_ui_list.bl_idname, text="", icon='TRIA_DOWN').move_type = 'DOWN'
        col.separator()

        row = layout.row(align=True)
        row.operator(ot.MDHARD_OT_link_part_colleciton_to_scene.bl_idname, text="Link", icon='LINKED')
        row.operator(ot.MDHARD_OT_unlink_part_collection_to_scene.bl_idname, text="Unlink", icon='UNLINKED')
        
        layout.separator()

        row = layout.row(align=True)
        row.scale_y = 1.5

        current_uilist_scene_collection = getattr(sn, ct.ACTIVE_UILIST_COLLECTION) # This scene property is both return part or non part collection.
        if current_uilist_scene_collection is not None:
            visibilities = ut.PartManager.get_collection_visibility_dict(part_collection=current_uilist_scene_collection)
            icon_set = lambda prefix: "HIDE_OFF" if visibilities.get(prefix, False) else "HIDE_ON"
            row.operator(ot.MDHARD_OT_part_children_visibility_toggle.bl_idname, text="F-", icon=icon_set(ct.FINAL_COLLECTION)).collection_prefix = ct.FINAL_COLLECTION
            row.operator(ot.MDHARD_OT_part_children_visibility_toggle.bl_idname, text="DEP-", icon=icon_set(ct.DEP_COLLECTION)).collection_prefix = ct.DEP_COLLECTION
            row.operator(ot.MDHARD_OT_part_children_visibility_toggle.bl_idname, text="D-", icon=icon_set(ct.DESIGN_COLLECTION)).collection_prefix = ct.DESIGN_COLLECTION
            row.operator(ot.MDHARD_OT_part_children_visibility_toggle.bl_idname, text="NORMAL-", icon=icon_set(ct.NORMAL_COLLECTION)).collection_prefix = ct.NORMAL_COLLECTION

            if getattr(current_uilist_scene_collection, ct.IS_MD_HARDSURF_PART_COLLECTION):
                row.enabled = True
            else:
                row.enabled = False

        return
    
    
@register_wrap
class MDHARD_PT_md_normal_transfer(bpy.types.Panel):
    """Panel for normal transfer
    """
    bl_idname = "MDHARD_PT_md_normal_transfer" 
    bl_label = "Part Operators"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MD Hard" # tab name

    def draw(self, context):
        active_obj = context.active_object
        part_collection = getattr(bpy.context.scene, ct.ACTIVE_PART_COLLECTION)

        layout = self.layout
        col = layout.column(heading="Normal Transfer")

        if part_collection is not None:
            col.prop(part_collection, ct.NORMAL_TRANSFER_SRC_OBJ_PER_COLLECTION, text="Source")
            row = col.row(align=True)
            row.scale_y = 1.7
            split = row.split(factor=0.2)
            split.operator(ot.MDHARD_OT_separate_normal_source.bl_idname, text="", icon="MOD_EXPLODE")
            split.operator(ot.MDHARD_OT_normal_transfer.bl_idname, text="Normal Transfer", icon="MOD_DATA_TRANSFER")

        else:
            col.label(text=f"Active Part: None")

        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.7
        row.operator(ot.MDHARD_OT_sync_dnt.bl_idname, text="Sync DNT", icon="FILE_REFRESH")    

        return



#-------------------------------------------------------------------------------
# Part UIList
#-------------------------------------------------------------------------------
@register_wrap
class MDHARD_UL_scene_part(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            part_col = item # scene.collection.children ()
            layout.label(
                text=part_col.name,
                icon="COLLECTION_COLOR_01" if getattr(part_col, ct.IS_MD_HARDSURF_PART_COLLECTION) else "OUTLINER_COLLECTION")

            # split = layout.split(factor=0.5, align=False)
            # split.prop(item, 'name', text="", emboss=False)
            # row = split.row(align = True)
            # row.emboss = 'NONE_OR_STATUS'

            # row.prop(item, 'lock_shape', text="", emboss=False, icon='DECORATE_LOCKED' if item.lock_shape else 'DECORATE_UNLOCKED')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")



#-------------------------------------------------------------------------------
# Harpoon
#-------------------------------------------------------------------------------
@register_wrap
class MDHARD_UL_Harpoon(bpy.types.UIList):
    def draw_item(self, context, layout:bpy.types.UILayout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            harpoon_element = item # scene.collection.children ()
            row = layout.row()
            if harpoon_element.filepath == '':
                row.enabled = False
            else:
                row.enabled = True
            
            split = row.split(factor=0.9)
            split.prop(harpoon_element, 'name', text="", emboss=False)
            split.operator(ot.MDHARD_OT_harpoon_go_to_file_slot.bl_idname, text='', icon='FILE_BLEND', emboss=False).index = index

            
            
                # icon="COLLECTION_COLOR_01" if getattr(part_col, ct.IS_MD_HARDSURF_PART_COLLECTION) else "OUTLINER_COLLECTION")

            # split = layout.split(factor=0.5, align=False)
            # split.prop(item, 'name', text="", emboss=False)
            # row = split.row(align = True)
            # row.emboss = 'NONE_OR_STATUS'

            # row.prop(item, 'lock_shape', text="", emboss=False, icon='DECORATE_LOCKED' if item.lock_shape else 'DECORATE_UNLOCKED')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")

@register_wrap
class MDHARD_PT_harpoon(bpy.types.Panel):
    """Panel for normal transfer
    """
    bl_idname = "MDHARD_PT_harpoon" 
    bl_label = "Harpoon"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MD Hard" # tab name

    def draw(self, context):
        wm = context.window_manager

        layout = self.layout
        if getattr(wm, ct.MD_PROJECT_CWD) == '':
            layout.enabled = False
        else:
            layout.enabled = True

        row = layout.row()
        row.template_list(MDHARD_UL_Harpoon.__name__, "", wm, ct.MD_HARPOON_UILIST_COLLECTION, wm, ct.MD_HARPOON_INDEX)
        col = row.column(align=True)
        col.operator(ot.MDHARD_OT_harpoon_move_ui_list.bl_idname, text="", icon='TRIA_UP').move_type = 'UP'
        col.operator(ot.MDHARD_OT_harpoon_move_ui_list.bl_idname, text="", icon='TRIA_DOWN').move_type = 'DOWN'
        col.separator()
        col.operator(ot.MDHARD_OT_harpoon_add_slot.bl_idname, text="", icon='ADD')
        col.operator(ot.MDHARD_OT_harpoon_remove_slot.bl_idname, text="", icon='REMOVE')

        row = layout.row()
        row.operator(ot.MDHARD_OT_harpoon_assign_to_slot.bl_idname, 
                     text="Assign To Slot", 
                     icon='FILE_BLEND')

            
        

#-------------------------------------------------------------------------------
# Menu
#-------------------------------------------------------------------------------

@register_wrap
class MDHARD_MT_md_hard_surface(bpy.types.Menu):
    bl_label = "MD Hard Surface Menu"
    bl_idname = "MDHARD_MT_md_hard_surface"

    def draw(self, context):
        layout = self.layout
        try:
            if context.area.type == 'VIEW_3D':
                layout.menu(MDHARD_MT_face_strength_submenu.bl_idname, text="F Face Strength...", icon="FACESEL")
                layout.menu(MDHARD_MT_edge_bevel_weight_submenu.bl_idname, text="B Bevel Weight...", icon="MOD_BEVEL")
                layout.menu(MDHARD_MT_toggle_submenu.bl_idname, text="T Toggle Vibility...")
                layout.operator(ot.MDHARD_OT_shade_smooth_anywhere.bl_idname, text="S Shade Smooth Anywhere")
            layout.menu(MDHARD_MT_project_submenu.bl_idname, text="W Project...")

            col = layout.column()
            col.operator_context = 'INVOKE_DEFAULT'
            col.operator(ot.MDHARD_OT_open_file_in_project.bl_idname, text="P Open File in Project")
            col.operator(ot.MDHARD_OT_link_part.bl_idname, text="A Link Part")
        except AttributeError:
            # Exception when you have not selected anything.
            # When you have not selected mesh, you cannot check the line
            # "context.object.type"  but this error doesn't do anything so ignore it.
            pass


#-------------------------------------------------------------------------------
# Sub Menu
#-------------------------------------------------------------------------------
@register_wrap
class MDHARD_MT_face_strength_submenu(bpy.types.Menu):
    bl_label = "Face Strength Menu"
    bl_idname = "MDHARD_MT_face_strength_submenu"

    def draw(self, context):
        layout = self.layout
        try:
            layout.operator(ot.MDHARD_OT_face_strength_material_override_toggle.bl_idname, text="F Toggle Material Override", icon="MATERIAL")
            if context.object.type == 'MESH':
                if context.active_object.mode=='EDIT':
                    ops_face_weak = layout.operator("mesh.mod_weighted_strength", text="W Weak")
                    ops_face_weak.set = True
                    ops_face_weak.face_strength = 'WEAK'

                    ops_face_medium = layout.operator("mesh.mod_weighted_strength", text="M Medium")
                    ops_face_medium.set = True
                    ops_face_medium.face_strength = 'MEDIUM'

                    ops_face_strong = layout.operator("mesh.mod_weighted_strength", text="S Strong")
                    ops_face_strong.set = True
                    ops_face_strong.face_strength = 'STRONG'

        except AttributeError:
            pass


@register_wrap
class MDHARD_MT_edge_bevel_weight_submenu(bpy.types.Menu):
    bl_label = "Edge Bevel Weight Menu"
    bl_idname = "MDHARD_MT_edge_bevel_weight_submenu"

    def draw(self, context):
        layout = self.layout
        try:
            if context.object.type == 'MESH':
                layout.operator(ot.MDHARD_OT_set_dnt_bevel_modifier_width.bl_idname, text="W Set DNT Bevel Modifier Width")
                if context.active_object.mode=='EDIT':
                    layout.separator()
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="Z set 0.00").weight = 0.0
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="A set 0.125").weight = 0.125
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="S set 0.25").weight = 0.25
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="D set 0.50").weight = 0.5
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="F set 0.75").weight = 0.75
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="G set 1.00").weight = 1.0
                    layout.operator(ot.MDHARD_OT_set_bevel_weight.bl_idname, text="B Set Previous")

        except AttributeError:
            pass

      
@register_wrap
class MDHARD_MT_toggle_submenu(bpy.types.Menu):
    bl_label = "Hard Surface Toggle Menu"
    bl_idname = "MDHARD_MT_toggle_submenu"

    def draw(self, context):
        layout = self.layout
        try:
            if context.object.type == 'MESH':
                layout.operator(ot.MDHARD_OT_toggle_dnt_visibility.bl_idname, text="T Toggle DNT visibility")
                
        except AttributeError:
            pass


@register_wrap
class MDHARD_MT_project_submenu(bpy.types.Menu):
    bl_label = "MD Project Submenu"
    bl_idname = "MDHARD_MT_project_submenu"

    def draw(self, context):
        layout = self.layout
        try:
            if context.area.type == 'VIEW_3D':
                layout.operator(ot.MDHARD_OT_go_to_part.bl_idname, text="G Go To This Part")
                layout.operator(ot.MDHARD_OT_go_to_source_collection.bl_idname, text="S Go To Source", icon="OUTLINER_COLLECTION")
                # layout.operator(ot.MDHARD_OT_navigate_forward.bl_idname, text="F Navigate Forward", icon="LOOP_FORWARDS")
                # layout.operator(ot.MDHARD_OT_navigate_back.bl_idname, text="B Navigate Backward", icon="LOOP_BACK") # TODO create better keymap for nav back/forward
                layout.operator(ot.MDHARD_OT_open_project.bl_idname, text="O Open Project")
                layout.operator(ot.MDHARD_OT_close_project.bl_idname, text="C Close Project")
            # if context.area.type == 'OUTLINER':
            #     layout.operator(ot.MDHARD_OT_md_unlink_part.bl_idname, text="U Unlink This Part Collection")
            #     # if context.object.type == 'MESH':

                
            
        except AttributeError:
            pass
