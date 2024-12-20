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
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import Operator
import webbrowser
import tempfile
import meshio

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
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.message)

    def cancel(self, context):
        """Override the cancel action to behave like execute"""
        return self.execute(context)

# ----------------------------
# Run PolyFem Simulation Operator
# ----------------------------
class RunPolyFemSimulationOperator(Operator):
    """Run PolyFem simulation"""
    bl_idname = "polyfem.run_simulation"
    bl_label = "Run PolyFem Simulation"
    bl_description = "Run PolyFem simulation to generate VTU files"
    bl_options = {'REGISTER', 'UNDO'}

    report_queue = queue.Queue()
    _thread = None

    def execute(self, context):
        polyfem_settings = context.scene.polyfem_settings
        export_path = bpy.path.abspath(polyfem_settings.export_path)

        if not os.path.exists(export_path):
            self.report({'ERROR'}, f"Project directory '{export_path}' does not exist.")
            return {'CANCELLED'}

        if RunPolyFemSimulationOperator._thread and RunPolyFemSimulationOperator._thread.is_alive():
            self.report({'WARNING'}, "PolyFem simulation is already running.")
            return {'CANCELLED'}

        RunPolyFemSimulationOperator._thread = threading.Thread(
            target=self.run_polyfem_simulation,
            args=(context,),
            daemon=True
        )
        RunPolyFemSimulationOperator._thread.start()

        bpy.app.timers.register(self.process_report_queue)
        return {'FINISHED'}

    def run_polyfem_simulation(self, context):
        settings = context.scene.polyfem_settings
        json_input = bpy.path.abspath(settings.json_filename)
        export_path = bpy.path.abspath(settings.export_path)

        if settings.execution_mode_polyfem == 'DOCKER':
            self.run_docker_simulation(json_input, export_path)
        elif settings.execution_mode_polyfem == 'EXECUTABLE':
            self.run_executable_simulation(json_input, export_path, settings.executable_path_polyfem)

    def run_docker_simulation(self, json_input, export_path):
        container_name = "polyfem_simulation"
        command = [
            'docker', 'run', '--rm', '--name', container_name,
            '-v', f'{export_path}:/data',
            'antoinebou12/polyfem',
            '--json', f'/data/{os.path.basename(json_input)}'
        ]
        self.execute_command(command)

    def run_executable_simulation(self, json_input, export_path, executable_path):
        if not os.path.isfile(executable_path):
            self.report_queue.put(('ERROR', f"Executable not found at path: {executable_path}"))
            return

        command = [executable_path, '--json', json_input, '--output', export_path]
        self.execute_command(command)

    def execute_command(self, command):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            self.report_queue.put(('INFO', f"Command Output:\n{result.stdout}"))
            if result.stderr:
                self.report_queue.put(('WARNING', f"Warnings:\n{result.stderr}"))
            self.report_queue.put(('INFO', "PolyFem simulation completed successfully."))
        except subprocess.CalledProcessError as e:
            self.report_queue.put(('ERROR', f"Command failed with error:\n{e.stderr}"))
        except FileNotFoundError:
            self.report_queue.put(('ERROR', "Command not found. Please ensure it is available in the system's PATH."))
        except Exception as e:
            self.report_queue.put(('ERROR', f"Unexpected error:\n{e}"))

    def process_report_queue(self):
        output_log = []  # Store all messages to display at the end
        has_error = False

        while not self.report_queue.empty():
            level, message = self.report_queue.get()
            if level == 'ERROR':
                has_error = True
            output_log.append(message)
            self.report({level}, message)

        if not RunPolyFemSimulationOperator._thread.is_alive():
            bpy.ops.polyfem.show_message_box(
                'INVOKE_DEFAULT',
                message="\n".join(output_log),
                title="PolyFem Simulation Output" if not has_error else "PolyFem Simulation Errors",
                icon='ERROR' if has_error else 'INFO'
            )
            return None
        else:
            return 0.1

    def show_popup(self, message, title, icon):
        bpy.ops.polyfem.show_message_box('INVOKE_DEFAULT', message=message, title=title, icon=icon)

