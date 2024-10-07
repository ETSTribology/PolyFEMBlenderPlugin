import bpy
import bmesh
import numpy as np
from mathutils import noise, Vector

class ApplyHeightmapOperator(bpy.types.Operator):
    """Apply Heightmap to Selected Face"""
    bl_idname = "object.apply_heightmap"
    bl_label = "Apply Heightmap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Access the heightmap settings
        settings = context.scene.heightmap_settings

        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object is not a mesh.")
            return {'CANCELLED'}

        # Ensure we're in Edit mode
        bpy.ops.object.mode_set(mode='EDIT')

        # Get BMesh representation
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()

        # Get selected faces
        selected_faces = [f for f in bm.faces if f.select]

        if len(selected_faces) == 0:
            self.report({'ERROR'}, "No face selected.")
            return {'CANCELLED'}
        elif len(selected_faces) > 1:
            self.report({'ERROR'}, "Please select only one face.")
            return {'CANCELLED'}

        face = selected_faces[0]

        # Subdivide the face
        bmesh.ops.subdivide_edges(
            bm,
            edges=face.edges,
            cuts=settings.resolution,
            use_grid_fill=True
        )
        bmesh.update_edit_mesh(obj.data)

        # Get updated mesh and face data
        bm.faces.ensure_lookup_table()
        face = bm.faces[face.index]  # Update face reference after subdivision

        # Generate heightmap
        verts = [v for v in face.verts]
        size_x = size_y = int(np.sqrt(len(verts)))
        if size_x * size_y != len(verts):
            self.report({'ERROR'}, "The face does not have a square number of vertices.")
            return {'CANCELLED'}

        # Choose noise function
        if settings.noise_type == 'FBM':
            noise_func = self.fbm_noise
            noise_params = {
                'octaves': settings.octaves,
                'persistence': settings.persistence,
                'lacunarity': settings.lacunarity
            }
        elif settings.noise_type == 'PERLIN':
            noise_func = self.perlin_noise
            noise_params = {}
        elif settings.noise_type == 'SINE':
            noise_func = self.sine_wave
            noise_params = {}
        elif settings.noise_type == 'SQUARE':
            noise_func = self.square_wave
            noise_params = {}
        else:
            noise_func = self.fbm_noise
            noise_params = {}

        # Generate heightmap
        heightmap = self.generate_heightmap(size_x, size_y, noise_func, amplitude=settings.amplitude, **noise_params)

        # Apply heightmap to the face vertices
        self.apply_heightmap_to_face(verts, heightmap, face.normal)

        # Update the mesh
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

    # Noise functions and helpers
    def fbm_noise(self, x, y, z=0, octaves=4, persistence=0.5, lacunarity=2.0):
        """Fractal Brownian Motion noise using mathutils.noise."""
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        for _ in range(octaves):
            n = noise.noise(Vector((x * frequency, y * frequency, z * frequency)))
            value += amplitude * n
            amplitude *= persistence
            frequency *= lacunarity
        return value

    def perlin_noise(self, x, y, z=0):
        """Simple Perlin noise using mathutils.noise."""
        return noise.noise(Vector((x, y, z)))

    def sine_wave(self, x, y, z=0):
        """Sine wave noise."""
        return np.sin(10.0 * x)

    def square_wave(self, x, y, z=0):
        """Square wave noise."""
        return np.sign(np.sin(10.0 * x))

    def generate_heightmap(self, size_x, size_y, noise_function, amplitude=1.0, **noise_params):
        """Generate a heightmap using the specified noise function."""
        heightmap = np.zeros((size_x, size_y))
        for i in range(size_x):
            for j in range(size_y):
                x = i / size_x
                y = j / size_y
                heightmap[i, j] = noise_function(x, y, **noise_params)
        # Normalize and scale the heightmap
        heightmap = self.normalize_heightmap(heightmap) * amplitude
        return heightmap

    def normalize_heightmap(self, heightmap):
        """Normalize the heightmap to range [0, 1]."""
        # Since mathutils.noise returns values in [-1, 1], adjust accordingly
        return (heightmap + 1) / 2

    def apply_heightmap_to_face(self, verts, heightmap, normal):
        """Apply the heightmap to the face's vertices along the face normal."""
        size_x, size_y = heightmap.shape

        # Sort vertices to match the heightmap grid
        verts_sorted = self.sort_vertices(verts, size_x, size_y)

        # Apply heightmap to vertices
        for idx, v in enumerate(verts_sorted):
            i = idx // size_y
            j = idx % size_y
            displacement = normal * heightmap[i, j]
            v.co += displacement

    def sort_vertices(self, verts, size_x, size_y):
        """Sort vertices based on their local coordinates."""
        # Get local coordinates of vertices
        local_coords = [v.co.copy() for v in verts]

        # Compute the plane of the face
        u_axis = verts[1].co - verts[0].co
        v_axis = verts[size_y].co - verts[0].co

        # Create a local coordinate system
        origin = verts[0].co.copy()
        u_axis.normalize()
        v_axis.normalize()

        # Map vertices to 2D grid
        uv_coords = []
        for co in local_coords:
            vec = co - origin
            u = vec.dot(u_axis)
            v = vec.dot(v_axis)
            uv_coords.append((u, v))

        # Sort vertices based on uv_coords
        verts_uv = list(zip(verts, uv_coords))
        verts_uv.sort(key=lambda item: (item[1][1], item[1][0]))  # Sort by v then u

        sorted_verts = [item[0] for item in verts_uv]
        return sorted_verts
