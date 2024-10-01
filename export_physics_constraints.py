bl_info = {
    "name": "Extract Objects and Physics Constraints",
    "author": "Your Name",
    "version": (1, 3),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Physics",
    "description": "Extracts objects and their physics constraints and exports to JSON",
    "category": "Object",
}

import bpy
import json
import os
from bpy.props import StringProperty, BoolProperty
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

    export_stl: BoolProperty(
        name="Export STL Files",
        description="Export each object as an STL file",
        default=True
    )

    def execute(self, context):
        output_dir = os.path.dirname(self.filepath)
        data = {
            "geometry": [],
            "contact": {
                "friction_coefficient": 0.5
            }
        }

        # Create a mapping from objects to IDs
        object_id_map = {}
        current_id = 1

        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue  # Skip non-mesh objects

            obj_data = {}
            obj_id = obj.pass_index if obj.pass_index != 0 else current_id
            object_id_map[obj.name] = obj_id
            current_id += 1  # Increment ID for next object if pass_index is not used

            # Export object as STL
            if self.export_stl:
                stl_filename = f"{obj.name}.stl"
                stl_filepath = os.path.join(output_dir, stl_filename)
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.export_mesh.stl(
                    filepath=stl_filepath,
                    use_selection=True,
                    global_scale=1.0,
                    use_scene_unit=False,
                    use_mesh_modifiers=True,
                )
                obj_data["mesh"] = stl_filename
            else:
                obj_data["mesh"] = f"{obj.name}.stl"  # Assuming the STL files exist

            # Add transformation
            obj_data["transformation"] = {
                "translation": list(obj.location)
            }

            # Assign volume_selection or id
            obj_data["volume_selection"] = obj_id

            # Determine if object is an obstacle
            if obj.rigid_body and obj.rigid_body.type == 'PASSIVE':
                obj_data["is_obstacle"] = True

            # Extract physics properties
            physics_properties = {}

            # Soft Body properties
            if 'SOFT_BODY' in [mod.type for mod in obj.modifiers]:
                sb_settings = obj.modifiers['Softbody'].settings
                physics_properties['bending_stiffness'] = sb_settings.bending
                physics_properties['self_collision'] = sb_settings.use_self_collision

            # Rigid Body properties
            if obj.rigid_body:
                rb = obj.rigid_body
                physics_properties['mass'] = rb.mass
                physics_properties['friction'] = rb.friction
                physics_properties['restitution'] = rb.restitution
                physics_properties['collision_shape'] = rb.collision_shape

            # Rigid Body Constraint properties
            if obj.rigid_body_constraint:
                rbc = obj.rigid_body_constraint
                physics_properties['constraint'] = {
                    'type': rbc.type,
                    'enabled': rbc.enabled,
                    'collision_disabled': rbc.disable_collisions,
                    'object1': rbc.object1.name if rbc.object1 else None,
                    'object2': rbc.object2.name if rbc.object2 else None,
                }

            if physics_properties:
                obj_data["physics_properties"] = physics_properties

            data["geometry"].append(obj_data)

        # Write JSON file
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
