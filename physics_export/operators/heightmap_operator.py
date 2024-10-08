import bpy
import bmesh
import numpy as np
from mathutils import noise, Vector
from mathutils.kdtree import KDTree
from ..properties.heightmap_properties import HeightmapSettings

class ApplyHeightmapOperator(bpy.types.Operator):
    """Apply a heightmap to the selected face using specified noise settings"""
    bl_idname = "object.apply_heightmap"
    bl_label = "Apply Heightmap"
    bl_description = "Apply a heightmap to the selected face using specified noise settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.heightmap_settings
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object is not a mesh.")
            return {'CANCELLED'}

        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        selected_faces = [f for f in bm.faces if f.select]

        if not selected_faces:
            self.report({'ERROR'}, "Please select a face before applying the heightmap.")
            return {'CANCELLED'}
        elif len(selected_faces) > 1:
            self.report({'ERROR'}, "Please select only one face. The current selection has too many.")
            return {'CANCELLED'}

        face = selected_faces[0]

        # Generate a temporary heightmap to determine variability
        noise_func, noise_params = self.get_noise_function(settings)

        if noise_func is None:
            self.report({'ERROR'}, "Invalid noise type.")
            return {'CANCELLED'}

        try:
            heightmap_resolution = max(10, int(20 * settings.amplitude))  # Adjust resolution based on amplitude
            size_x, size_y = heightmap_resolution, heightmap_resolution

            heightmap = self.generate_heightmap(
                size_x, size_y,
                noise_func,
                amplitude=settings.amplitude,
                **noise_params
            )
        except Exception as e:
            self.report({'ERROR'}, f"Heightmap generation failed: {e}")
            return {'CANCELLED'}

        # Calculate adaptive subdivision based on heightmap variability
        variability = self.calculate_heightmap_variability(heightmap)
        subdivisions = self.determine_subdivisions(variability)

        # Subdivide the face adaptively
        try:
            bmesh.ops.subdivide_edges(
                bm,
                edges=face.edges,
                cuts=subdivisions,
                use_grid_fill=True
            )
        except Exception as e:
            self.report({'ERROR'}, f"Subdivision failed: {e}")
            return {'CANCELLED'}

        bmesh.update_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        face = bm.faces[face.index]

        verts = [v for v in face.verts]
        size_x, size_y = self.calculate_grid_size(len(verts))

        if size_x * size_y != len(verts):
            self.report({'ERROR'}, "Unable to determine grid size from subdivided face.")
            return {'CANCELLED'}

        try:
            heightmap = self.generate_heightmap(
                size_x, size_y,
                noise_func,
                amplitude=settings.amplitude,
                **noise_params
            )
        except Exception as e:
            self.report({'ERROR'}, f"Heightmap generation failed: {e}")
            return {'CANCELLED'}

        try:
            self.apply_heightmap_to_face(verts, heightmap, face.normal)
        except Exception as e:
            self.report({'ERROR'}, f"Applying heightmap failed: {e}")
            return {'CANCELLED'}

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'INFO'}, "Heightmap applied successfully.")
        return {'FINISHED'}

    def get_noise_function(self, settings):
        """Retrieve the appropriate noise function and parameters based on settings."""
        if settings.noise_type == 'FBM':
            return self.fbm_noise, {
                'octaves': settings.octaves,
                'persistence': settings.persistence,
                'lacunarity': settings.lacunarity
            }
        elif settings.noise_type == 'PERLIN':
            return self.perlin_noise, {}
        elif settings.noise_type == 'SINE':
            return self.sine_wave, {}
        elif settings.noise_type == 'SQUARE':
            return self.square_wave, {}
        elif settings.noise_type == 'GABOR':
            return self.gabor_noise, {
                'orientation': settings.orientation,
                'bandwidth': settings.bandwidth,
                'power_spectrum': settings.power_spectrum
            }
        else:
            return None, {}

    def fbm_noise(self, x, y, z=0, octaves=4, persistence=0.5, lacunarity=2.0):
        position = Vector((x, y, z))
        value = noise.fractal(position, H=persistence, lacunarity=lacunarity, octaves=octaves)
        return value

    def perlin_noise(self, x, y, z=0):
        return noise.noise(Vector((x, y, z)))

    def sine_wave(self, x, y, z=0):
        return np.sin(10.0 * x)

    def square_wave(self, x, y, z=0):
        return np.sign(np.sin(10.0 * x))

    def gabor_noise(self, x, y, z=0, orientation=0, bandwidth=1.0, power_spectrum=1.0):
        position = Vector((x, y, z))
        gabor_value = np.cos(2 * np.pi * power_spectrum * position.x * np.cos(orientation) +
                             position.y * np.sin(orientation)) * \
                      np.exp(-0.5 * (position.length_squared / bandwidth ** 2))
        return gabor_value

    def generate_heightmap(self, size_x, size_y, noise_function, amplitude=1.0, **noise_params):
        x_vals = np.linspace(0, 1, size_x)
        y_vals = np.linspace(0, 1, size_y)
        xv, yv = np.meshgrid(x_vals, y_vals, indexing='ij')

        vectorized_noise = np.vectorize(lambda x, y: noise_function(x, y, **noise_params))
        heightmap = vectorized_noise(xv, yv)

        heightmap = self.normalize_heightmap(heightmap) * amplitude
        return heightmap

    def normalize_heightmap(self, heightmap):
        mean = np.mean(heightmap)
        std_dev = np.std(heightmap)
        return (heightmap - mean) / (3 * std_dev)  # Normalize to -1 to 1 range

    def calculate_heightmap_variability(self, heightmap):
        """Calculate variability of the heightmap by looking at standard deviation."""
        return np.std(heightmap)

    def determine_subdivisions(self, variability, base_subdivisions=1):
        """Determine the number of subdivisions based on variability."""
        scale_factor = 8 if 'GABOR' in settings.noise_type else 5
        return base_subdivisions + int(scale_factor * variability)

    def apply_heightmap_to_face(self, verts, heightmap, normal):
        size_x, size_y = heightmap.shape
        verts_sorted = self.sort_vertices(verts, size_x, size_y)

        for idx, v in enumerate(verts_sorted):
            i = idx // size_y
            j = idx % size_y
            displacement = normal * heightmap[i, j]
            v.co += displacement

    def sort_vertices(self, verts, size_x, size_y):
        kdtree = KDTree(len(verts))
        for i, v in enumerate(verts):
            kdtree.insert(v.co, i)
        kdtree.balance()

        sorted_verts = []
        for y in np.linspace(0, 1, size_y):
            for x in np.linspace(0, 1, size_x):
                location = self.interpolate_uv_position(x, y, verts)
                _, index, _ = kdtree.find(location)
                sorted_verts.append(verts[index])
        return sorted_verts

    def calculate_grid_size(self, num_verts):
        possible_sizes = [(i, num_verts // i) for i in range(2, num_verts) if num_verts % i == 0]
        if not possible_sizes:
            return 1, num_verts  # Fallback to 1xN grid
        size_x, size_y = min(possible_sizes, key=lambda x: abs(x[0] - x[1]))
        return size_x, size_y
