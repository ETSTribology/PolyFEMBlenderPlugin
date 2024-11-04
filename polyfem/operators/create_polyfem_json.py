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
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Operator to pull Docker images
class PullDockerImages(bpy.types.Operator):
    bl_idname = "polyfem.pull_docker_image"
    bl_label = "Pull Docker Image"
    bl_description = "Pull the selected Docker image"

    docker_image: bpy.props.StringProperty(name="Docker Image", default="yixinhu/tetwild") # type: ignore

    def execute(self, context):
        # Check if Docker is installed
        if is_docker_installed():
            if self.docker_image:
                background_pull_docker_image(self.docker_image)
                return {'FINISHED'}
            else:
                display_message("No Docker image specified.", icon='ERROR')
                return {'CANCELLED'}
        else:
            display_message("Docker is not installed. Please install Docker to proceed.", icon='ERROR')
            return {'CANCELLED'}

def display_message(message, title="Notification", icon='INFO'):
    """Schedule a popup message to be shown on the main thread."""
    def draw(self, context):
        self.layout.label(text=message)

    # Schedule the popup on the main thread using bpy.app.timers
    def show_popup():
        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
        return None  # Return None to stop the timer

    # Register a one-time timer to run the popup on the main thread
    bpy.app.timers.register(show_popup)

