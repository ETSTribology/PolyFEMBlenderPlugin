import bpy
import os
import subprocess
from .._vendor import meshio
from bpy.types import Operator
import webbrowser
import math
import numpy as np
import mathutils
import tempfile
from datetime import datetime
import threading
import concurrent.futures

class RunPolyFemSimulationOperator(Operator):
    """Run PolyFem simulation"""
    bl_idname = "polyfem.run_simulation"
    bl_label = "Run PolyFem Simulation"
    bl_description = "Run PolyFem simulation to generate VTU files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        polyfem_settings = context.scene.polyfem_settings
        project_path = bpy.path.abspath(polyfem_settings.project_path)

        if not os.path.exists(project_path):
            self.report({'ERROR'}, f"Project directory '{project_path}' does not exist.")
            return {'CANCELLED'}

        # Run PolyFem simulation
        if not self.run_polyfem_simulation(context):
            return {'CANCELLED'}

        self.report({'INFO'}, "PolyFem simulation completed successfully.")
        return {'FINISHED'}

    def run_polyfem_simulation(self, context):
        """Run the PolyFem simulation with the provided JSON config"""
        polyfem_settings = context.scene.polyfem_settings
        executable_path = bpy.path.abspath(polyfem_settings.polyfem_executable_path)
        json_input = bpy.path.abspath(polyfem_settings.polyfem_json_input)
        project_path = bpy.path.abspath(polyfem_settings.project_path)

        if not os.path.isfile(executable_path):
            self.report({'ERROR'}, f"PolyFem executable '{executable_path}' not found.")
            return False

        if not os.path.isfile(json_input):
            self.report({'ERROR'}, f"PolyFem JSON input file '{json_input}' not found.")
            return False

        # Execute PolyFem
        try:
            result = subprocess.run(
                [executable_path, "--json", json_input],
                capture_output=True,
                text=True,
                check=True,
                cwd=project_path  # Ensure the simulation runs in the project directory
            )
            self.report({'INFO'}, f"PolyFem Output:\n{result.stdout}")
            if result.stderr:
                self.report({'WARNING'}, f"PolyFem Warnings:\n{result.stderr}")
            return True
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f"PolyFem simulation failed:\n{e.stderr}")
            return False
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred while running PolyFem:\n{e}")
            return False


