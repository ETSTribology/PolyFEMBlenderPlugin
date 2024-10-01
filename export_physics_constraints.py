bl_info = {
    "name": "Extract Objects and Physics Constraints",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Physics",
    "description": "Extracts objects and their physics constraints and exports to JSON",
    "category": "Object",
}

import bpy
import json
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

class OBJECT_OT_extract_physics_constraints(bpy.types.Operator, ExportHelper):
    """Extract Objects and Physics Constraints"""
    bl_idname = "object.extract_physics_constraints"
    bl_label = "Export Physics Constraints to JSON"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        data = []
        for obj in bpy.context.scene.objects:
            obj_data = {
                'name': obj.name,
                'rigid_body': None,
                'constraint': None,
            }

            if obj.rigid_body:
                obj_data['rigid_body'] = {
                    'type': obj.rigid_body.type,
                    'mass': obj.rigid_body.mass,
                    'friction': obj.rigid_body.friction,
                    'restitution': obj.rigid_body.restitution,
                    # Add other rigid body properties as needed
                }

            if obj.rigid_body_constraint:
                constraint = obj.rigid_body_constraint
                obj_data['constraint'] = {
                    'type': constraint.type,
                    'object1': constraint.object1.name if constraint.object1 else None,
                    'object2': constraint.object2.name if constraint.object2 else None,
                    # Add other constraint properties as needed
                }

            data.append(obj_data)

        # Write data to JSON file
        try:
            with open(self.filepath, 'w') as outfile:
                json.dump(data, outfile, indent=4)
            self.report({'INFO'}, f"Data exported to {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to write file: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class VIEW3D_PT_extract_physics_panel(bpy.types.Panel):
    """Panel for Extracting Physics Constraints"""
    bl_label = "Extract Physics Constraints"
    bl_idname = "VIEW3D_PT_extract_physics_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Physics'

    def draw(self, context):
        layout = self.layout
        layout.operator(OBJECT_OT_extract_physics_constraints.bl_idname, text="Export to JSON")

def register():
    bpy.utils.register_class(OBJECT_OT_extract_physics_constraints)
    bpy.utils.register_class(VIEW3D_PT_extract_physics_panel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_extract_physics_constraints)
    bpy.utils.unregister_class(VIEW3D_PT_extract_physics_panel)

if __name__ == "__main__":
    register()
