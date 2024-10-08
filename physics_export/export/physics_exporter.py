import bpy
import json
import os
import subprocess
import shutil
import math
import bmesh
from mathutils import Vector

class ExportPhysics(bpy.types.Operator):
    """Extract Objects and Physics Constraints"""
    bl_idname = "physics_export.export_physics"
    bl_label = "Export Physics Constraints to JSON"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.scene.export_physics_settings

        # Ensure export_directory and json_filename are set
        if not settings.export_directory:
            self.report({'ERROR'}, "Please specify an export directory in the addon settings.")
            return {'CANCELLED'}

        if not settings.json_filename:
            self.report({'ERROR'}, "Please specify a JSON filename in the addon settings.")
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(settings.export_directory)
        json_filepath = os.path.join(output_dir, settings.json_filename)

        data = {
            "geometry": [],
            "contact": {
                "friction_coefficient": 0.5
            }
        }

        # Determine which objects to export
        if settings.export_selected_only:
            objects_to_export = context.selected_objects
        else:
            objects_to_export = context.scene.objects

        # Check if any objects are selected
        if not objects_to_export:
            self.report({'WARNING'}, "No objects selected for export.")
            return {'CANCELLED'}

        # Process each object
        object_id_map = {}
        current_id = 1

        for obj in objects_to_export:
            if obj.type != 'MESH':
                continue  # Skip non-mesh objects

            obj_data = self.process_object(obj, current_id, output_dir, settings, context)
            if obj_data is None:
                return {'CANCELLED'}

            data["geometry"].append(obj_data)
            object_id_map[obj.name] = current_id
            current_id += 1

        # Write JSON file
        if not self.write_json(data, json_filepath):
            self.report({'ERROR'}, f"Failed to write JSON file to {json_filepath}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Data exported to {json_filepath}")
        return {'FINISHED'}

    def process_object(self, obj, obj_id, output_dir, settings, context):
        """Process an individual object and collect its data."""
        obj_data = {}
        obj_data["volume_selection"] = obj_id

        # Export mesh
        if settings.export_stl:
            mesh_filename = f"{obj.name}.{settings.export_format.lower()}"
            mesh_filepath = os.path.join(output_dir, mesh_filename)
            success = self.export_mesh(obj, mesh_filepath, settings)
            if not success:
                self.report({'ERROR'}, f"Failed to export mesh for object {obj.name}")
                return None
            obj_data["mesh"] = mesh_filename
        else:
            obj_data["mesh"] = f"{obj.name}.{settings.export_format.lower()}"

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

    def get_point_selection(self, obj, context):
        """Retrieve the bounding boxes of selected vertices and format them for JSON."""

        point_selection_data = []

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
    

    def export_mesh_to_stl(obj, filepath):
        """Exports the mesh data of an object to an STL file."""
        with open(filepath, 'w') as stl_file:
            stl_file.write('solid {}\n'.format(obj.name))
            mesh = obj.to_mesh()
            mesh.calc_loop_triangles()

            for tri in mesh.loop_triangles:
                vertices = [mesh.vertices[i].co for i in tri.vertices]
                # Calculate normal
                normal = tri.normal
                stl_file.write('facet normal {} {} {}\n'.format(normal.x, normal.y, normal.z))
                stl_file.write('    outer loop\n')
                for vert in vertices:
                    stl_file.write('        vertex {} {} {}\n'.format(vert.x, vert.y, vert.z))
                stl_file.write('    endloop\n')
                stl_file.write('endfacet\n')

            stl_file.write('endsolid {}\n'.format(obj.name))
            obj.to_mesh_clear()
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
            elif export_format == 'PLY':
                self.report({'ERROR'}, "PLY export is not supported without the PLY addon.")
                return False
            elif export_format == 'MSH':
                # Export to OFF format for TetWild
                temp_off_filepath = os.path.join(os.path.dirname(mesh_filepath), f"{obj.name}_temp.stl")
                success = self.export_mesh_to_stl(obj, temp_off_filepath)
                if not success:
                    self.report({'ERROR'}, f"Failed to export {obj.name} to OFF format for TetWild.")
                    return False
                # Run TetWild
                success = run_tetwild(temp_off_filepath, mesh_filepath)
                if not success:
                    return False
            else:
                self.report({'ERROR'}, f"Unsupported export format without addons: {export_format}")
                return False
        except Exception as e:
            self.report({'ERROR'}, f"Error exporting {obj.name}: {e}")
            return False

        return True

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

    def write_json(self, data, json_filepath):
        """Write the collected data to a JSON file."""
        try:
            with open(json_filepath, 'w') as outfile:
                json.dump(data, outfile, indent=4)
            return True
        except Exception as e:
            print(f"Failed to write JSON file: {e}")
            return False
        

    def export_camera(self, scene):
        """Export the camera data."""
        cam_ob = scene.camera
        if cam_ob is None or cam_ob.type != 'CAMERA':
            print("ERROR: No camera found in the scene.")
            return {}, {}

        print(f"INFO: Exporting camera: {cam_ob.name}")

        # Camera transformation
        from_point = cam_ob.matrix_world.translation
        at_point = from_point - cam_ob.matrix_world.col[2].to_3d()
        up_vector = cam_ob.matrix_world.col[1].to_3d()

        # Field of view
        fov = cam_ob.data.angle * 180 / math.pi
        aspect_ratio = scene.render.resolution_x / scene.render.resolution_y

        camera_data = {
            "resolution": [
                scene.render.resolution_x,
                scene.render.resolution_y
            ],
            "vfov": fov,
            "aspect_ratio": aspect_ratio,
            "transform": {
                "from": [from_point.x, from_point.y, from_point.z],
                "at": [at_point.x, at_point.y, at_point.z],
                "up": [up_vector.x, up_vector.y, up_vector.z]
            }
        }

        # Sampler settings
        sampler_data = {
            "type": "independent",
            "samples": scene.render.resolution_percentage  # Example usage
        }

        return camera_data, sampler_data
    

    def export_materials(self, obj, filepath, exported_materials):
        """Export materials used by the object."""
        materials_data = []
        for mat_slot in obj.material_slots:
            material = mat_slot.material
            if material and material.name not in exported_materials:
                mat_data = self.export_material(material, filepath)
                materials_data.append(mat_data)
                exported_materials.add(material.name)
        return materials_data

    def export_material(self, material, filepath):
        """Export a single material."""
        print(f"INFO: Exporting material: {material.name}")
        mat_data = {
            "name": material.name,
            "type": "diffuse",
            "albedo": [0.8, 0.8, 0.8]  # Default albedo
        }
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == 'BSDF_DIFFUSE':
                    color = node.inputs['Color'].default_value
                    mat_data["albedo"] = [color[0], color[1], color[2]]
        return mat_data

def run_tetwild(input_file, output_file, ideal_edge_length=0.05, epsilon=1e-3, filter_energy=10, max_pass=80):
    """Run TetWild via Docker to generate an MSH file from a mesh."""
    # Build the command string with the required parameters
    command = [
        "docker", "run", "--rm",
        "-v", f"{os.path.abspath(os.path.dirname(input_file))}:/data",  # Mount the directory containing the input file
        "yixinhu/tetwild",  # Docker image
        "--input", f"{os.path.basename(input_file)}",  # Input file path in container
        "--ideal-edge-length", str(ideal_edge_length),
        "--epsilon", str(epsilon),
        "--filter-energy", str(filter_energy),
        "--max-pass", str(max_pass),
        "--output", f"{os.path.basename(output_file)}"  # Output file
    ]

    # Execute the command
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"TetWild ran successfully with input: {input_file}")
        print(result.stdout)
        return True
    except FileNotFoundError:
        print("Docker not found. Please ensure Docker is installed and in your system's PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error running TetWild: {e}")
        print(f"Standard Output: {e.stdout}")
        print(f"Standard Error: {e.stderr}")
        print(e.stderr)
        return False