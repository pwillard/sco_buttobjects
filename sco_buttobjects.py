# Blender Addon: SCO ButtObjects
# Version 2.0.10
# Author: BEAST_of_BURDEN (sun503@yahoo.com)

# Support Page: https://github.com/pwillard/sco_buttobjects/discussions

# This script is licensed under the GNU General Public License v3.
# See the LICENSE file for more details.

# This script incorporates code from [Distribute/BlenderBob]
# Originally licensed under GPLv3: [https://extensions.blender.org/add-ons/distribute/]
# Modifications and additions by [SCO ButtObjects/BEAST_of_BURDEN]
# Incorporated "Distribute" function into this script - changed labels and buttons.

import bpy
import bmesh
from mathutils import Vector
from bpy.props import EnumProperty, BoolProperty, FloatVectorProperty, PointerProperty
from bpy.types import PropertyGroup


def get_obj_bounds(obj):
    b = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = [min(v[i] for v in b) for i in range(3)]
    mx = [max(v[i] for v in b) for i in range(3)]
    ct = [(mn[i] + mx[i]) / 2 for i in range(3)]
    return mn, mx, ct


class SCO_Props(PropertyGroup):
    SCO_ucur: BoolProperty(
        name="Use Cursor",
        description="Align to 3D Cursor",
        default=False,
    )
    SCO_aorig: BoolProperty(
        name="Align to Origin",
        description="Align to Object Origin",
        default=False,
    )
    SCO_cpos: FloatVectorProperty(
        name="Cursor Pos Saved",
        description="Saved position of 3D cursor",
        default=(0.0, 0.0, 0.0)
    )
    SCO_lext: EnumProperty(
        name="Last Extent",
        items=[
            ('MIN', "Min", "Align to Minimum Extent"),
            ('CTR', "Ctr", "Align to Center Extent"),
            ('MAX', "Max", "Align to Maximum Extent"),
        ],
        default='CTR'
    )
    SCO_bpos: EnumProperty(
        name="Bounds Position",
        items=[
            ('INSIDE', "Inside", "Align inside the active object's bounds"),
            ('OUTSIDE', "Outside", "Align outside the active object's bounds"),
        ],
        default='INSIDE'
    )


def align_objs(context, axis, aln_min, insd, use_ctr, use_cur, aorig, cpos):
    scene = context.scene
    pg = scene.SCO_pg
    sel = context.selected_objects
    act = context.active_object

    if aorig:
        if not act:
            return
        orig_pos = act.location[axis]
        for o in sel:
            if o == act:
                continue
            o.location[axis] = orig_pos
        context.view_layer.update()
        return

    if use_cur:
        cur_pos = scene.cursor.location[:]
        tgt = cur_pos[axis]
    else:
        if not act:
            return
        amin, amax, actr = get_obj_bounds(act)
        lext = pg.SCO_lext
        if lext == "MIN":
            tgt = amin[axis]
        elif lext == "MAX":
            tgt = amax[axis]
        else:
            tgt = actr[axis]

    for o in sel:
        if not use_cur and o == act:
            continue
        omin, omax, octr = get_obj_bounds(o)
        lext = pg.SCO_lext

        if insd:
            if lext == "MIN":
                off = tgt - omin[axis]
            elif lext == "MAX":
                off = tgt - omax[axis]
            else:
                off = tgt - octr[axis]
        else:
            if lext == "MIN":
                off = tgt - omax[axis]
            elif lext == "MAX":
                off = tgt - omin[axis]
            else:
                off = tgt - octr[axis]

        o.location[axis] += off

    context.view_layer.update()


class SCO_OT_AlignObj(bpy.types.Operator):
    bl_idname = "sco.alignobj"
    bl_label = "Align Objects"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=[
            ('0', "X", ""),
            ('1', "Y", ""),
            ('2', "Z", ""),
        ],
        default='0'
    )

    def execute(self, context):
        scene = context.scene
        pg = scene.SCO_pg

        lext = pg.SCO_lext
        use_center = lext == "CTR"
        align_to_min = lext == "MIN"

        align_objs(
            context,
            int(self.axis),
            align_to_min,
            pg.SCO_bpos == "INSIDE",
            use_center,
            pg.SCO_ucur,
            pg.SCO_aorig,
            pg.SCO_cpos
        )

        return {'FINISHED'}


class SCO_OT_CopyScal(bpy.types.Operator):
    bl_idname = "sco.copyscal"
    bl_label = "Copy Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        act = context.active_object
        if not act:
            self.report({'WARNING'}, "No active object!")
            return {'CANCELLED'}

        for o in context.selected_objects:
            if o != act:
                o.scale = act.scale
        return {'FINISHED'}


