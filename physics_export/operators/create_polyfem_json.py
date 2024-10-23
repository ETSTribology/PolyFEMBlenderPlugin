import bpy
import json
import os
import subprocess
import bmesh
import math
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, IntProperty
from bpy.types import Operator

class CreatePolyFemJSONOperator(Operator):
    """Create a JSON configuration file for PolyFem simulation and export meshes"""
    bl_idname = "polyfem.create_json"
    bl_label = "Create PolyFEM JSON"
    bl_description = "Generate a JSON configuration file for PolyFEM simulation and export selected meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.polyfem_settings_json
        project_path = bpy.path.abspath(settings.export_path)
        json_filename = settings.json_filename
        json_path = os.path.join(project_path, json_filename)

        # Ensure the project directory exists
        if not os.path.exists(project_path):
            os.makedirs(project_path)

        # Create JSON data structure
        json_data = self.create_json_data(settings)

        # Determine which objects to export
        objects_to_export = self.get_objects_to_export(context, settings)

        if not objects_to_export:
            self.report({'WARNING'}, "No objects selected for export.")
            return {'CANCELLED'}

        output_mesh_dir = os.path.join(project_path, "exported_meshes")
        if not os.path.exists(output_mesh_dir):
            os.makedirs(output_mesh_dir)

        current_id = 1

        for obj in objects_to_export:
            if obj.type != 'MESH':
                continue  # Skip non-mesh objects

            obj_data = self.process_object(obj, current_id, output_mesh_dir, settings, context)
            if obj_data is None:
                return {'CANCELLED'}

            json_data["geometry"].append(obj_data)
            current_id += 1

        # Write the JSON configuration file
        if not self.write_json_file(json_data, json_path):
            return {'CANCELLED'}

        self.report({'INFO'}, f"Meshes exported and processed successfully in '{output_mesh_dir}'")
        return {'FINISHED'}

    def create_json_data(self, settings):
        """Create the initial JSON data structure based on settings."""
        json_data = {
            "contact": {
                "enabled": settings.contact_enabled,
                "dhat": settings.contact_dhat,
                "friction_coefficient": settings.contact_friction_coefficient,
                "epsv": settings.contact_epsv
            },
            "time": {
                "integrator": settings.time_integrator,
                "tend": settings.time_tend,
                "dt": settings.time_dt
            },
            "space": {
                "advanced": {
                    "bc_method": settings.space_bc_method
                }
            },
            "boundary_conditions": {
                "rhs": [settings.boundary_rhs_x, settings.boundary_rhs_y, settings.boundary_rhs_z]
            },
            "materials": {
                "type": settings.materials_type,
                "E": settings.materials_E,
                "nu": settings.materials_nu,
                "rho": settings.materials_rho
            },
            "solver": {
                "linear": {
                    "solver": settings.solver_linear_solver
                },
                "nonlinear": {
                    "x_delta": settings.solver_nonlinear_x_delta
                },
                "advanced": {
                    "lump_mass_matrix": settings.solver_advanced_lump_mass_matrix
                },
                "contact": {
                    "friction_convergence_tol": settings.solver_contact_friction_convergence_tol,
                    "friction_iterations": settings.solver_contact_friction_iterations
                }
            },
            "output": {
                "json": settings.output_json,
                "paraview": {
                    "file_name": settings.output_paraview_file_name,
                    "options": {
                        "material": settings.output_paraview_material,
                        "body_ids": settings.output_paraview_body_ids,
                        "tensor_values": settings.output_paraview_tensor_values,
                        "nodes": settings.output_paraview_nodes
                    },
                    "vismesh_rel_area": settings.output_paraview_vismesh_rel_area
                },
                "advanced": {
                    "save_solve_sequence_debug": settings.output_advanced_save_solve_sequence_debug,
                    "save_time_sequence": settings.output_advanced_save_time_sequence
                }
            },
            "geometry": []
        }
        return json_data

    def get_objects_to_export(self, context, settings):
        """Determine which objects to export based on settings."""
        if settings.export_selected_only:
            return context.selected_objects
        else:
            return context.scene.objects

    def process_object(self, obj, obj_id, output_dir, settings, context):
        """Process an individual object and collect its data."""
        obj_data = {}
        obj_data["volume_selection"] = obj_id

        # Export mesh
        mesh_filename = f"{obj.name}.{settings.export_format.lower()}"
        mesh_filepath = os.path.join(output_dir, mesh_filename)
        success = self.export_mesh(obj, mesh_filepath, settings)
        if not success:
            self.report({'ERROR'}, f"Failed to export mesh for object {obj.name}")
            return None
        obj_data["mesh"] = mesh_filename

        # Add transformation using quaternion
        obj_data["transformation"] = {
            "translation": list(obj.location),
            "rotation": list(obj.rotation_quaternion),
            "scale": list(obj.scale),
        }

        # Determine if object is an obstacle
        if obj.rigid_body and obj.rigid_body.type == 'PASSIVE':
            obj_data["is_obstacle"] = True

        # Extract physics properties
        physics_properties = self.extract_physics_properties(obj)
        if physics_properties:
            obj_data["physics_properties"] = physics_properties

        # Include custom properties
        custom_props = self.get_custom_properties(obj)
        if custom_props:
            obj_data["custom_properties"] = custom_props

        # Include point selection if vertices are selected and export_point_selection is True
        if settings.export_point_selection:
            point_selection = self.get_point_selection(obj, context)
            if point_selection:
                obj_data["point_selection"] = point_selection

        return obj_data

    def export_mesh(self, obj, mesh_filepath, settings):
        """Export the mesh of an object based on the selected format."""
        bpy.ops.object.mode_set(mode='OBJECT')

        for obj_iter in bpy.context.view_layer.objects:
            obj_iter.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        export_format = settings.export_format.upper()

        try:
            if export_format == 'STL':
                self.export_mesh_to_stl(obj, mesh_filepath)
            elif export_format == 'OBJ':
                self.export_mesh_to_obj(obj, mesh_filepath)
            elif export_format == 'FBX':
                self.report({'ERROR'}, "FBX export is not supported without the FBX addon.")
                return False
            elif export_format == 'GLTF':
                self.report({'ERROR'}, "GLTF export is not supported without the GLTF addon.")
                return False
            elif export_format == 'MSH':
                # Export to STL format for TetWild
                temp_stl_filepath = os.path.join(os.path.dirname(mesh_filepath), f"{obj.name}_temp.stl")
                success = self.export_mesh_to_stl(obj, temp_stl_filepath)
                if not success:
                    self.report({'ERROR'}, f"Failed to export {obj.name} to STL format for TetWild.")
                    return False
                # Run TetWild
                success = self.run_tetwild(temp_stl_filepath, mesh_filepath)
                if not success:
                    return False
            else:
                self.report({'ERROR'}, f"Unsupported export format without addons: {export_format}")
                return False
        except Exception as e:
            self.report({'ERROR'}, f"Error exporting {obj.name}: {e}")
            return False

        return True

    def export_mesh_to_stl(self, obj, filepath):
        """Exports the mesh data of an object to an STL file."""
        mesh = obj.to_mesh()
        mesh.calc_loop_triangles()

        with open(filepath, 'w') as stl_file:
            stl_file.write(f'solid {obj.name}\n')

            for tri in mesh.loop_triangles:
                normal = tri.normal
                stl_file.write(f'facet normal {normal.x} {normal.y} {normal.z}\n')
                stl_file.write('  outer loop\n')
                for vertex_index in tri.vertices:
                    vertex = mesh.vertices[vertex_index].co
                    stl_file.write(f'    vertex {vertex.x} {vertex.y} {vertex.z}\n')
                stl_file.write('  endloop\n')
                stl_file.write('endfacet\n')

            stl_file.write(f'endsolid {obj.name}\n')

        obj.to_mesh_clear()
        return True

    def export_mesh_to_obj(self, obj, filepath):
        """Exports the mesh data of an object to an OBJ file."""
        mesh = obj.to_mesh()
        mesh.calc_loop_triangles()
        mesh.calc_normals_split()

        with open(filepath, 'w') as obj_file:
            obj_file.write('# OBJ file\n')

            # Write vertices
            for vertex in mesh.vertices:
                coord = vertex.co
                obj_file.write(f'v {coord.x} {coord.y} {coord.z}\n')

            # Write normals
            for loop in mesh.loops:
                normal = loop.normal
                obj_file.write(f'vn {normal.x} {normal.y} {normal.z}\n')

            # Write faces
            for tri in mesh.loop_triangles:
                indices = [str(vertex_index + 1) for vertex_index in tri.vertices]
                obj_file.write(f'f {" ".join(indices)}\n')

        obj.to_mesh_clear()
        return True

    def run_tetwild(self, input_file, output_file, ideal_edge_length=0.05, epsilon=1e-3, filter_energy=10, max_pass=80):
        """Run TetWild via Docker to generate an MSH file from a mesh."""
        # Build the command string with the required parameters
        command = [
            "docker", "run", "--rm",
            "-v", f"{os.path.abspath(os.path.dirname(input_file))}:/data",  # Mount the directory containing the input file
            "yixinhu/tetwild",  # Docker image
            "--input", f"/data/{os.path.basename(input_file)}",  # Input file path in container
            "--ideal-edge-length", str(ideal_edge_length),
            "--epsilon", str(epsilon),
            "--filter-energy", str(filter_energy),
            "--max-pass", str(max_pass),
            "--output", f"/data/{os.path.basename(output_file)}"  # Output file
        ]

        # Execute the command
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"TetWild ran successfully with input: {input_file}")
            print(result.stdout)
            return True
        except FileNotFoundError:
            self.report({'ERROR'}, "Docker not found. Please ensure Docker is installed and in your system's PATH.")
            return False
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f"Error running TetWild: {e}")
            print(f"Standard Output: {e.stdout}")
            print(f"Standard Error: {e.stderr}")
            return False

    def extract_physics_properties(self, obj):
        """Extract physics properties from an object."""
        physics_properties = {}

        # Soft Body properties
        for mod in obj.modifiers:
            if mod.type == 'SOFT_BODY':
                sb_settings = mod.settings
                physics_properties['bending_stiffness'] = sb_settings.bending
                physics_properties['self_collision'] = sb_settings.use_self_collision
                break  # Assuming only one Soft Body modifier

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

        return physics_properties if physics_properties else None

    def get_custom_properties(self, obj):
        """Retrieve custom properties from an object."""
        custom_props = {}
        for prop_name in obj.keys():
            if prop_name not in "_RNA_UI":  # Exclude Blender's internal properties
                custom_props[prop_name] = obj[prop_name]
        return custom_props if custom_props else None

    def get_point_selection(self, obj, context):
        """Retrieve the bounding boxes of selected vertices and format them for JSON."""
        # Save the current mode
        original_mode = obj.mode

        # Switch to Edit Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Get the mesh data
        bm = bmesh.from_edit_mesh(obj.data)

        # Check if any vertices are selected
        selected_verts = [v for v in bm.verts if v.select]
        if not selected_verts:
            bpy.ops.object.mode_set(mode='OBJECT')
            return None  # No vertices selected for this object

        # Calculate the bounding box of selected vertices
        min_coord = Vector((float('inf'), float('inf'), float('inf')))
        max_coord = Vector((float('-inf'), float('-inf'), float('-inf')))

        for v in selected_verts:
            global_coord = obj.matrix_world @ v.co
            min_coord.x = min(min_coord.x, global_coord.x)
            min_coord.y = min(min_coord.y, global_coord.y)
            min_coord.z = min(min_coord.z, global_coord.z)

            max_coord.x = max(max_coord.x, global_coord.x)
            max_coord.y = max(max_coord.y, global_coord.y)
            max_coord.z = max(max_coord.z, global_coord.z)

        # Optionally, calculate relative coordinates based on object's bounding box
        obj_bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        obj_min = Vector((
            min(corner.x for corner in obj_bbox),
            min(corner.y for corner in obj_bbox),
            min(corner.z for corner in obj_bbox)
        ))
        obj_max = Vector((
            max(corner.x for corner in obj_bbox),
            max(corner.y for corner in obj_bbox),
            max(corner.z for corner in obj_bbox)
        ))

        # Function to calculate relative positions
        def get_relative(value, min_obj, max_obj):
            return (value - min_obj) / (max_obj - min_obj) if max_obj != min_obj else 0.0

        # Calculate relative coordinates
        rel_min = Vector((
            get_relative(min_coord.x, obj_min.x, obj_max.x),
            get_relative(min_coord.y, obj_min.y, obj_max.y),
            get_relative(min_coord.z, obj_min.z, obj_max.z)
        ))
        rel_max = Vector((
            get_relative(max_coord.x, obj_min.x, obj_max.x),
            get_relative(max_coord.y, obj_min.y, obj_max.y),
            get_relative(max_coord.z, obj_min.z, obj_max.z)
        ))

        # Prepare the point selection data
        point_selection = [{
            "id": 1,  # You may want to adjust the ID or make it dynamic
            "box": [
                [rel_min.x, rel_min.y, rel_min.z],
                [rel_max.x, rel_max.y, rel_max.z]
            ],
            "relative": True
        }]

        bpy.ops.object.mode_set(mode='OBJECT')  # Return to Object Mode

        return point_selection

    def write_json_file(self, data, json_path):
        """Write the collected data to a JSON file."""
        try:
            with open(json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            self.report({'INFO'}, f"JSON file created at '{json_path}'")
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create JSON file: {e}")
            return False