# ----------------------------
# Render PolyFem Animation Operator
# ----------------------------
class RenderPolyFemAnimationOperator(Operator):
    """Convert VTU files to OBJ, import them as separate objects, and set up visibility animation."""
    bl_idname = "polyfem.render_animation"
    bl_label = "Render PolyFem Animation"
    bl_description = "Convert VTU files to OBJ, import as separate objects, and animate visibility."
    bl_options = {'REGISTER', 'UNDO'}

    # Class-level variables to manage threading and importing
    _thread = None
    _obj_file_list = []
    _current_import_index = 0
    _import_in_progress = False

    # Queue for thread-safe reporting
    report_queue = queue.Queue()

    # ThreadPoolExecutor for concurrent conversions
    conversion_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    # Progress bar variables
    total_imports = 0

    def execute(self, context):
        # Prevent multiple instances
        if RenderPolyFemAnimationOperator._thread and RenderPolyFemAnimationOperator._thread.is_alive():
            self.report({'WARNING'}, "Animation rendering is already in progress.")
            return {'CANCELLED'}

        # Reset class variables
        RenderPolyFemAnimationOperator._obj_file_list = []
        RenderPolyFemAnimationOperator._current_import_index = 0
        RenderPolyFemAnimationOperator._import_in_progress = False
        RenderPolyFemAnimationOperator.total_imports = 0

        # Start the background thread
        RenderPolyFemAnimationOperator._thread = threading.Thread(
            target=self.run_animation_process,
            args=(context,),
            daemon=True
        )
        RenderPolyFemAnimationOperator._thread.start()

        # Register the timer to process the report queue and handle imports
        bpy.app.timers.register(self.process_report_queue)

        self.report({'INFO'}, "Started rendering PolyFem animation in the background.")
        return {'FINISHED'}

    def run_animation_process(self, context):
        """Background thread method to handle the animation rendering process."""
        polyfem_settings = context.scene.polyfem_settings
        export_path = bpy.path.abspath(polyfem_settings.export_path)
        start_frame = 0
        frame_interval = 1
        scale_factor = 1

        if not os.path.exists(export_path):
            self.report_queue.put(('ERROR', f"Project directory '{export_path}' does not exist."))
            return

        # Define obj_folder
        obj_folder = os.path.join(export_path, "obj")
        os.makedirs(obj_folder, exist_ok=True)

        # Step 1: Read and sort VTU files
        try:
            vtu_files = [f for f in os.listdir(export_path) if f.startswith("step_") and f.endswith(".vtu")]
            if not vtu_files:
                self.report_queue.put(('ERROR', "No VTU files found in the specified directory."))
                return
            # Sort files based on the numeric value after 'step_'
            vtu_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
            num_steps = len(vtu_files)
            self.report_queue.put(('INFO', f"Found {num_steps} VTU files."))
        except Exception as e:
            self.report_queue.put(('ERROR', f"Error retrieving VTU files: {e}"))
            return

        # Step 2: Convert VTU to OBJ in separate threads
        conversion_errors = []
        obj_file_paths = [None] * len(vtu_files)
        index_map = {vtu_file: index for index, vtu_file in enumerate(vtu_files)}

        def convert_vtu_wrapper(vtu_file):
            vtu_path = os.path.join(export_path, vtu_file)
            obj_filename = f"{os.path.splitext(vtu_file)[0]}.obj"
            obj_path = os.path.join(obj_folder, obj_filename)

            if not os.path.exists(obj_path):
                try:
                    tmp_obj_path = self.convert_vtu_to_obj(vtu_path, scale_factor)
                    os.rename(tmp_obj_path, obj_path)
                    self.report_queue.put(('INFO', f"Converted '{vtu_file}' to OBJ."))
                except Exception as e:
                    error_msg = f"Failed to convert '{vtu_file}': {e}"
                    self.report_queue.put(('ERROR', error_msg))
                    conversion_errors.append(error_msg)
                    return None
            else:
                self.report_queue.put(('INFO', f"OBJ already exists for '{vtu_file}'. Skipping conversion."))

            return obj_path

        # Submit conversion tasks to the executor
        futures = {self.conversion_executor.submit(convert_vtu_wrapper, vtu): vtu for vtu in vtu_files}
        for future in concurrent.futures.as_completed(futures):
            vtu_file = futures[future]
            index = index_map[vtu_file]
            result = future.result()
            if result:
                obj_file_paths[index] = result

        # After conversion, store the list
        RenderPolyFemAnimationOperator._obj_file_list = obj_file_paths
        RenderPolyFemAnimationOperator.total_imports = len(obj_file_paths)

        if conversion_errors and not any(obj_file_paths):
            self.report_queue.put(('ERROR', "All conversions failed. Animation setup aborted."))
            return
        elif conversion_errors:
            self.report_queue.put(('WARNING', f"Some conversions failed: {conversion_errors}"))

        if not any(obj_file_paths):
            self.report_queue.put(('ERROR', "No OBJ files to import. Animation setup aborted."))
            return

        self.report_queue.put(('INFO', "Conversion of VTU files to OBJ completed. Starting import."))

    def process_report_queue(self):
        """Process messages from the report queue and handle OBJ imports."""
        while not self.report_queue.empty():
            level, message = self.report_queue.get()
            self.report({level}, message)

        # Handle OBJ imports sequentially with progress updates
        if RenderPolyFemAnimationOperator._current_import_index < len(RenderPolyFemAnimationOperator._obj_file_list):
            if not RenderPolyFemAnimationOperator._import_in_progress:
                # Start import of the next OBJ file
                RenderPolyFemAnimationOperator._import_in_progress = True
                bpy.app.timers.register(self.import_next_obj)
        else:
            # All OBJ files have been imported; unregister the timer and end progress bar
            bpy.context.window_manager.progress_end()

            # Determine the final status
            if RenderPolyFemAnimationOperator._thread.is_alive():
                # Simulation is still running
                return 0.1  # Continue the timer
            else:
                # Simulation has finished
                # Check if there were any errors during conversion/import
                # For simplicity, assuming messages were already reported
                bpy.ops.polyfem.show_message_box(
                    message="PolyFem animation rendering completed successfully.",
                    title="Animation Render Complete",
                    icon='INFO'
                )
                return None  # Unregister the timer

        return 0.1  # Continue the timer

    def import_next_obj(self):
        """Import the next OBJ file and set up keyframes with a progress bar."""
        if RenderPolyFemAnimationOperator._current_import_index >= len(RenderPolyFemAnimationOperator._obj_file_list):
            RenderPolyFemAnimationOperator._import_in_progress = False
            self.report_queue.put(('INFO', "All OBJ files imported successfully."))
            bpy.context.window_manager.progress_end()
            return None  # Unregister the timer

        obj_path = RenderPolyFemAnimationOperator._obj_file_list[RenderPolyFemAnimationOperator._current_import_index]
        collection = self.ensure_collection("AnimationFrames")
        step_number = RenderPolyFemAnimationOperator._current_import_index + 1
        frame_interval = 1  # Default frame interval
        frame = 1 + (step_number - 1) * frame_interval

        try:
            # Update progress bar
            progress = (RenderPolyFemAnimationOperator._current_import_index / RenderPolyFemAnimationOperator.total_imports) * 100
            bpy.context.window_manager.progress_update(progress)

            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.wm.obj_import(filepath=obj_path)
            imported_objs = bpy.context.selected_objects.copy()
            if not imported_objs:
                warning_msg = f"No objects imported from '{obj_path}'."
                self.report_queue.put(('WARNING', warning_msg))
            else:
                imported_obj = imported_objs[0]  # Assuming single object per OBJ
                imported_obj.name = f"Step_{step_number:03d}"  # e.g., Step_001
                collection.objects.link(imported_obj)
                bpy.context.scene.collection.objects.unlink(imported_obj)

                # Set up visibility keyframes
                # Initially hide the object before its frame
                imported_obj.hide_viewport = True
                imported_obj.hide_render = True
                imported_obj.keyframe_insert(data_path="hide_viewport", frame=frame - frame_interval)
                imported_obj.keyframe_insert(data_path="hide_render", frame=frame - frame_interval)

                # Make it visible at the target frame
                imported_obj.hide_viewport = False
                imported_obj.hide_render = False
                imported_obj.keyframe_insert(data_path="hide_viewport", frame=frame)
                imported_obj.keyframe_insert(data_path="hide_render", frame=frame)

                # Make it invisible immediately after
                imported_obj.hide_viewport = True
                imported_obj.hide_render = True
                imported_obj.keyframe_insert(data_path="hide_viewport", frame=frame + 1)
                imported_obj.keyframe_insert(data_path="hide_render", frame=frame + 1)

                self.report_queue.put(('INFO', f"Imported '{imported_obj.name}' and set keyframes at frame {frame}."))
        except Exception as e:
            error_msg = f"Failed to import '{obj_path}': {e}"
            self.report_queue.put(('ERROR', error_msg))

        # Increment the import index
        RenderPolyFemAnimationOperator._current_import_index += 1
        RenderPolyFemAnimationOperator._import_in_progress = False

        return 0.1  # Continue the timer

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
            self.report_queue.put(('WARNING', "No 'solution' data found, using original points."))
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
                self.report_queue.put(('WARNING', f"Unsupported cell type '{cell_block.type}' encountered and skipped."))

        self.report_queue.put(('INFO', f"Converted cells to triangles. Total triangles: {len(triangles)}"))
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

    def show_popup(self, message, title, icon):
        """Helper function to display a popup message box"""
        bpy.ops.polyfem.show_message_box('INVOKE_DEFAULT', message=message, title=title, icon=icon)

