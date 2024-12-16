bl_info = {
    "name": "SCO ButtObjects",
    "author": "BEAST_of_BURDEN ",
    "version": (2, 0),
    "blender": (4, 0, 0),
    "location": "3D View > Sidebar > Item > Object Mode",
    "description": "Align Objects to a Active Object or 3D Cursor based on bounds",
    "category": "Object",
}

import bpy
from . import sco_buttobjects


def register():
    sco_buttobjects.register()


def unregister():
    sco_buttobjects.unregister()
