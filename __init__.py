if "bpy" not in locals():
    import bpy
    from . import setup_tools
    from . import tools
    from . import props
    from . import prefs
    from . import myblendrc_utils

else:
    import importlib
    importlib.reload(setup_tools)
    importlib.reload(tools)
    importlib.reload(props)
    importlib.reload(prefs)
    importlib.reload(myblendrc_utils)
    



def register():
    for cls in setup_tools.register.__bl_classes:
        bpy.utils.register_class(cls)

    for menu, f in setup_tools.register.__extend_menu:
        menu.append(f)

    for obj, name, prop in setup_tools.register.__props:
        setattr(obj, name, prop)

    for register_func, _ in setup_tools.register.__other_register:
        register_func()

def unregister():
    for cls in setup_tools.register.__bl_classes:
        bpy.utils.unregister_class(cls)

    for menu, f in setup_tools.register.__extend_menu:
        menu.remove(f)

    for obj, name, _ in setup_tools.register.__props:
        delattr(obj, name)

    for _, unregister_func in setup_tools.register.__other_register:
        unregister_func()

if __name__ == '__main__':
    register()