# ----------------------------
# Open PolyFem Documentation Operator
# ----------------------------
class OpenPolyFemDocsOperator(Operator):
    """Open PolyFem documentation in a browser"""
    bl_idname = "polyfem.open_docs"
    bl_label = "Open PolyFem Documentation"
    bl_description = "Open PolyFem documentation in the default web browser"
    bl_options = {'REGISTER'}

    def execute(self, context):
        webbrowser.open("https://polyfem.github.io/json_defaults_and_spec/?h=json+s")
        self.report({'INFO'}, "Opened PolyFem documentation in your default web browser.")
        return {'FINISHED'}

# ----------------------------
# Clear Cache Operator
# ----------------------------
class ClearCachePolyFemOperator(Operator):
    """Clear the cache directory for PolyFem"""
    bl_idname = "polyfem.clear_cache"
    bl_label = "Clear Cache"
    bl_description = "Clear the cache directory for PolyFem"
    bl_options = {'REGISTER'}

    def execute(self, context):
        polyfem_settings = context.scene.polyfem_settings
        export_path = bpy.path.abspath(polyfem_settings.export_path)
        cache_path = os.path.join(export_path, "obj")
        try:
            if not os.path.exists(cache_path):
                self.report({'WARNING'}, f"Cache directory '{cache_path}' does not exist.")
                return {'CANCELLED'}
            for file in os.listdir(cache_path):
                file_path = os.path.join(cache_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            self.report({'INFO'}, "Cleared the cache directory for PolyFem.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to clear the cache directory: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}