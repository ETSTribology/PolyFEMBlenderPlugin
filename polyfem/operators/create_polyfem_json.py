import bpy
import json
import os
import subprocess
import bmesh
import math
import platform
import threading
import queue
import concurrent.futures
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, IntProperty
from bpy.types import Operator

# ----------------------------
# Popup Message Box Operator
# ----------------------------
class POLYFEM_OT_ShowMessageBox(Operator):
    """Show a popup message box"""
    bl_idname = "polyfem.show_message_box"
    bl_label = "PolyFem Notification"
    bl_options = {'REGISTER'}

    message: StringProperty(name="Message")
    title: StringProperty(name="Title", default="PolyFem Notification")
    icon: EnumProperty(
        name="Icon",
        items=[
            ('INFO', "Info", "Information"),
            ('ERROR', "Error", "Error"),
            ('WARNING', "Warning", "Warning"),
            ('NONE', "None", "No Icon"),
        ],
        default='INFO'
    )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.message)


class PolyFEMApplyMaterial(Operator):
    bl_idname = "polyfem.apply_material"
    bl_label = "Apply PolyFem Material"

    obj_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)
        settings = context.scene.polyfem_settings

        if obj:
            # Assign material properties from the UI to the object's custom properties
            obj["material_type"] = settings.materials_type
            obj["material_E"] = settings.materials_E
            obj["material_nu"] = settings.materials_nu
            obj["material_rho"] = settings.materials_rho
            obj["material_id"] = obj.get("material_id", len(context.scene.objects) + 1)  # Assign a unique ID

            self.report({'INFO'}, f"Material applied to {obj.name} (ID: {obj['material_id']})")
        else:
            self.report({'ERROR'}, f"Object {self.obj_name} not found")

        return {'FINISHED'}


