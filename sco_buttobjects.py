# Blender Addon: SCO ButtObjects
# Version 2.0.1
# Author: BEAST_of_BURDEN (scottb613@yahoo.com)

# This script is licensed under the GNU General Public License v3.
# See the LICENSE file for more details.

# This script incorporates code from [Distribute/BlenderBob]
# Originally licensed under GPLv3: [https://extensions.blender.org/add-ons/distribute/]
# Modifications and additions by [SCO ButtObjects/BEAST_of_BURDEN]
# Incorporated "Distribute" function into this script – changed labels and buttons.

import bpy
from mathutils import Vector
from bpy.props import EnumProperty, BoolProperty, FloatVectorProperty, PointerProperty
from bpy.types import PropertyGroup

# Define the Property Group
class SCOButtObjectsProperties(PropertyGroup):
    use_cursor: BoolProperty(
        name="Use Cursor",
        description="Align to 3D Cursor",
        default=False,
    )
    align_to_origin: BoolProperty(
        name="Align to Origin",
        description="Align to Object Origin",
        default=False,
    )
    cursor_position_saved: FloatVectorProperty(
        name="Cursor Position Saved",
        description="Saved position of the 3D cursor",
        default=(0.0, 0.0, 0.0)
    )
    last_extent: EnumProperty(
        name="Last Extent",
        items=[
            ('MIN', "Min", "Align to Minimum Extent"),
            ('CTR', "Ctr", "Align to Center Extent"),
            ('MAX', "Max", "Align to Maximum Extent"),
        ],
        default='CTR'
    )

# Alignment function
def align_objects(context, axis, align_to_min, inside, use_center, use_cursor, align_to_origin, cursor_position):
    if align_to_origin:
        active_obj = context.active_object
        if not active_obj:
            return

        origin_position = active_obj.location[axis]

        for obj in context.selected_objects:
            if obj == active_obj:
                continue
            obj.location[axis] = origin_position
        bpy.context.view_layer.update()  # Update the view layer
        return

    if use_cursor:
        cursor_position = context.scene.cursor.location[:]
        target_position = cursor_position[axis]
    else:
        active_obj = context.active_object
        if not active_obj:
            return

        active_bounds = [active_obj.matrix_world @ Vector(coord) for coord in active_obj.bound_box]
        active_min = [min([v[i] for v in active_bounds]) for i in range(3)]
        active_max = [max([v[i] for v in active_bounds]) for i in range(3)]
        active_ctr = [(active_min[i] + active_max[i]) / 2 for i in range(3)]

        if context.scene.sco_buttobjects_properties.last_extent == "MIN":
            target_position = active_min[axis]
        elif context.scene.sco_buttobjects_properties.last_extent == "MAX":
            target_position = active_max[axis]
        elif context.scene.sco_buttobjects_properties.last_extent == "CTR":
            target_position = active_ctr[axis]

    for obj in context.selected_objects:
        if not use_cursor and obj == context.active_object:
            continue

        obj_bounds = [obj.matrix_world @ Vector(coord) for coord in obj.bound_box]
        obj_min = [min([v[i] for v in obj_bounds]) for i in range(3)]
        obj_max = [max([v[i] for v in obj_bounds]) for i in range(3)]
        obj_ctr = [(obj_min[i] + obj_max[i]) / 2 for i in range(3)]

        if inside:
            if context.scene.sco_buttobjects_properties.last_extent == "MIN":
                offset = target_position - obj_min[axis]
            elif context.scene.sco_buttobjects_properties.last_extent == "MAX":
                offset = target_position - obj_max[axis]
            elif context.scene.sco_buttobjects_properties.last_extent == "CTR":
                offset = target_position - obj_ctr[axis]
        else:
            if context.scene.sco_buttobjects_properties.last_extent == "MIN":
                offset = target_position - obj_max[axis]
            elif context.scene.sco_buttobjects_properties.last_extent == "MAX":
                offset = target_position - obj_min[axis]
            elif context.scene.sco_buttobjects_properties.last_extent == "CTR":
                offset = target_position - obj_ctr[axis]

        obj.location[axis] += offset

    bpy.context.view_layer.update()  # Update the view layer

# Align Objects Operator
class SCO_OT_AlignObjects(bpy.types.Operator):
    bl_idname = "sco.align_objects"
    bl_label = "Align Objects"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=[
            ('0', "X", "Align along the X axis"),
            ('1', "Y", "Align along the Y axis"),
            ('2', "Z", "Align along the Z axis"),
        ],
        default='0'
    )

    align_to_min: BoolProperty(
        name="Align to Min",
        description="Align objects to the minimum bounds",
        default=False,
    )

    inside: BoolProperty(
        name="Inside",
        description="Align objects inside the bounds",
        default=False,
    )

    use_center: BoolProperty(
        name="Use Center",
        description="Align objects to the center bounds",
        default=True,
    )

    def execute(self, context):
        cursor_position = context.scene.sco_buttobjects_properties.cursor_position_saved
        use_cursor = context.scene.sco_buttobjects_properties.use_cursor
        align_to_origin = context.scene.sco_buttobjects_properties.align_to_origin

        if self.use_center:
            context.scene.sco_buttobjects_properties.last_extent = "CTR"
        elif self.align_to_min:
            context.scene.sco_buttobjects_properties.last_extent = "MIN"
        else:
            context.scene.sco_buttobjects_properties.last_extent = "MAX"

        align_objects(
            context, int(self.axis), self.align_to_min, self.inside,
            self.use_center, use_cursor, align_to_origin, cursor_position
        )

        # Reset properties after execution if "Ctr" is used
        if self.use_center:
            self.reset_properties()

        return {'FINISHED'}

    def reset_properties(self):
        # Reset operator properties to their default state
        self.align_to_min = True
        self.inside = False
        self.use_center = False
