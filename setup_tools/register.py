import bpy

__bl_classes = []
__extend_menu = []
__props = []

def register_wrap(cls):
    __bl_classes.append(cls)
    return cls


def register_extend_menu(menu, func):
    """Extend existing menu cleanly (un)registering.
    Example usage:
    extend_menu(bpy.types.NODE_MT_context_menu, ui_func)
    """
    __extend_menu.append((menu, func))
    return


def register_prop(obj, prop_name, prop):
    """Register properties cleanly.
    Example usage:
    register_prop(bpy.type.Object, 'boolean', bpy.props.PointerProperty(type=OBJECT_PG_booleans, name="Booleans"))
    """
    __props.append((obj, prop_name, prop))
    return