# ----------------------------
# Create PolyFem JSON Operator
# ----------------------------
class CreatePolyFemJSONOperator(Operator):
    """Create a JSON configuration file for PolyFem simulation and export meshes"""
    bl_idname = "polyfem.create_json"
    bl_label = "Create PolyFEM JSON"
    bl_description = "Generate a JSON configuration file for PolyFEM simulation and export selected meshes"
    bl_options = {'REGISTER', 'UNDO'}

    # Queue for thread-safe reporting
    report_queue = queue.Queue()

    # ThreadPoolExecutor for concurrent Docker tasks
    docker_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def execute(self, context):
        settings = context.scene.polyfem_settings
        # Start the background thread for JSON creation and mesh exporting
        threading.Thread(target=self.background_process, args=(context,), daemon=True).start()
        # Register a timer to process the report queue
        bpy.app.timers.register(self.process_report_queue)
        self.report({'INFO'}, "Started JSON creation and mesh exporting in the background.")
        return {'FINISHED'}

    def background_process(self, context):
        """Background thread to handle JSON creation and mesh exporting."""
        settings = context.scene.polyfem_settings
        project_path = bpy.path.abspath(settings.export_path)
        json_filename = settings.json_filename
        json_path = os.path.join(project_path, json_filename)

        # Ensure the project directory exists
        if not os.path.exists(project_path):
            try:
                os.makedirs(project_path)
                self.report_queue.put(('INFO', f"Created project directory at '{project_path}'"))
            except Exception as e:
                self.report_queue.put(('ERROR', f"Failed to create project directory: {e}"))
                return

        # Create JSON data structure
        try:
            json_data = self.create_json_data(settings)
            self.report_queue.put(('INFO', "JSON data structure created successfully."))
        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to create JSON data structure: {e}"))
            return

        # Determine which objects to export
        try:
            objects_to_export = self.get_objects_to_export(context, settings)
            if not objects_to_export:
                self.report_queue.put(('WARNING', "No objects selected for export."))
                return
            self.report_queue.put(('INFO', f"Found {len(objects_to_export)} objects to export."))
        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to determine objects to export: {e}"))
            return

        # Ensure the output mesh directory exists
        output_mesh_dir = os.path.join(project_path, "exported_meshes")
        if not os.path.exists(output_mesh_dir):
            try:
                os.makedirs(output_mesh_dir)
                self.report_queue.put(('INFO', f"Created mesh export directory at '{output_mesh_dir}'"))
            except Exception as e:
                self.report_queue.put(('ERROR', f"Failed to create mesh export directory: {e}"))
                return

        current_id = 1
        geometry_list = []
        docker_futures = []

        for obj in objects_to_export:
            if obj.type != 'MESH':
                self.report_queue.put(('WARNING', f"Skipping non-mesh object '{obj.name}'."))
                continue  # Skip non-mesh objects

            obj_data = self.process_object(obj, current_id, output_mesh_dir, settings, context)
            if obj_data is None:
                self.report_queue.put(('ERROR', f"Failed to process object '{obj.name}'."))
                continue

            geometry_list.append(obj_data)
            current_id += 1

        json_data["geometry"] = geometry_list

        # Write the JSON configuration file
        try:
            self.write_json_file(json_data, json_path)
        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to write JSON file: {e}"))
            return

        self.report_queue.put(('INFO', f"JSON file created at '{json_path}'"))
        self.report_queue.put(('INFO', f"Meshes exported successfully in '{output_mesh_dir}'"))

        # Wait for all Docker tasks to complete
        if docker_futures:
            self.report_queue.put(('INFO', "Waiting for all Docker tasks to complete..."))
            concurrent.futures.wait(docker_futures)
            self.report_queue.put(('INFO', "All Docker tasks completed."))

    def process_object(self, obj, material_id, output_dir, settings, context):
        """Process an individual object and collect its data."""
        obj_data = {}
        obj_data["volume_selection"] = material_id

        # Export mesh
        mesh_filename = f"{obj.name}.{settings.export_format.lower()}"
        mesh_filepath = os.path.join(output_dir, mesh_filename)
        success = self.export_mesh(obj, mesh_filepath, settings)
        if not success:
            self.report_queue.put(('ERROR', f"Failed to export mesh for object '{obj.name}'"))
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

        obj_data["material"] = material_id

        # Include point selection if vertices are selected and export_point_selection is True
        if settings.export_point_selection:
            point_selection = self.get_point_selection(obj, context)
            if point_selection:
                obj_data["point_selection"] = point_selection

        # If export format is 'MSH', enqueue TetWild Docker command
        if settings.export_format.upper() == 'MSH':
            temp_stl_filepath = os.path.join(os.path.dirname(mesh_filepath), f"{obj.name}_temp.stl")
            success_stl = self.export_mesh_to_stl(obj, temp_stl_filepath)
            if not success_stl:
                self.report_queue.put(('ERROR', f"Failed to export {obj.name} to STL format for TetWild."))
                return None

            # Define output MSH filepath
            msh_filepath = mesh_filepath

            # Enqueue TetWild Docker command
            future = self.docker_executor.submit(
                self.run_tetwild,
                temp_stl_filepath,
                msh_filepath
            )
            self.report_queue.put(('INFO', f"Enqueued TetWild processing for '{obj.name}'."))
            # Optionally, store the future if you need to track it

        return obj_data

    def export_mesh(self, obj, mesh_filepath, settings):
        """Export the mesh of an object based on the selected format."""
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            self.report_queue.put(('WARNING', "Could not set mode to OBJECT. Proceeding anyway."))

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        export_format = settings.export_format.upper()

        try:
            if export_format == 'STL':
                self.export_mesh_to_stl(obj, mesh_filepath)
            elif export_format == 'OBJ':
                self.export_mesh_to_obj(obj, mesh_filepath)
            elif export_format == 'FBX':
                self.report_queue.put(('ERROR', "FBX export is not supported without the FBX addon."))
                return False
            elif export_format == 'GLTF':
                self.report_queue.put(('ERROR', "GLTF export is not supported without the GLTF addon."))
                return False
            elif export_format == 'MSH':
                # Export to STL format for TetWild
                temp_stl_filepath = os.path.join(os.path.dirname(mesh_filepath), f"{obj.name}_temp.stl")
                success = self.export_mesh_to_stl(obj, temp_stl_filepath)
                if not success:
                    self.report_queue.put(('ERROR', f"Failed to export {obj.name} to STL format for TetWild."))
                    return False
                # The TetWild processing is handled asynchronously
            else:
                self.report_queue.put(('ERROR', f"Unsupported export format: {export_format}"))
                return False
        except Exception as e:
            self.report_queue.put(('ERROR', f"Error exporting {obj.name}: {e}"))
            return False

        return True

    def export_mesh_to_stl(self, obj, filepath):
        """Exports the mesh data of an object to an STL file."""
        try:
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
            self.report_queue.put(('INFO', f"Exported STL for '{obj.name}' at '{filepath}'"))
            return True
        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to export STL for '{obj.name}': {e}"))
            return False

    def export_mesh_to_obj(self, obj, filepath):
        """Exports the mesh data of an object to an OBJ file."""
        try:
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
            self.report_queue.put(('INFO', f"Exported OBJ for '{obj.name}' at '{filepath}'"))
            return True
        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to export OBJ for '{obj.name}': {e}"))
            return False

    def run_tetwild(self, input_file, output_file, ideal_edge_length=0.05, epsilon=1e-3, filter_energy=10, max_pass=80):
        """Run TetWild via Docker to generate an MSH file from a mesh."""
        try:
            # Get the absolute path of the input and output directories
            input_dir = os.path.abspath(os.path.dirname(input_file))
            output_dir = os.path.abspath(os.path.dirname(output_file))

            # Check the platform and adjust paths for Windows
            if platform.system() == 'Windows':
                # Convert Windows paths to a format Docker can understand (Unix-style paths)
                input_dir = input_dir.replace('\\', '/')
                output_dir = output_dir.replace('\\', '/')
                # Docker on Windows typically uses paths like `/c/Users/...` instead of `C:/Users/...`
                if input_dir[1] == ':':  # Detects drive letter, e.g., C:
                    input_dir = f'/{input_dir[0].lower()}{input_dir[2:]}'
                if output_dir[1] == ':':  # Detects drive letter, e.g., C:
                    output_dir = f'/{output_dir[0].lower()}{output_dir[2:]}'

            # Build the command list with the required parameters
            command = [
                "docker", "run", "--rm",
                "-v", f"{input_dir}:/data",  # Mount the input directory
                "yixinhu/tetwild",  # Docker image
                "--input", f"/data/{os.path.basename(input_file)}",  # Input file path in container
                "--ideal-edge-length", str(ideal_edge_length),
                "--epsilon", str(epsilon),
                "--filter-energy", str(filter_energy),
                "--max-pass", str(max_pass),
                "--output", f"/data/{os.path.basename(output_file)}"  # Output file
            ]

            # Execute the command
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            self.report_queue.put(('INFO', f"TetWild ran successfully with input: {input_file}"))
            self.report_queue.put(('INFO', f"TetWild Output:\n{result.stdout}"))
            if result.stderr:
                self.report_queue.put(('WARNING', f"TetWild Warnings:\n{result.stderr}"))
            self.report_queue.put(('INFO', f"Generated MSH file at '{output_file}'"))
            return True
        except FileNotFoundError:
            self.report_queue.put(('ERROR', "Docker not found. Please ensure Docker is installed and in your system's PATH."))
            return False
        except subprocess.CalledProcessError as e:
            self.report_queue.put(('ERROR', f"Error running TetWild:\n{e.stderr}"))
            return False
        except Exception as e:
            self.report_queue.put(('ERROR', f"An unexpected error occurred while running TetWild:\n{e}"))
            return False

    def create_json_data(self, settings, context):
        """Create the initial JSON data structure based on settings."""
        materials_list = []  # List of materials for the global materials section
        materials_map = {}  # Map to avoid duplicate materials
        geometry_list = []  # List of objects (geometry)

        # Loop through all objects and assign materials
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # Check if the object has custom material properties
                material_data = {
                    "type": obj.get("material", settings.materials_type),
                    "E": obj.get("material_E", settings.materials_E),
                    "nu": obj.get("material_nu", settings.materials_nu),
                    "rho": obj.get("material_rho", settings.materials_rho)
                }

                # Convert the material properties to a tuple (for easy comparison)
                material_tuple = (material_data["type"], material_data["E"], material_data["nu"], material_data["rho"])

                # Check if the material already exists in the map, if not, add it
                if material_tuple not in materials_map:
                    material_id = len(materials_list)
                    materials_list.append(material_data)
                    materials_map[material_tuple] = material_id
                else:
                    material_id = materials_map[material_tuple]

                # Process the object and assign the material by its ID
                obj_data = self.process_object(obj, material_id, settings, context)
                geometry_list.append(obj_data)

        # Final JSON structure
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
            "materials": materials_list,  # The global materials list
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
            "geometry": geometry_list  # List of object entries
        }

        return json_data

    def get_objects_to_export(self, context, settings):
        """Determine which objects to export based on settings."""
        if settings.export_selected_only:
            return context.selected_objects
        else:
            return context.scene.objects

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

        try:
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

        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to retrieve point selection for '{obj.name}': {e}"))
            return None

    def write_json_file(self, data, json_path):
        """Write the collected data to a JSON file."""
        try:
            with open(json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            self.report_queue.put(('INFO', f"JSON file created at '{json_path}'"))
            return True
        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to create JSON file: {e}"))
            return False

    def process_report_queue(self):
        """Process messages from the report queue and display them to the user."""
        while not self.report_queue.empty():
            level, message = self.report_queue.get()
            bpy.ops.polyfem.show_message_box('INVOKE_DEFAULT', message=message, title=f"PolyFem - {level}", icon=level)
        return 0.1  # Continue the timer every 0.1 seconds

    def show_popup(self, message, title, icon):
        """Helper function to display a popup message box"""
        bpy.ops.polyfem.show_message_box('INVOKE_DEFAULT', message=message, title=title, icon=icon)
        return None  # To ensure the timer doesn't keep registering the same popup