# Copy Scale Operator
class SCO_OT_CopyScale(bpy.types.Operator):
    bl_idname = "sco.copy_scale"
    bl_label = "Copy Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "No active object found!")
            return {'CANCELLED'}

        for obj in context.selected_objects:
            if obj == active_obj:
                continue
            obj.scale = active_obj.scale
        return {'FINISHED'}

# Copy Rotation Operator
class SCO_OT_CopyRotation(bpy.types.Operator):
    bl_idname = "sco.copy_rotation"
    bl_label = "Copy Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "No active object found!")
            return {'CANCELLED'}

        for obj in context.selected_objects:
            if obj == active_obj:
                continue
            obj.rotation_euler = active_obj.rotation_euler
        return {'FINISHED'}

# Distribute Objects Operator
class DistributeSelectedOperator(bpy.types.Operator):
    """Operator to distribute selected objects evenly"""
    bl_idname = "object.distribute_selected"
    bl_label = "Distribute Selected"
    
    axis: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(bpy.context.selected_objects) >= 3

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        selected_objects.sort(key=lambda obj: obj.location[int(self.axis)])
        
        first_object = selected_objects[0]
        last_object = selected_objects[-1]
        
        total_distance = last_object.location[int(self.axis)] - first_object.location[int(self.axis)]
        spacing = total_distance / (len(selected_objects) - 1)
        
        for i, obj in enumerate(selected_objects):
            pos = list(obj.location)
            pos[int(self.axis)] = first_object.location[int(self.axis)] + (i * spacing)
            obj.location = tuple(pos)
        
        return {'FINISHED'}

# Main Panel
class SCO_PT_ButtObjectsPanel(bpy.types.Panel):
    bl_label = "ButtObjects"
    bl_idname = "SCO_PT_butt_objects_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Item"

    @classmethod
    def poll(cls, context):
        # Only show the panel in Object Mode
        return context.space_data.type == 'VIEW_3D' and context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        active_obj = context.active_object

        if active_obj:
            layout.label(text=f"Active Object: {active_obj.name}")
        else:
            layout.label(text="Active Object: None")

        sco_props = context.scene.sco_buttobjects_properties

        if not sco_props.use_cursor:
            layout.prop(sco_props, "align_to_origin", text="Align to Origin")

        if not sco_props.align_to_origin:
            layout.prop(sco_props, "use_cursor", text="Align to 3D Cursor")

        col = layout.column()
        col.label(text="Select Axis:")
        row = col.row(align=True)
        row.operator(SCO_OT_AlignObjects.bl_idname, text="X").axis = '0'
        row.operator(SCO_OT_AlignObjects.bl_idname, text="Y").axis = '1'
        row.operator(SCO_OT_AlignObjects.bl_idname, text="Z").axis = '2'

        if not sco_props.align_to_origin:
            col = layout.column()
            col.label(text="Bounds Extent:")
            row = col.row(align=True)
            row.operator(SCO_OT_AlignObjects.bl_idname, text="Min").align_to_min = True
            row.operator(SCO_OT_AlignObjects.bl_idname, text="Ctr").use_center = True
            row.operator(SCO_OT_AlignObjects.bl_idname, text="Max").align_to_min = False

            if not sco_props.use_cursor:
                col = layout.column()
                col.label(text="Bounds Position:")
                row = col.row(align=True)
                row.operator(SCO_OT_AlignObjects.bl_idname, text="Inside").inside = True
                row.operator(SCO_OT_AlignObjects.bl_idname, text="Outside").inside = False

        if sco_props.align_to_origin:
            col = layout.column(align=True)
            col.operator("sco.copy_scale", text="Copy Scale")
            col.operator("sco.copy_rotation", text="Copy Rotation")
            col.separator()  # Adds 1 lines of space
            col.separator()  # Adds 1 lines of space
            col.separator()  # Adds 1 lines of space
            col.label(text="Distribute Objects (3 or more):")
            row = col.row(align=True)
            row.operator("object.distribute_selected", text="X").axis = "0"
            row.operator("object.distribute_selected", text="Y").axis = "1"
            row.operator("object.distribute_selected", text="Z").axis = "2"

classes = [
    SCO_OT_AlignObjects, SCO_OT_CopyScale, SCO_OT_CopyRotation,
    DistributeSelectedOperator, SCO_PT_ButtObjectsPanel, SCOButtObjectsProperties
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.sco_buttobjects_properties = PointerProperty(type=SCOButtObjectsProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.sco_buttobjects_properties

if __name__ == "__main__":
    register()