def is_docker_installed():
    """Check if Docker is installed and available on the machine."""
    try:
        result = subprocess.run(["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Docker not found: {e}")
        return False

def background_pull_docker_image(docker_image):
    """Pull a single Docker image in the background with progress updates."""
    def pull_image():
        try:
            bpy.context.window_manager.progress_begin(0, 1)
            try:
                logger.info(f"Pulling Docker image '{docker_image}'...")
                subprocess.run(["docker", "pull", docker_image], check=True)
                logger.info(f"Pulled Docker image '{docker_image}' successfully.")
                display_message(f"Successfully pulled Docker image '{docker_image}'", icon='INFO')
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to pull Docker image '{docker_image}': {e}")
                display_message(f"Failed to pull Docker image '{docker_image}'. Check console for details.", icon='ERROR')
            bpy.context.window_manager.progress_update(1)
            bpy.context.window_manager.progress_end()
        except Exception as e:
            display_message(f"Error pulling Docker image '{docker_image}': {e}", title="Error", icon='ERROR')
            logger.error(f"Error during Docker image pull: {e}")

    threading.Thread(target=pull_image, daemon=True).start()

# ----------------------------
# Popup Message Box Operator
# ----------------------------
class POLYFEM_OT_ShowMessageBox(Operator):
    """Show a popup message box"""
    bl_idname = "polyfem.show_message_box"
    bl_label = "PolyFem Notification"
    bl_options = {'REGISTER'}

    message: StringProperty(name="Message") # type: ignore
    title: StringProperty(name="Title", default="PolyFem Notification") # type: ignore
    icon: EnumProperty(
        name="Icon",
        items=[
            ('INFO', "Info", "Information"),
            ('ERROR', "Error", "Error"),
            ('WARNING', "Warning", "Warning"),
            ('NONE', "None", "No Icon"),
        ],
        default='INFO'
    ) # type: ignore

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

    obj_name: bpy.props.StringProperty() # type: ignore

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)
        settings = context.scene.polyfem_settings

        if obj and obj.type == 'MESH':
            # Assign material properties from the UI to the object's custom properties
            obj["material_type"] = settings.materials_type
            obj["material_E"] = settings.materials_E
            obj["material_nu"] = settings.materials_nu
            obj["material_rho"] = settings.materials_rho

            # Ensure a unique material ID is assigned
            if "material_id" not in obj:
                # Get the highest material_id used in the scene and assign a new unique ID
                used_ids = [o.get("material_id", 0) for o in bpy.context.scene.objects if "material_id" in o]
                next_id = max(used_ids, default=0) + 1
                obj["material_id"] = next_id
            else:
                # Keep the same material ID if it already exists
                obj["material_id"] = obj.get("material_id")

            # Create or get an existing material based on the selected material properties
            material_name = settings.selected_material
            if material_name not in bpy.data.materials:
                mat = bpy.data.materials.new(name=material_name)
            else:
                mat = bpy.data.materials[material_name]

            # Set material properties (for later visualization or export)
            mat["material_type"] = settings.materials_type
            mat["material_E"] = settings.materials_E
            mat["material_nu"] = settings.materials_nu
            mat["material_rho"] = settings.materials_rho

            # Enable 'use_nodes' if not already
            if not mat.use_nodes:
                mat.use_nodes = True

            # Link the material to the object
            if obj.data.materials:
                obj.data.materials[0] = mat  # Replace existing material
            else:
                obj.data.materials.append(mat)  # Add new material to the mesh

            self.report({'INFO'}, f"Material '{material_name}' applied to {obj.name} (ID: {obj['material_id']})")
        else:
            self.report({'ERROR'}, f"Object {self.obj_name} not found or is not a mesh")

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
        # only meshes can be exported
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        settings = context.scene.polyfem_settings

        # Start the background thread for JSON creation and mesh exporting
        threading.Thread(target=self.background_process, args=(selected_objects, context), daemon=True).start()

        # Register a timer to process the report queue
        bpy.app.timers.register(self.process_report_queue)
        self.report({'INFO'}, "Started JSON creation and mesh exporting in the background.")
        return {'FINISHED'}

    def background_process(self, selected_objects, context):
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
            json_data = self.create_json_data(settings, context, selected_objects)
            self.report_queue.put(('INFO', "JSON data structure created successfully."))
        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to create JSON data structure: {e}"))
            return

        def update_main_thread():
            try:
                if not os.path.exists(project_path):
                    os.makedirs(project_path)
                    self.report_queue.put(('INFO', f"Created project directory at '{project_path}'"))

                output_mesh_dir = os.path.join(project_path, "exported_meshes")
                if not os.path.exists(output_mesh_dir):
                    os.makedirs(output_mesh_dir)
                    self.report_queue.put(('INFO', f"Created mesh export directory at '{output_mesh_dir}'"))

                # Write the JSON file
                self.write_json_file(json_data, json_path)
                self.report_queue.put(('INFO', f"JSON file created at '{json_path}'"))

            except Exception as e:
                self.report_queue.put(('ERROR', f"Failed to create directories or write JSON: {e}"))

            return None

        bpy.app.timers.register(update_main_thread)

        current_id = 1
        geometry_list = []
        docker_futures = []

        for obj in selected_objects:
            if obj.type != 'MESH':
                self.report_queue.put(('WARNING', f"Skipping non-mesh object '{obj.name}'.")) 
                continue

            output_mesh_dir = os.path.join(project_path, "exported_meshes")
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
        output_mesh_dir = os.path.join(project_path, "exported_meshes")
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
        obj_data["is_obstacle"] = obj.polyfem_props.is_obstacle

        # Retrieve the export type from the object's properties
        export_type = obj.polyfem_props.export_type

        # Export mesh based on execution mode and export type
        if export_type == 'STL':
            self.report_queue.put(('INFO', f"Exporting {obj.name} as STL."))
            export_success = self.export_mesh(obj, os.path.join(output_dir, f"{obj.name}.stl"), settings, export_format='STL')
            if not export_success:
                self.report_queue.put(('ERROR', f"Failed to export STL for object '{obj.name}'"))
                return None
            obj_data["mesh"] = f"{obj.name}.stl"
        elif export_type == 'MSH':
            self.report_queue.put(('INFO', f"Exporting {obj.name} as MSH using TetWild."))
            # Use the TetWild execution mode and parameters
            success = self.export_mesh_using_tetwild(obj, output_dir, settings)
            if not success:
                self.report_queue.put(('ERROR', f"Failed to export MSH for object '{obj.name}'"))
                return None
            obj_data["mesh"] = f"{obj.name}.msh"
        else:
            self.report_queue.put(('ERROR', f"Unsupported export type '{export_type}' for object '{obj.name}'"))
            return None

        obj_data["transformation"] = {
            "translation": list(obj.location),
            "rotation": list(obj.rotation_quaternion),
            "scale": list(obj.scale),
        }

        return obj_data
    
    def export_mesh_using_tetwild(self, obj, output_dir, settings):
        """Use TetWild to export the mesh as MSH."""
        try:
            # Export mesh to STL first
            temp_stl_filepath = os.path.join(output_dir, f"{obj.name}_temp.stl")
            success_stl = self.export_mesh_to_stl(obj, temp_stl_filepath)

            if success_stl:
                msh_filepath = os.path.join(output_dir, f"{obj.name}.msh")
                if settings.execution_mode_tetwild == 'DOCKER':
                    self.report_queue.put(('INFO', f"Processing {obj.name} using Docker."))
                    success = self.export_mesh_using_docker(obj, output_dir, settings)
                elif settings.execution_mode_tetwild == 'EXECUTABLE':
                    self.report_queue.put(('INFO', f"Processing {obj.name} using Executable."))
                    success = self.export_mesh_using_executable(obj, output_dir, settings.executable_path_polyfem)
                return True
            return False
        except Exception as e:
            self.report_queue.put(('ERROR', f"Error using TetWild: {e}"))
            return False

    def export_mesh_using_docker(self, obj, output_dir, settings):
        """Use Docker to export the mesh."""
        try:
            temp_stl_filepath = os.path.join(output_dir, f"{obj.name}_temp.stl")
            success_stl = self.export_mesh_to_stl(obj, temp_stl_filepath)

            if success_stl:
                msh_filepath = os.path.join(output_dir, f"{obj.name}.msh")
                future = self.docker_executor.submit(
                    self.run_tetwild, temp_stl_filepath, msh_filepath
                )
                return True
            return False
        except Exception as e:
            self.report_queue.put(('ERROR', f"Error using Docker: {e}"))
            return False

    def export_mesh_using_executable(self, obj, output_dir, executable_path):
        """Use the PolyFem executable to export the mesh."""
        if not os.path.isfile(executable_path):
            self.report_queue.put(('ERROR', f"Executable not found at path: {executable_path}"))
            return False

        mesh_filepath = os.path.join(output_dir, f"{obj.name}.msh")

        command = [executable_path, '--input', mesh_filepath, '--output', output_dir]

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            self.report_queue.put(('INFO', f"Mesh exported successfully using executable for '{obj.name}'."))
            return True
        except subprocess.CalledProcessError as e:
            self.report_queue.put(('ERROR', f"Error exporting with executable: {e.stderr}"))
        except Exception as e:
            self.report_queue.put(('ERROR', f"Unexpected error: {e}"))
        return False

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

    def run_tetwild(self, input_file, output_file):
        """Run TetWild via Docker to generate an MSH file from a mesh with enhanced parameters."""
        try:
            settings = bpy.context.scene.polyfem_settings
            ideal_edge_length = settings.tetwild_max_tets / 100000.0  # Example scaling
            epsilon = settings.tetwild_min_tets / 100000.0
            filter_energy = settings.tetwild_mesh_quality * 100
            max_pass = 80  # Existing parameter

            # Get the absolute path of the input and output directories
            input_dir = os.path.abspath(os.path.dirname(input_file))
            output_dir = os.path.abspath(os.path.dirname(output_file))

            # Adjust paths for Windows if necessary
            if platform.system() == 'Windows':
                input_dir = input_dir.replace('\\', '/')
                output_dir = output_dir.replace('\\', '/')
                if input_dir[1] == ':':
                    input_dir = f'/{input_dir[0].lower()}{input_dir[2:]}'
                if output_dir[1] == ':':
                    output_dir = f'/{output_dir[0].lower()}{output_dir[2:]}'

            # Build the TetWild Docker command with new parameters
            container_name = f"tetwild_{os.path.basename(input_file)}"
            command = [
                "docker", "run", "--rm", "--name", container_name,
                "-v", f"{input_dir}:/data",
                "yixinhu/tetwild:latest",  # Ensure you're using the correct tag
                "--input", f"/data/{os.path.basename(input_file)}",
                "--ideal-edge-length", str(ideal_edge_length),
                "--epsilon", str(epsilon),
                "--filter-energy", str(filter_energy),
                "--max-pass", str(max_pass),
                "--output", f"/data/{os.path.basename(output_file)}"
            ]

            # Execute the command
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            self.report_queue.put(('INFO', f"TetWild ran successfully with input: {input_file}"))
            self.report_queue.put(('INFO', f"TetWild Output:\n{result.stdout}"))
            if result.stderr:
                self.report_queue.put(('WARNING', f"TetWild Warnings:\n{result.stderr}"))
            self.report_queue.put(('INFO', f"Generated MSH file at '{output_file}'"))
            self.cleanup_docker_container(container_name)
            return True
        except FileNotFoundError:
            self.report_queue.put(('ERROR', "Docker not found. Please ensure Docker is installed and in your system's PATH."))
            return False
        except subprocess.CalledProcessError as e:
            self.cleanup_docker_container(container_name)
            self.report_queue.put(('ERROR', f"Error running TetWild:\n{e.stderr}"))
            return False
        except Exception as e:
            self.cleanup_docker_container(container_name)
            self.report_queue.put(('ERROR', f"An unexpected error occurred while running TetWild:\n{e}"))
            return False

    def cleanup_docker_container(self, container_name):
        """Manually stop and remove any lingering Docker containers by name."""
        try:
            # Check if the container exists
            subprocess.run(["docker", "container", "inspect", container_name], check=True, stdout=subprocess.PIPE)

            # If it exists, remove it
            self.report_queue.put(('INFO', f"Cleaning up Docker container '{container_name}'..."))
            subprocess.run(["docker", "container", "rm", "-f", container_name], check=True, stdout=subprocess.PIPE)
            self.report_queue.put(('INFO', f"Docker container '{container_name}' cleaned up successfully."))

        except subprocess.CalledProcessError:
            self.report_queue.put(('INFO', f"No lingering Docker container '{container_name}' found, cleanup not needed."))
        except Exception as e:
            self.report_queue.put(('ERROR', f"Error during Docker container cleanup: {e}"))

    def create_json_data(self, settings, context, selected_objects):
        """Create the initial JSON data structure based on settings."""
        materials_list = []  # List of materials for the global materials section
        materials_map = {}  # Map to avoid duplicate materials
        geometry_list = []  # List of objects (geometry)

        # Loop through all objects and assign materials
        for obj in selected_objects:
            if obj.type == 'MESH':
                # Check if the object has custom material properties
                material_data = {
                    "id": obj.get("material_id", 0),
                    "type": obj.get("material", settings.materials_type),
                    "E": round(obj.get("material_E", settings.materials_E), 6),
                    "nu": round(obj.get("material_nu", settings.materials_nu), 4),
                    "rho": round(obj.get("material_rho", settings.materials_rho), 6)
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
                settings = context.scene.polyfem_settings
                project_path = bpy.path.abspath(settings.export_path)
                obj_data = self.process_object(obj, material_id, project_path, settings, context)
                if obj_data:
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
            "materials": materials_list,
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
            "geometry": geometry_list
        }

        return json_data

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
                def float_precision(o):
                    if isinstance(o, float):
                        return format(o, ".6f")  # Use 6 decimal places for floats
                    raise TypeError(f"Object of type {type(o)} is not JSON serializable")

                json.dump(data, json_file, indent=4, default=float_precision)
            self.report_queue.put(('INFO', f"JSON file created at '{json_path}'"))
            return True
        except Exception as e:
            self.report_queue.put(('ERROR', f"Failed to create JSON file: {e}"))
            return False

    def process_report_queue(self):
        """Process messages from the report queue and display them to the user."""
        while not self.report_queue.empty():
            level, message = self.report_queue.get()
            self.report({level}, message)
        return 0.1

    def show_popup(self, message, title, icon):
        """Helper function to display a popup message box"""
        bpy.ops.polyfem.show_message_box('INVOKE_DEFAULT', message=message, title=title, icon=icon)
        return None
