import bpy
import bmesh
import numpy as np
from mathutils import noise, Vector
from bpy.types import Operator

class ApplyHeightmapOperator(Operator):
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

        # Store the original mode to restore later
        original_mode = obj.mode

        try:
            # Ensure we're in edit mode
            if original_mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            # Create BMesh for mesh editing
            bm = bmesh.from_edit_mesh(obj.data)
            bm.faces.ensure_lookup_table()
            selected_faces = [f for f in bm.faces if f.select]

            # Validate face selection
            if not selected_faces:
                self.report({'ERROR'}, "Please select a face before applying the heightmap.")
                return {'CANCELLED'}
            elif len(selected_faces) > 1:
                self.report({'ERROR'}, "Please select only one face. The current selection has too many.")
                return {'CANCELLED'}

            face = selected_faces[0]

            # Ensure the face is a quad
            if len(face.verts) != 4:
                self.report({'ERROR'}, "Selected face is not a quad. Please select a quad face.")
                return {'CANCELLED'}

            # Ensure the face has a valid normal
            if not face.is_valid or face.normal.length == 0:
                self.report({'ERROR'}, "Selected face is not valid or has no normal.")
                return {'CANCELLED'}

            # Check if the face is planar
            if not self.is_face_planar(face):
                self.report({'ERROR'}, "Selected face is not planar. Please select a planar quad face.")
                return {'CANCELLED'}

            # Generate heightmap based on noise function
            noise_func, noise_params = self.get_noise_function(settings)
            if noise_func is None:
                self.report({'ERROR'}, "Invalid noise type.")
                return {'CANCELLED'}

            try:
                heightmap_resolution = max(2, settings.resolution)  # Ensure at least 2 for subdivision

                # Limit the number of cuts per edge to prevent performance issues
                max_cuts_per_edge = 20
                if heightmap_resolution > max_cuts_per_edge:
                    self.report({'WARNING'}, f"Resolution too high. Limiting edge cuts to {max_cuts_per_edge}.")
                    grid_cuts = max_cuts_per_edge
                else:
                    grid_cuts = heightmap_resolution

                # Generate heightmap with (grid_cuts +1) grid points
                size_x, size_y = grid_cuts + 1, grid_cuts + 1

                heightmap = self.generate_heightmap(
                    size_x, size_y,
                    noise_func,
                    amplitude=settings.amplitude,
                    **noise_params
                )
                print(f"Generated heightmap with resolution: {size_x}x{size_y}")
            except Exception as e:
                self.report({'ERROR'}, f"Heightmap generation failed: {e}")
                return {'CANCELLED'}

            # Subdivide face into a grid using subdivide_edges with grid fill
            try:
                # Select all edges of the face for subdivision
                edges_to_subdivide = face.edges[:]
                print(f"Edges to subdivide: {[e.index for e in edges_to_subdivide]}")

                # Perform face subdivision without use_smooth
                result = bmesh.ops.subdivide_edges(
                    bm,
                    edges=edges_to_subdivide,
                    cuts=grid_cuts,
                    use_grid_fill=True
                )
                print(f"Subdivided face into a grid with {grid_cuts} cuts per edge.")
                print(f"Subdivision Result: {result}")

                # Collect new vertices directly from the subdivision result
                new_vertices = [ele for ele in result['geom'] if isinstance(ele, bmesh.types.BMVert)]
                expected_vertex_count = size_x * size_y
                print(f"Number of new vertices from subdivision: {len(new_vertices)} (expected: {expected_vertex_count})")

                # Use get_subdivided_vertices to accurately collect subdivided vertices
                subdivided_verts = self.get_subdivided_vertices(bm, face, grid_cuts)

                print(f"Number of subdivided vertices collected: {len(subdivided_verts)} (expected: {expected_vertex_count})")

                if len(subdivided_verts) != expected_vertex_count:
                    self.report({'ERROR'}, f"Subdivision resulted in {len(subdivided_verts)} vertices, expected {expected_vertex_count}.")
                    return {'CANCELLED'}

            except Exception as e:
                self.report({'ERROR'}, f"Subdivision failed: {e}")
                return {'CANCELLED'}

            # Update mesh after subdivision to ensure all geometry is up-to-date
            bmesh.update_edit_mesh(obj.data, True)

            # Sort the new vertices into grid order
            try:
                sorted_vertices = self.sort_vertices_grid_order(subdivided_verts, size_x, size_y, face)
                print(f"Sorted vertices into grid order with dimensions: {size_x}x{size_y}")
            except Exception as e:
                self.report({'ERROR'}, f"Vertex sorting failed: {e}")
                return {'CANCELLED'}

            # Apply heightmap to sorted vertices
            try:
                self.apply_heightmap_to_vertices(sorted_vertices, heightmap, face.normal)
                print("Applied heightmap to face vertices.")
            except Exception as e:
                self.report({'ERROR'}, f"Applying heightmap failed: {e}")
                return {'CANCELLED'}

            # Final mesh update and viewport refresh
            bmesh.update_edit_mesh(obj.data, True)
            obj.data.update()  # Ensure viewport update in Blender 4.2
            obj.update_tag()

        finally:
            # Restore the original mode
            bpy.ops.object.mode_set(mode=original_mode)

        self.report({'INFO'}, "Heightmap applied successfully.")
        return {'FINISHED'}

    def get_noise_function(self, settings):
        """Retrieve the appropriate noise function and parameters based on settings."""
        if settings.noise_type == 'FBM':
            return self.fbm_noise, {
                'H': settings.H,
                'lacunarity': settings.lacunarity,
                'octaves': settings.octaves
            }
        elif settings.noise_type == 'PERLIN':
            return self.perlin_noise, {}
        elif settings.noise_type == 'SINE':
            return self.sine_wave, {}
        elif settings.noise_type == 'SQUARE':
            return self.square_wave, {}
        elif settings.noise_type == 'GABOR':
            return self.gabor_noise, {
                'orientation': np.radians(settings.orientation),
                'bandwidth': settings.bandwidth,
                'power_spectrum': settings.power_spectrum
            }
        else:
            return None, {}

    def fbm_noise(self, x, y, z=0, H=0.5, lacunarity=2.0, octaves=4):
        """Fractal Brownian Motion Noise"""
        position = Vector((x, y, z))
        value = noise.fractal(position, H=H, lacunarity=lacunarity, octaves=octaves)
        return value

    def perlin_noise(self, x, y, z=0):
        """Perlin Noise"""
        position = Vector((x, y, z))
        return noise.noise(position)

    def sine_wave(self, x, y, z=0):
        """Sine Wave"""
        return np.sin(10.0 * x)

    def square_wave(self, x, y, z=0):
        """Square Wave"""
        return np.sign(np.sin(10.0 * x))

    def gabor_noise(self, x, y, z=0, orientation=0.0, bandwidth=1.0, power_spectrum=1.0):
        """Gabor Noise"""
        position = Vector((x, y, z))
        theta = orientation
        x_rot = position.x * np.cos(theta) + position.y * np.sin(theta)
        y_rot = -position.x * np.sin(theta) + position.y * np.cos(theta)
        gabor_value = np.cos(2 * np.pi * power_spectrum * x_rot) * \
                      np.exp(-0.5 * (y_rot ** 2) / (bandwidth ** 2))
        return gabor_value

    def generate_heightmap(self, size_x, size_y, noise_function, amplitude=1.0, **noise_params):
        """Generate a heightmap using vectorized operations"""
        x_vals = np.linspace(0, 1, size_x)
        y_vals = np.linspace(0, 1, size_y)
        xv, yv = np.meshgrid(x_vals, y_vals, indexing='ij')

        vectorized_noise_func = np.vectorize(noise_function)
        heightmap = vectorized_noise_func(xv, yv)

        heightmap = self.normalize_heightmap(heightmap) * amplitude
        return heightmap

    def normalize_heightmap(self, heightmap):
        """Normalize the heightmap to roughly -1 to 1 range"""
        mean = np.mean(heightmap)
        std_dev = np.std(heightmap)
        if std_dev == 0:
            return heightmap - mean
        return (heightmap - mean) / (3 * std_dev)

    def get_subdivided_vertices(self, bm, original_face, grid_cuts):
        """Identify all vertices lying on the original face's plane and within its bounds"""
        normal = original_face.normal
        center = original_face.calc_center_median()
        tolerance = 1e-2  # Increased tolerance

        # Create local coordinate system
        tangent = (original_face.verts[1].co - original_face.verts[0].co).normalized()
        bitangent = normal.cross(tangent).normalized()

        # Calculate face bounds
        edge1_length = (original_face.verts[1].co - original_face.verts[0].co).dot(tangent)
        edge2_length = (original_face.verts[3].co - original_face.verts[0].co).dot(bitangent)

        # Get the origin point (vertex 0 of original face)
        origin = original_face.verts[0].co

        # Function to get UV coordinates for a vertex
        def get_uv_coords(vert_co):
            vec = vert_co - origin
            u = vec.dot(tangent) / edge1_length if edge1_length != 0 else 0
            v = vec.dot(bitangent) / edge2_length if edge2_length != 0 else 0
            return u, v

        # Create a grid to store vertices
        size = grid_cuts + 1
        vertex_grid = [[None for _ in range(size)] for _ in range(size)]

        # First pass: collect all vertices that lie on the face's plane
        potential_verts = []
        for v in bm.verts:
            if abs(normal.dot(v.co - center)) < tolerance:
                u, v_coord = get_uv_coords(v.co)
                # Add a small epsilon for floating point comparison
                if -0.01 <= u <= 1.01 and -0.01 <= v_coord <= 1.01:
                    potential_verts.append((v, u, v_coord))

        # Debug: Print the number of potential vertices found
        print(f"Potential vertices on face's plane: {len(potential_verts)}")

        # Assign vertices to grid positions
        for vert, u, v in potential_verts:
            # Calculate grid position
            grid_u = int(round(u * grid_cuts))
            grid_v = int(round(v * grid_cuts))

            # Clamp to valid grid positions
            grid_u = max(0, min(grid_u, grid_cuts))
            grid_v = max(0, min(grid_v, grid_cuts))

            # Store vertex in grid
            if vertex_grid[grid_u][grid_v] is None:
                vertex_grid[grid_u][grid_v] = vert

        # Convert grid to list and filter out None values
        subdivided_verts = []
        for i in range(size):
            for j in range(size):
                if vertex_grid[i][j] is not None:
                    subdivided_verts.append(vertex_grid[i][j])

        # Verify we have the expected number of vertices
        expected_verts = (grid_cuts + 1) * (grid_cuts + 1)
        if len(subdivided_verts) != expected_verts:
            print(f"Warning: Found {len(subdivided_verts)} vertices (expected {expected_verts})")

        return subdivided_verts

    def sort_vertices_grid_order(self, verts, size_x, size_y, face):
        """Sort vertices in grid order based on their position relative to the face's local coordinate system"""
        face_center = face.calc_center_median()
        normal = face.normal
        tangent = (face.verts[1].co - face.verts[0].co).normalized()
        bitangent = normal.cross(tangent).normalized()

        projections = []
        for v in verts:
            vec = v.co - face_center
            u = vec.dot(tangent)
            v_ = vec.dot(bitangent)
            projections.append((u, v_))

        # Sort vertices first by v_ (bitangent), then by u (tangent)
        sorted_verts = [v for _, v in sorted(zip(projections, verts), key=lambda pair: (pair[0][1], pair[0][0]))]

        return sorted_verts

    def apply_heightmap_to_vertices(self, verts, heightmap, normal):
        """Apply heightmap displacement to vertices"""
        heightmap_flat = heightmap.flatten()

        if len(verts) != len(heightmap_flat):
            raise Exception("Mismatch between sorted vertices and heightmap size.")

        for i, v in enumerate(verts):
            displacement_value = heightmap_flat[i]
            displacement = normal * displacement_value
            v.co += displacement

    def is_face_planar(self, face, tolerance=1e-5):
        """Check if a face is planar within a given tolerance"""
        normal = face.normal
        center = face.calc_center_median()
        for loop in face.loops:
            vec = loop.vert.co - center
            if abs(normal.dot(vec)) > tolerance:
                return False
        return True