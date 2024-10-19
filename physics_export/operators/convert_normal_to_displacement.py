import bpy
import os
import numpy as np
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy.types import Operator
from mathutils import Vector

class ConvertNormalToDisplacementOperator(Operator):
    """Convert a Normal Map to a Displacement Map with optional bias, contrast, and inversion"""
    bl_idname = "object.convert_normal_to_displacement"
    bl_label = "Convert Normal to Displacement"
    bl_description = "Convert a selected normal map to a displacement map and save it with optional bias, contrast, and inversion"
    bl_options = {'REGISTER', 'UNDO'}

    # Internal properties for modal operation
    _timer = None
    _current_row = 0
    _total_rows = 0
    _chunk_size = 100  # Number of rows to process per timer event
    _displacement_mapped = None
    _disp_pixels_flat = None
    _disp_image = None
    _disp_map_path = ""
    _width = 0
    _height = 0
    _normal_image = None  # Store normal_image as an instance variable

    def execute(self, context):
        settings = context.scene.heightmap_settings
        project_path = bpy.path.abspath(settings.project_path)
        normal_map_path = bpy.path.abspath(settings.normal_map)

        # Validate Normal Map path
        if not os.path.isfile(normal_map_path):
            self.report({'ERROR'}, "Normal map file not found. Please provide a valid path.")
            return {'CANCELLED'}

        # Ensure Project Path exists
        if not os.path.exists(project_path):
            try:
                os.makedirs(project_path)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to create project directory: {e}")
                return {'CANCELLED'}

        try:
            # Load the normal map image
            self._normal_image = bpy.data.images.load(normal_map_path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load normal map: {e}")
            return {'CANCELLED'}

        # Validate image channels
        if self._normal_image.channels < 3:
            self.report({'ERROR'}, "Normal map image must have at least 3 channels (RGB).")
            self._normal_image.user_clear()
            bpy.data.images.remove(self._normal_image)
            return {'CANCELLED'}

        # Prepare image data as NumPy array
        pixels = np.array(self._normal_image.pixels[:])
        width, height = self._normal_image.size

        # Reshape to (height, width, channels)
        channels = self._normal_image.channels
        try:
            pixels = pixels.reshape((height, width, channels))
        except ValueError as e:
            self.report({'ERROR'}, f"Image reshape failed: {e}")
            self._normal_image.user_clear()
            bpy.data.images.remove(self._normal_image)
            return {'CANCELLED'}

        # Extract the blue channel (assuming Z is the displacement)
        blue_channel = pixels[:, :, 2]

        # Normalize from [0, 1] to [-1, 1]
        displacement = (blue_channel * 2.0) - 1.0

        # Apply contrast adjustment
        displacement = self.adjust_contrast(displacement, settings.contrast)

        # Optionally invert the displacement map
        if settings.invert_displacement:
            displacement = 1.0 - displacement

        # Calculate the displacement bias using the four corner pixels
        displacement_bias = self.calculate_displacement_bias(displacement, width, height)

        # Adjust displacement map with bias
        displacement -= displacement_bias

        # Map displacement from [-1, 1] to [0, 1] for image representation
        displacement_mapped = (displacement * 0.5) + 0.5

        # Initialize displacement pixels array with zeros and set alpha channel to 1
        disp_pixels = np.zeros((height, width, 4), dtype=np.float32)
        disp_pixels[:, :, 0] = displacement_mapped  # Red channel
        disp_pixels[:, :, 3] = 1.0  # Alpha channel

        # Flatten the pixel data
        disp_pixels_flat = disp_pixels.flatten()

        # Create a new image for displacement map
        disp_image_name = os.path.splitext(os.path.basename(normal_map_path))[0] + "_displacement"
        disp_image = bpy.data.images.new(name=disp_image_name, width=width, height=height)
        disp_image.pixels = disp_pixels_flat.tolist()

        # Prepare to save the displacement map
        disp_map_path = os.path.join(project_path, disp_image_name + ".png")

        # Assign to internal properties for modal access
        self._disp_image = disp_image
        self._disp_map_path = disp_map_path
        self._width = width
        self._height = height
        self._total_rows = height
        self._current_row = 0

        # Start modal operation with a timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        # Initialize progress bar
        wm.progress_begin(0, 100)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        wm = context.window_manager

        if event.type == 'TIMER':
            # Determine the range of rows to process in this chunk
            start_row = self._current_row
            end_row = min(self._current_row + self._chunk_size, self._total_rows)

            # Process the current chunk
            try:
                # Update progress bar
                progress = (end_row / self._total_rows) * 100
                wm.progress_update(progress)

                # Update current row
                self._current_row = end_row

                # If all rows have been processed, save the image
                if self._current_row >= self._total_rows:
                    try:
                        self._disp_image.filepath_raw = self._disp_map_path
                        self._disp_image.file_format = 'PNG'
                        self._disp_image.save()
                        self.report({'INFO'}, f"Displacement map saved to {self._disp_map_path}")
                    except Exception as e:
                        self.report({'ERROR'}, f"Failed to save displacement map: {e}")
                        wm.progress_end()
                        self._disp_image.user_clear()
                        bpy.data.images.remove(self._disp_image)
                        self._normal_image.user_clear()
                        bpy.data.images.remove(self._normal_image)
                        wm.event_timer_remove(self._timer)
                        return {'CANCELLED'}

                    # Clean up
                    self._normal_image.user_clear()
                    bpy.data.images.remove(self._normal_image)
                    self._disp_image.user_clear()
                    bpy.data.images.remove(self._disp_image)
                    wm.progress_end()
                    wm.event_timer_remove(self._timer)
                    return {'FINISHED'}

            except Exception as e:
                self.report({'ERROR'}, f"An unexpected error occurred during processing: {e}")
                wm.progress_end()
                wm.event_timer_remove(self._timer)
                return {'CANCELLED'}

        elif event.type in {'ESC'}:
            # Handle cancel operation
            wm.progress_end()
            wm.event_timer_remove(self._timer)
            self.report({'INFO'}, "Operation cancelled by user.")
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        wm = context.window_manager
        wm.progress_end()
        wm.event_timer_remove(self._timer)
        self.report({'INFO'}, "Operation cancelled.")

    def calculate_displacement_bias(self, displacement, width, height):
        """Calculate displacement bias based on the average of the four corners."""
        top_left = displacement[0, 0]
        top_right = displacement[0, width - 1]
        bottom_left = displacement[height - 1, 0]
        bottom_right = displacement[height - 1, width - 1]
        displacement_bias = (top_left + top_right + bottom_left + bottom_right) / 4.0
        return displacement_bias

    def adjust_contrast(self, displacement, contrast):
        """Apply contrast adjustment to the displacement map."""
        factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
        displacement = factor * (displacement - 0.5) + 0.5
        return np.clip(displacement, -1, 1)  # Keep within [-1, 1] range