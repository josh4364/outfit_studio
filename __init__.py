bl_info = {
    "name": "Outfit Studio",
    "author": "Josh",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Outfit Studio",
    "description": "Bulk export variants of character models with different outfits",
    "category": "Import-Export",
}

import bpy
from . import properties, operators, ui

def register():
    properties.register()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