class SCO_OT_CopyRot(bpy.types.Operator):
    bl_idname = "sco.copyrot"
    bl_label = "Copy Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        act = context.active_object
        if not act:
            self.report({'WARNING'}, "No active object!")
            return {'CANCELLED'}

        for o in context.selected_objects:
            if o != act:
                o.rotation_euler = act.rotation_euler
        return {'FINISHED'}


class SCO_OT_Distrib(bpy.types.Operator):
    bl_idname = "sco.distrib"
    bl_label = "Distribute"

    axis: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(context.selected_objects) >= 3

    def execute(self, context):
        sel = context.selected_objects
        sel.sort(key=lambda o: o.location[int(self.axis)])
        first = sel[0]
        last = sel[-1]

        dist = last.location[int(self.axis)] - first.location[int(self.axis)]
        step = dist / (len(sel) - 1)

        for i, o in enumerate(sel):
            p = list(o.location)
            p[int(self.axis)] = first.location[int(self.axis)] + (i * step)
            o.location = tuple(p)

        return {'FINISHED'}


class SCO_PT_Objs(bpy.types.Panel):
    bl_label = "SCO ButtObjects"
    bl_idname = "VIEW3D_PT_sco_buttobjects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Item"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        pg = context.scene.SCO_pg
        act = context.active_object

        layout.label(text=f"Active: {act.name if act else 'None'}")

        if not pg.SCO_ucur:
            layout.prop(pg, "SCO_aorig", text="Align Origin")

        if not pg.SCO_aorig:
            layout.prop(pg, "SCO_ucur", text="Use 3D Cursor")

        col = layout.column()
        col.label(text="Select Axis:")
        row = col.row(align=True)
        row.operator("sco.alignobj", text="X").axis = '0'
        row.operator("sco.alignobj", text="Y").axis = '1'
        row.operator("sco.alignobj", text="Z").axis = '2'

        if not pg.SCO_aorig:
            col = layout.column()
            col.label(text="Bounds Extent:")
            col.prop(pg, "SCO_lext", expand=True)

            if not pg.SCO_ucur:
                col = layout.column()
                col.label(text="Bounds Pos:")
                col.prop(pg, "SCO_bpos", expand=True)

        if pg.SCO_aorig:
            col = layout.column(align=True)
            col.operator("sco.copyscal", text="Copy Scale")
            col.operator("sco.copyrot", text="Copy Rotation")
            col.separator()
            col.separator()
            col.separator()
            col.label(text="Distribute (3+):")
            row = col.row(align=True)
            row.operator("sco.distrib", text="X").axis = "0"
            row.operator("sco.distrib", text="Y").axis = "1"
            row.operator("sco.distrib", text="Z").axis = "2"


class SCO_OT_MoveOrig(bpy.types.Operator):
    bl_idname = "object.move_origin_to_selected"
    bl_label = "Move Origin to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'EDIT_MESH':
            return False
        sel_objs = [o for o in context.objects_in_mode if o.type == 'MESH']
        if not sel_objs:
            return False
        sel_count = 0
        for o in sel_objs:
            bm = bmesh.from_edit_mesh(o.data)
            if any(v.select for v in bm.verts) or any(e.select for e in bm.edges) or any(f.select for f in bm.faces):
                sel_count += 1
                if sel_count > 1:
                    return False
        return sel_count == 1

    def execute(self, context):
        scene = context.scene
        orig_cur_loc = scene.cursor.location.copy()
        edit_objs = [o for o in scene.objects if o.select_get() and o.mode == 'EDIT']
        sel_objs = [o for o in context.objects_in_mode if o.type == 'MESH']

        for o in sel_objs:
            bm = bmesh.from_edit_mesh(o.data)
            if any(v.select for v in bm.verts) or any(e.select for e in bm.edges) or any(f.select for f in bm.faces):
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.view3d.snap_cursor_to_selected()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = o
                o.select_set(True)
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                scene.cursor.location = orig_cur_loc
                break

        for eo in edit_objs:
            eo.select_set(True)
            context.view_layer.objects.active = eo
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


class SCO_PT_ObjsEdit(bpy.types.Panel):
    bl_label = "SCO ButtObjects"
    bl_idname = "VIEW3D_PT_sco_buttobjects_edit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Item"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.move_origin_to_selected")


classes = [
    SCO_OT_AlignObj,
    SCO_OT_CopyScal,
    SCO_OT_CopyRot,
    SCO_OT_Distrib,
    SCO_PT_Objs,
    SCO_Props,
    SCO_OT_MoveOrig,
    SCO_PT_ObjsEdit
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.SCO_pg = PointerProperty(type=SCO_Props)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.SCO_pg


if __name__ == "__main__":
    register()