class RenderPolyFemAnimationOperator(Operator):
    """Convert VTU files to OBJ, import them as separate objects, and set up visibility animation."""
    bl_idname = "polyfem.render_animation"
    bl_label = "Render PolyFem Animation"
    bl_description = "Convert VTU files to OBJ, import as separate objects, and animate visibility."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        polyfem_settings = context.scene.polyfem_settings
        project_path = bpy.path.abspath(polyfem_settings.project_path)
        start_frame = polyfem_settings.start_frame
        frame_interval = polyfem_settings.frame_interval  # Make frame_interval configurable
        scale_factor = polyfem_settings.scale_factor      # Make scale_factor configurable

        if not os.path.exists(project_path):
            self.report({'ERROR'}, f"Project directory '{project_path}' does not exist.")
            return {'CANCELLED'}

        # Define obj_folder
        obj_folder = os.path.join(project_path, "obj")
        os.makedirs(obj_folder, exist_ok=True)

        # Step 1: Read and sort VTU files
        try:
            vtu_files = [f for f in os.listdir(project_path) if f.startswith("step_") and f.endswith(".vtu")]
            if not vtu_files:
                self.report({'ERROR'}, "No VTU files found in the specified directory.")
                return {'CANCELLED'}
            # Sort files based on the numeric value after 'step_'
            vtu_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
            self.report({'INFO'}, f"Found {len(vtu_files)} VTU files.")
        except Exception as e:
            self.report({'ERROR'}, f"Error retrieving VTU files: {e}")
            return {'CANCELLED'}

        # Step 2: Create a collection for animation frames
        collection_name = "AnimationFrames"
        collection = self.ensure_collection(collection_name)

        # Step 3: Convert VTU to OBJ in separate threads
        conversion_errors = []
        obj_file_paths = []

        def convert_vtu_wrapper(vtu_file):
            vtu_path = os.path.join(project_path, vtu_file)
            obj_filename = f"{os.path.splitext(vtu_file)[0]}.obj"
            obj_path = os.path.join(obj_folder, obj_filename)

            if not os.path.exists(obj_path):
                try:
                    tmp_obj_path = self.convert_vtu_to_obj(vtu_path, scale_factor)
                    os.rename(tmp_obj_path, obj_path)
                    self.report({'INFO'}, f"Converted '{vtu_file}' to OBJ.")
                except Exception as e:
                    error_msg = f"Failed to convert '{vtu_file}': {e}"
                    self.report({'ERROR'}, error_msg)
                    conversion_errors.append(error_msg)
                    return None
            else:
                self.report({'INFO'}, f"OBJ already exists for '{vtu_file}'. Skipping conversion.")

            return obj_path

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(convert_vtu_wrapper, vtu): vtu for vtu in vtu_files}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    obj_file_paths.append(result)

        if conversion_errors and not obj_file_paths:
            self.report({'ERROR'}, "All conversions failed. Animation setup aborted.")
            return {'CANCELLED'}
        elif conversion_errors:
            self.report({'WARNING'}, f"Some conversions failed: {conversion_errors}")

        if not obj_file_paths:
            self.report({'ERROR'}, "No OBJ files to import. Animation setup aborted.")
            return {'CANCELLED'}

        # Step 4: Import OBJ files on the main thread
        imported_objects = []
        import_errors = []

        for idx, obj_path in enumerate(obj_file_paths):
            try:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.import_scene.obj(filepath=obj_path)
                imported_objs = bpy.context.selected_objects.copy()
                if not imported_objs:
                    warning_msg = f"No objects imported from '{obj_path}'."
                    self.report({'WARNING'}, warning_msg)
                    import_errors.append(warning_msg)
                    continue
                imported_obj = imported_objs[0]  # Assuming single object per OBJ
                imported_obj.name = f"Frame_{idx}"
                collection.objects.link(imported_obj)
                bpy.context.scene.collection.objects.unlink(imported_obj)
                imported_objects.append(imported_obj)
                self.report({'INFO'}, f"Imported '{imported_obj.name}'.")
            except Exception as e:
                error_msg = f"Failed to import '{obj_path}': {e}"
                self.report({'ERROR'}, error_msg)
                import_errors.append(error_msg)

        if import_errors and not imported_objects:
            self.report({'ERROR'}, "All imports failed. Animation setup aborted.")
            return {'CANCELLED'}
        elif import_errors:
            self.report({'WARNING'}, f"Some imports failed: {import_errors}")

        # Step 5: Set up visibility keyframes
        self.setup_visibility_keyframes(imported_objects, start_frame, frame_interval)

        self.report({'INFO'}, "Animation rendering completed successfully.")
        return {'FINISHED'}

    def get_sorted_vtu_files(self, project_path):
        """Retrieve and sort VTU files based on step number."""
        try:
            vtu_files = [f for f in os.listdir(project_path) if f.startswith("step_") and f.endswith(".vtu")]
            if not vtu_files:
                return []
            # Sort files based on the numeric value after 'step_'
            vtu_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
            self.report({'INFO'}, f"Found {len(vtu_files)} VTU files.")
            return vtu_files
        except Exception as e:
            self.report({'ERROR'}, f"Error retrieving VTU files: {e}")
            return []

    def ensure_collection(self, collection_name):
        """Ensure that a collection exists; if not, create it."""
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        return collection

    def convert_vtu_to_obj(self, vtu_path, scale_factor=1.0):
        """Convert a VTU file to a deformed OBJ file."""
        mesh = meshio.read(vtu_path)
        triangle_cells, deformed_points = self.get_triangle_cells(mesh, scale_factor)

        # Create a meshio Mesh object with triangles
        deformed_mesh = meshio.Mesh(
            points=deformed_points,
            cells=[("triangle", triangle_cells)],
        )

        # Write to a temporary OBJ file
        tmp_obj = tempfile.NamedTemporaryFile(delete=False, suffix=".obj")
        meshio.write(tmp_obj.name, deformed_mesh)

        return tmp_obj.name  # Return the path to the temporary OBJ file

    def get_triangle_cells(self, mesh, scale_factor=1.0):
        """Extract triangle cells and apply deformation."""
        solution_vectors = mesh.point_data.get("solution")
        points = mesh.points

        if solution_vectors is not None:
            deformed_points = points + scale_factor * solution_vectors
        else:
            self.report({'WARNING'}, "No 'solution' data found, using original points.")
            deformed_points = points

        triangles = []
        for cell_block in mesh.cells:
            if cell_block.type == "triangle":
                triangles.extend(cell_block.data.tolist())
            elif cell_block.type == "tetra":
                triangles.extend(self.get_tetra_faces(cell_block.data))
            elif cell_block.type == "hexahedron":
                triangles.extend(self.get_hexa_faces(cell_block.data))
            elif cell_block.type == "quad":
                triangles.extend(self.get_quad_faces(cell_block.data))
            else:
                self.report({'WARNING'}, f"Unsupported cell type '{cell_block.type}' encountered and skipped.")

        self.report({'INFO'}, f"Converted cells to triangles. Total triangles: {len(triangles)}")
        # Convert all triangle indices to integers
        triangles = [list(map(int, face)) for face in triangles]
        return triangles, deformed_points

    def get_tetra_faces(self, cells):
        """Extract triangular faces from tetrahedral cells."""
        triangles = []
        for cell in cells:
            triangles.append([cell[0], cell[1], cell[2]])
            triangles.append([cell[0], cell[1], cell[3]])
            triangles.append([cell[0], cell[2], cell[3]])
            triangles.append([cell[1], cell[2], cell[3]])
        return triangles

    def get_hexa_faces(self, cells):
        """Extract triangular faces from hexahedral cells."""
        triangles = []
        for cell in cells:
            # Each hexahedron has 6 faces; each face can be split into 2 triangles
            faces = [
                [cell[0], cell[1], cell[2], cell[3]],  # Front
                [cell[4], cell[5], cell[6], cell[7]],  # Back
                [cell[0], cell[1], cell[5], cell[4]],  # Bottom
                [cell[2], cell[3], cell[7], cell[6]],  # Top
                [cell[0], cell[3], cell[7], cell[4]],  # Left
                [cell[1], cell[2], cell[6], cell[5]],  # Right
            ]
            for face in faces:
                triangles.append([face[0], face[1], face[2]])
                triangles.append([face[0], face[2], face[3]])
        return triangles

    def get_quad_faces(self, cells):
        """Convert quads to triangles."""
        triangles = []
        for quad in cells:
            triangles.append([quad[0], quad[1], quad[2]])
            triangles.append([quad[0], quad[2], quad[3]])
        return triangles

    def import_obj_as_object(self, obj_path, collection):
        """Import an OBJ file and add it to a specified collection."""
        # Deselect all objects before import
        bpy.ops.object.select_all(action='DESELECT')

        # Import the OBJ file using the correct operator
        bpy.ops.wm.obj_import(filepath=obj_path)

        # The imported objects are selected after import
        imported_objects = bpy.context.selected_objects.copy()

        # Move imported objects to the specified collection
        for obj in imported_objects:
            collection.objects.link(obj)
            bpy.context.scene.collection.objects.unlink(obj)

        return imported_objects  # Return the list of imported objects

    def setup_visibility_keyframes(self, objects, start_frame, frame_interval=1):
        for idx, obj in enumerate(objects):
            frame = start_frame + idx

            # Initially hide the object
            obj.hide_viewport = True
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=start_frame - 1)
            obj.keyframe_insert(data_path="hide_render", frame=start_frame - 1)

            # Make it visible at the target frame
            obj.hide_viewport = False
            obj.hide_render = False
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)
            obj.keyframe_insert(data_path="hide_render", frame=frame)

            # Make it invisible immediately after
            obj.hide_viewport = True
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=frame + 1)
            obj.keyframe_insert(data_path="hide_render", frame=frame + 1)

            self.report({'INFO'}, f"Visibility keyframes set for '{obj.name}' at frame {frame}.")

class OpenPolyFemDocsOperator(Operator):
    """Open PolyFem documentation in a browser"""
    bl_idname = "polyfem.open_docs"
    bl_label = "Open PolyFem Documentation"
    bl_description = "Open PolyFem documentation in the default web browser"

    def execute(self, context):
        webbrowser.open("https://polyfem.github.io/json_defaults_and_spec/?h=json+s")
        return {'FINISHED'}