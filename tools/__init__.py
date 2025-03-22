if "bpy" not in locals():
    import bpy
    from . import constants 
    from . import utils
    from . import navigation
    from . import md_project
    from . import operators
    from . import ui

else:
    import importlib
    importlib.reload(constants)
    importlib.reload(utils)
    importlib.reload(navigation)
    importlib.reload(md_project)
    importlib.reload(operators)
    importlib.reload(ui)
