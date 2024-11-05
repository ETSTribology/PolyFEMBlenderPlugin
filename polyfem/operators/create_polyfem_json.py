import bpy
import json
import os
import subprocess
import bmesh
import math
import platform
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, IntProperty
from bpy.types import Operator
import logging
import re

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

    docker_image: StringProperty(name="Docker Image", default="yixinhu/tetwild")  # type: ignore

    def execute(self, context):
        # Check if Docker is installed
        if is_docker_installed():
            if self.docker_image:
                pull_docker_image(self.docker_image)
                return {'FINISHED'}
            else:
                display_message("No Docker image specified.", icon='ERROR')
                return {'CANCELLED'}
        else:
            display_message("Docker is not installed. Please install Docker to proceed.", icon='ERROR')
            return {'CANCELLED'}

def display_message(message, title="Notification", icon='INFO'):
    """Display a popup message immediately."""
    bpy.ops.polyfem.show_message_box('INVOKE_DEFAULT', message=message, title=title, icon=icon)

def is_docker_installed():
    """Check if Docker is installed and available on the machine."""
    try:
        result = subprocess.run(["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Docker not found: {e}")
        return False

def pull_docker_image(docker_image):
    """Pull a Docker image synchronously."""
    try:
        logger.info(f"Pulling Docker image '{docker_image}'...")
        subprocess.run(["docker", "pull", docker_image], check=True)
        logger.info(f"Pulled Docker image '{docker_image}' successfully.")
        display_message(f"Successfully pulled Docker image '{docker_image}'", icon='INFO')
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to pull Docker image '{docker_image}': {e}")
        display_message(f"Failed to pull Docker image '{docker_image}'. Check console for details.", icon='ERROR')
    except Exception as e:
        logger.error(f"Error pulling Docker image '{docker_image}': {e}")
        display_message(f"Error pulling Docker image '{docker_image}': {e}", title="Error", icon='ERROR')

# ----------------------------
# Popup Message Box Operator
# ----------------------------
class POLYFEM_OT_ShowMessageBox(Operator):
    """Show a popup message box"""
    bl_idname = "polyfem.show_message_box"
    bl_label = "PolyFem Notification"
    bl_options = {'REGISTER'}

    message: StringProperty(name="Message")  # type: ignore
    title: StringProperty(name="Title", default="PolyFem Notification")  # type: ignore
    icon: EnumProperty(
        name="Icon",
        items=[
            ('INFO', "Info", "Information"),
            ('ERROR', "Error", "Error"),
            ('WARNING', "Warning", "Warning"),
            ('NONE', "None", "No Icon"),
        ],
        default='INFO'
    )  # type: ignore

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

    obj_name: StringProperty()  # type: ignore

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

    def execute(self, context):
        # Only meshes can be exported
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        settings = context.scene.polyfem_settings

        if settings.export_selected_only and not selected_objects:
            self.report({'ERROR'}, "No selected objects to export.")
            display_message("No selected objects to export.", icon='ERROR')
            return {'CANCELLED'}
        elif not selected_objects and not settings.export_selected_only:
            selected_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
            logger.info(f"Selected objects: {selected_objects}")

        project_path = bpy.path.abspath(settings.export_path)
        json_filename = settings.json_filename
        json_path = os.path.join(project_path, json_filename)

        # Ensure the project directory exists
        if not os.path.exists(project_path):
            try:
                os.makedirs(project_path)
                self.report({'INFO'}, f"Created project directory at '{project_path}'")
                display_message(f"Created project directory at '{project_path}'", icon='INFO')
            except Exception as e:
                self.report({'ERROR'}, f"Failed to create project directory: {e}")
                display_message(f"Failed to create project directory: {e}", icon='ERROR')
                return {'CANCELLED'}

        # Create JSON data structure
        try:
            json_data = self.create_json_data(settings, context, selected_objects)
            self.report({'INFO'}, "JSON data structure created successfully.")
            display_message("JSON data structure created successfully.", icon='INFO')
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create JSON data structure: {e}")
            display_message(f"Failed to create JSON data structure: {e}", icon='ERROR')
            return {'CANCELLED'}

        output_mesh_dir = os.path.join(project_path, "exported_meshes")
        if not os.path.exists(output_mesh_dir):
            try:
                os.makedirs(output_mesh_dir)
                self.report({'INFO'}, f"Created mesh export directory at '{output_mesh_dir}'")
                display_message(f"Created mesh export directory at '{output_mesh_dir}'", icon='INFO')
            except Exception as e:
                self.report({'ERROR'}, f"Failed to create mesh export directory: {e}")
                display_message(f"Failed to create mesh export directory: {e}", icon='ERROR')
                return {'CANCELLED'}

        geometry_list = []
        docker_futures = []

        for obj in selected_objects:
            if obj.type != 'MESH':
                self.report({'WARNING'}, f"Skipping non-mesh object '{obj.name}'.")
                display_message(f"Skipping non-mesh object '{obj.name}'.", icon='WARNING')
                continue

            obj_data = self.process_object(obj, output_mesh_dir, settings, context)
            if obj_data is None:
                self.report({'ERROR'}, f"Failed to process object '{obj.name}'.")
                display_message(f"Failed to process object '{obj.name}'.", icon='ERROR')
                continue

            geometry_list.append(obj_data)

        json_data["geometry"] = geometry_list

        # Write the JSON configuration file
        try:
            self.write_json_file(json_data, json_path)
            self.report({'INFO'}, f"JSON file created at '{json_path}'")
            display_message(f"JSON file created at '{json_path}'", icon='INFO')
        except Exception as e:
            self.report({'ERROR'}, f"Failed to write JSON file: {e}")
            display_message(f"Failed to write JSON file: {e}", icon='ERROR')
            return {'CANCELLED'}

        self.report({'INFO'}, f"Meshes exported successfully in '{output_mesh_dir}'")
        display_message(f"Meshes exported successfully in '{output_mesh_dir}'", icon='INFO')

        # Handle Docker tasks synchronously if any
        if docker_futures:
            self.report({'INFO'}, "Waiting for all Docker tasks to complete...")
            display_message("Waiting for all Docker tasks to complete...", icon='INFO')
            concurrent.futures.wait(docker_futures)
            self.report({'INFO'}, "All Docker tasks completed.")
            display_message("All Docker tasks completed.", icon='INFO')

        return {'FINISHED'}

    def process_object(self, obj, output_dir, settings, context):
        """Process an individual object and collect its data."""
        obj_data = {}
        obj_data["volume_selection"] = obj.get("material_id", 0)
        obj_data["is_obstacle"] = getattr(obj, "polyfem_props", {}).get("is_obstacle", False)
        obj_data["export_type"] = obj.polyfem_props.export_type.upper()

        print(f"Processing object '{obj.name}' with export type: {obj_data['export_type']}")

        # Retrieve the export type from the object's properties
        logger.info(f"Export type for '{obj.name}': {obj_data['export_type']}")

        mesh_filename = f"{obj.name}.{obj_data['export_type'].lower()}"
        mesh_filepath = os.path.join(output_dir, mesh_filename)
        success = self.export_mesh(obj, mesh_filepath, settings)
        if not success:
            self.report({'ERROR'}, f"Failed to export mesh for object '{obj.name}'")
            display_message(f"Failed to export mesh for object '{obj.name}'", icon='ERROR')
            return None

        obj_data["mesh"] = mesh_filename
        obj_data["material"] = obj.get("material_id", 0)

        if settings.export_point_selection:
            point_selection = self.get_point_selection(obj, context)
            if point_selection:
                obj_data["point_selection"] = point_selection

        if obj_data["export_type"] == 'MSH':
            temp_stl_filepath = os.path.join(os.path.dirname(mesh_filepath), f"{obj.name}_temp.stl")
            success_stl = self.export_mesh_to_stl(obj, temp_stl_filepath)
            if not success_stl:
                self.report({'ERROR'}, f"Failed to export {obj.name} to STL format for TetWild.")
                display_message(f"Failed to export {obj.name} to STL format for TetWild.", icon='ERROR')
                return None

            # Define output MSH filepath
            msh_filepath = mesh_filepath
            if settings.execution_mode_tetwild == 'DOCKER':
                # Use TetWild via Docker to export the mesh as MSH
                success = self.export_mesh_using_tetwild(obj, output_dir, settings)
                if not success:
                    return None
            elif settings.execution_mode_tetwild == 'EXECUTABLE':
                # Use the PolyFem executable to export the mesh as MSH
                success = self.export_mesh_using_executable(obj, output_dir, settings.executable_path_polyfem)
                if not success:
                    self.report({'ERROR'}, f"Failed to export {obj.name} using PolyFem executable.")
                    display_message(f"Failed to export {obj.name} using PolyFem executable.", icon='ERROR')
                    return None

        obj_data["transformation"] = {
            "translation": list(obj.location),
            "rotation": list(obj.rotation_quaternion.to_euler()),
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
                success = self.run_tetwild(temp_stl_filepath, msh_filepath, settings)
                return success
            return False
        except Exception as e:
            self.report({'ERROR'}, f"Error using TetWild: {e}")
            display_message(f"Error using TetWild: {e}", icon='ERROR')
            return False

    def export_mesh_using_executable(self, obj, output_dir, executable_path):
        """Use the PolyFem executable to export the mesh."""
        if not os.path.isfile(executable_path):
            self.report({'ERROR'}, f"Executable not found at path: {executable_path}")
            display_message(f"Executable not found at path: {executable_path}", icon='ERROR')
            return False

        mesh_filepath = os.path.join(output_dir, f"{obj.name}.msh")

        command = [executable_path, '--input', mesh_filepath, '--output', output_dir]

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            self.report({'INFO'}, f"Mesh exported successfully using executable for '{obj.name}'.")
            display_message(f"Mesh exported successfully using executable for '{obj.name}'.", icon='INFO')
            return True
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f"Error exporting with executable: {e.stderr}")
            display_message(f"Error exporting with executable: {e.stderr}", icon='ERROR')
        except Exception as e:
            self.report({'ERROR'}, f"Unexpected error: {e}")
            display_message(f"Unexpected error: {e}", icon='ERROR')
        return False

    def export_mesh(self, obj, mesh_filepath, settings):
        """Export the mesh of an object based on the selected format."""
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            self.report({'WARNING'}, "Could not set mode to OBJECT. Proceeding anyway.")
            display_message("Could not set mode to OBJECT. Proceeding anyway.", icon='WARNING')

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        export_format = obj.polyfem_props.export_type.upper()

        try:
            if export_format == 'STL':
                return self.export_mesh_to_stl(obj, mesh_filepath)
            elif export_format == 'OBJ':
                return self.export_mesh_to_obj(obj, mesh_filepath)
            elif export_format == 'FBX':
                self.report({'ERROR'}, "FBX export is not supported without the FBX addon.")
                display_message("FBX export is not supported without the FBX addon.", icon='ERROR')
                return False
            elif export_format == 'GLTF':
                self.report({'ERROR'}, "GLTF export is not supported without the GLTF addon.")
                display_message("GLTF export is not supported without the GLTF addon.", icon='ERROR')
                return False
            elif export_format == 'MSH':
                # Export to STL format for TetWild
                temp_stl_filepath = os.path.join(os.path.dirname(mesh_filepath), f"{obj.name}_temp.stl")
                success = self.export_mesh_to_stl(obj, temp_stl_filepath)
                if not success:
                    self.report({'ERROR'}, f"Failed to export {obj.name} to STL format for TetWild.")
                    display_message(f"Failed to export {obj.name} to STL format for TetWild.", icon='ERROR')
                    return False
                # TetWild processing is handled separately
                return True
            else:
                self.report({'ERROR'}, f"Unsupported export format: {export_format}")
                display_message(f"Unsupported export format: {export_format}", icon='ERROR')
                return False
        except Exception as e:
            self.report({'ERROR'}, f"Error exporting {obj.name}: {e}")
            display_message(f"Error exporting {obj.name}: {e}", icon='ERROR')
            return False

    def export_mesh_to_stl(self, obj, filepath):
        try:
            bpy.ops.object.select_all(action='DESELECT')

            if bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            obj.select_set(True)

            # Define export parameters
            export_params = {
                "filepath": filepath,
                "check_existing": False,
                "export_selected_objects": True,
                "ascii_format": False
            }

            # Perform the STL export
            bpy.ops.wm.stl_export(**export_params)

            # Report success
            obj_name = ', '.join([obj.name for obj in bpy.context.selected_objects])
            self.report({'INFO'}, f"Exported STL for objects '{obj_name}' at '{filepath}'")
            display_message(f"Exported STL for objects '{obj_name}' at '{filepath}'", icon='INFO')
            return True

        except Exception as e:
            # Report failure
            self.report({'ERROR'}, f"Failed to export STL: {e}")
            display_message(f"Failed to export STL: {e}", icon='ERROR')
            return False

    def export_mesh_to_obj(self, obj, filepath):
        """Exports the mesh data of an object to an OBJ file."""

        try:
            bpy.ops.object.select_all(action='DESELECT')

            if bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            obj.select_set(True)

            # Define export parameters
            export_params = {
                "filepath": filepath,
                "check_existing": False,
                "export_selected_objects": True,
                "ascii_format": False
            }

            # Perform the obj export
            bpy.ops.wm.obj_export(**export_params)

            # Report success
            obj_name = ', '.join([obj.name for obj in bpy.context.selected_objects])
            self.report({'INFO'}, f"Exported STL for objects '{obj_name}' at '{filepath}'")
            display_message(f"Exported STL for objects '{obj_name}' at '{filepath}'", icon='INFO')
            return True

        except Exception as e:
            # Report failure
            self.report({'ERROR'}, f"Failed to export STL: {e}")
            display_message(f"Failed to export STL: {e}", icon='ERROR')
            return False

    def run_tetwild(self, input_file, output_file, settings):
        """Run TetWild to generate an MSH file from a mesh with enhanced parameters."""
        try:
            ideal_edge_length = settings.tetwild_max_tets
            epsilon = settings.tetwild_min_tets
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
            self.report({'INFO'}, f"TetWild ran successfully with input: {input_file}")
            display_message(f"TetWild ran successfully with input: {input_file}", icon='INFO')

            if result.stdout:
                self.report({'INFO'}, f"TetWild Output:\n{result.stdout}")
                logger.info(f"TetWild Output:\n{result.stdout}")
            if result.stderr:
                self.report({'WARNING'}, f"TetWild Warnings:\n{result.stderr}")
                logger.warning(f"TetWild Warnings:\n{result.stderr}")

            self.report({'INFO'}, f"Generated MSH file at '{output_file}'")
            display_message(f"Generated MSH file at '{output_file}'", icon='INFO')

            # Cleanup Docker container
            self.cleanup_docker_container(container_name)

            return True
        except FileNotFoundError:
            self.report({'ERROR'}, "Docker not found. Please ensure Docker is installed and in your system's PATH.")
            display_message("Docker not found. Please ensure Docker is installed and in your system's PATH.", icon='ERROR')
            return False
        except subprocess.CalledProcessError as e:
            self.cleanup_docker_container(container_name)
            self.report({'ERROR'}, f"Error running TetWild:\n{e.stderr}")
            display_message(f"Error running TetWild:\n{e.stderr}", icon='ERROR')
            return False
        except Exception as e:
            self.cleanup_docker_container(container_name)
            self.report({'ERROR'}, f"An unexpected error occurred while running TetWild:\n{e}")
            display_message(f"An unexpected error occurred while running TetWild:\n{e}", icon='ERROR')
            return False

    def cleanup_docker_container(self, container_name):
        """Manually stop and remove any lingering Docker containers by name."""
        try:
            # Check if the container exists
            subprocess.run(["docker", "container", "inspect", container_name], check=True, stdout=subprocess.PIPE)

            # If it exists, remove it
            self.report({'INFO'}, f"Cleaning up Docker container '{container_name}'...")
            display_message(f"Cleaning up Docker container '{container_name}'...", icon='INFO')
            subprocess.run(["docker", "container", "rm", "-f", container_name], check=True, stdout=subprocess.PIPE)
            self.report({'INFO'}, f"Docker container '{container_name}' cleaned up successfully.")
            display_message(f"Docker container '{container_name}' cleaned up successfully.", icon='INFO')
        except subprocess.CalledProcessError:
            self.report({'INFO'}, f"No lingering Docker container '{container_name}' found, cleanup not needed.")
            logger.info(f"No lingering Docker container '{container_name}' found, cleanup not needed.")
        except Exception as e:
            self.report({'ERROR'}, f"Error during Docker container cleanup: {e}")
            display_message(f"Error during Docker container cleanup: {e}", icon='ERROR')

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
                    "type": obj.get("material_type", settings.materials_type),
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
                obj_data = self.process_object(obj, output_dir=context.scene.polyfem_settings.export_path, settings=settings, context=context)
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

    def get_point_selection(self, obj, context):
        """Retrieve the bounding boxes of selected vertices and format them for JSON."""
        # Save the current mode
        original_mode = obj.mode

        try:
            # Switch to Object Mode to ensure proper access
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.objects.active = obj

            # Get the mesh data
            mesh = obj.data
            selected_verts = [v for v in mesh.vertices if v.select]

            if not selected_verts:
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

            return point_selection

        except Exception as e:
            self.report({'ERROR'}, f"Failed to retrieve point selection for '{obj.name}': {e}")
            display_message(f"Failed to retrieve point selection for '{obj.name}': {e}", icon='ERROR')
            return None

    def write_json_file(self, data, json_path):
        """Write the collected data to a JSON file."""
        try:
            with open(json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            self.report({'INFO'}, f"JSON file created at '{json_path}'")
            display_message(f"JSON file created at '{json_path}'", icon='INFO')
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create JSON file: {e}")
            display_message(f"Failed to create JSON file: {e}", icon='ERROR')
            return False