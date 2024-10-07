bl_info = {
    "name": "Extract Objects and Physics Constraints",
    "author": "Your Name",
    "version": (1, 4),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Physics",
    "description": "Extracts objects and their physics constraints and exports to JSON",
    "category": "Object",
}

import importlib
import importlib.util
import os
import sys
import typing

import bpy
import json
import os
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

if bpy.app.version < (2, 91, 0):
    PYTHON_BINARY = bpy.app.binary_path_python
else:
    PYTHON_BINARY = sys.executable

BLENDER_EXECUTABLE = bpy.app.binary_path

STATUS_DLL_NOT_FOUND = 3221225781
""" The WindowsApps' rights restriction affects DLLs discovery in PATH """

def pip_fallback(modules_to_install, directory):
    """ A fallback to install using a Blender's executable. """

    from pip._internal import main
    return main(['install', '--upgrade', *modules_to_install, "--target", directory, '--verbose'])


def ensurepip_fallback():
    """ A fallback to install using a Blender's executable. """

    import ensurepip
    ensurepip.bootstrap(verbosity=1)


def get_python_expr(func, *args, **kwargs):
    """ Does not work with `shell=True`. """

    import inspect
    import json
    import textwrap

    expr = [textwrap.dedent(inspect.getsource(func))]

    args_json = repr(json.dumps(args))
    kwargs_json = repr(json.dumps(kwargs))

    if args and kwargs:
        expr.append('import json')
        expr.append(f'args = json.loads({args_json})')
        expr.append(f'kwargs = json.loads({kwargs_json})')
        expr.append(f'{func.__name__}(*args, **kwargs)')
    elif args:
        expr.append('import json')
        expr.append(f'args = json.loads({args_json})')
        expr.append(f'{func.__name__}(*args)')
    elif kwargs:
        expr.append('import json')
        expr.append(f'kwargs = json.loads({kwargs_json})')
        expr.append(f'{func.__name__}(**kwargs)')
    else:
        expr.append(f'{func.__name__}()')

    return '\n'.join(expr)


def get_terminal_width(fallback = 80):

    try:
        value = int(os.environ['COLUMNS'])
    except Exception:
        try:
            value = os.get_terminal_size(sys.__stdout__.fileno()).columns
        except Exception:
            value = fallback

    return value


def print_separator(*values: object, sep: str = ' '):

    width = get_terminal_width() - 1

    text = sep.join((str(value) for value in values))

    if text:
        text = ' ' + text + ' '

    text_len = len(text)
    rest_of_width = width - text_len
    half_rest_of_width = int(rest_of_width / 2)

    print('=' * half_rest_of_width, text, '=' * (width - (half_rest_of_width + text_len)), sep='', flush=True)


def get_os_environ():

    env = os.environ.copy()

    PATH = env['PATH']
    paths = PATH.split(os.pathsep)

    def add_to_PATH(path):

        if not os.path.exists(path):
            return

        path = os.path.realpath(path)
        if path in paths:
            return

        paths.insert(0, path)

    blender_dir = os.path.dirname(BLENDER_EXECUTABLE)
    # vcruntime140.dll
    blender_crt = os.path.join(blender_dir, 'blender.crt')

    add_to_PATH(blender_crt)
    add_to_PATH(blender_dir)

    env['PATH'] = os.pathsep.join(paths)

    return env


def get_site_packages_directory(root_dir: str = None):
    """ If `root_dir` is `None` then `ROOT_DIR` is used. """

    if root_dir is None:
        root_dir = ROOT_DIR

    version = sys.version_info
    return os.path.join(root_dir, '_deps', f"v{version[0]}{version[1]}")


def get_missing_site_packages(packages: typing.List[typing.Tuple[str, str]], directory = get_site_packages_directory()):
    """ Returns a list of missing packages in `packages`. """

    directory = os.path.abspath(directory)
    if not directory in sys.path and os.path.exists(directory):
        sys.path.append(directory)

    return [package for package in packages if not importlib.util.find_spec(package[0])]


def ensure_site_packages(packages: typing.List[typing.Tuple[str, str]], directory = get_site_packages_directory(), forced = False):
    """
    `packages`: list of tuples (<import name>, <pip name>)
    `directory`: a folder for site packages, will be created if does not exist and added to `sys.path`
    `forced`: ignore installed
    """

    if not packages:
        return


    directory = os.path.abspath(directory)
    os.makedirs(directory, exist_ok = True)
    if not directory in sys.path:
        sys.path.append(directory)


    if forced:
        modules_to_install = [module[1] for module in packages]
    else:
        modules_to_install = [module[1] for module in packages if not importlib.util.find_spec(module[0])]

    if not modules_to_install:
        return


    print_separator('START ensure_site_packages')

    import subprocess
    import traceback

    env = get_os_environ()
    env['PYTHONPATH'] = directory + os.pathsep + env.get('PYTHONPATH', '')
    env['PYTHONPATH'].strip(os.pathsep)

    if not importlib.util.find_spec('pip'):
        print_separator('ensurepip')
        try:
            subprocess.run([PYTHON_BINARY, '-m', 'ensurepip', '--verbose'], check=True, env=env)

        except subprocess.CalledProcessError as e:

            if e.returncode == STATUS_DLL_NOT_FOUND:
                subprocess.run([BLENDER_EXECUTABLE, '--factory-startup', '-b', '--python-expr', get_python_expr(ensurepip_fallback)], check=True, env=env)
            else:
                traceback.print_exc()

        except Exception:
            traceback.print_exc()

    print_separator('upgrade pip')
    try:
        subprocess.run([PYTHON_BINARY, '-m', 'pip', 'install', '--upgrade', 'pip', "--target", directory, '--verbose'], check=True, env=env)

    except subprocess.CalledProcessError as e:

        if e.returncode == STATUS_DLL_NOT_FOUND:
            subprocess.run([BLENDER_EXECUTABLE, '--factory-startup', '-b', '--python-expr', get_python_expr(pip_fallback, ['pip'], directory)], check=True, env=env)
        else:
            traceback.print_exc()

    except Exception:
        traceback.print_exc()


    print_separator('install dependencies')
    try:
        subprocess.run([PYTHON_BINARY, '-s', '-m', 'pip', 'install', '--upgrade', *modules_to_install, "--target", directory, '--verbose'], check=True, env=env)

    except subprocess.CalledProcessError as e:
        if e.returncode != STATUS_DLL_NOT_FOUND:
            raise e

        subprocess.run([BLENDER_EXECUTABLE, '--factory-startup', '-b', '--python-expr', get_python_expr(pip_fallback, modules_to_install, directory)], check=True, env=env)


    importlib.invalidate_caches()

    missing_packages = [package for package in packages if not importlib.util.find_spec(package[0])]
    if missing_packages:
        raise Exception(f'Fail to install dependencies: {missing_packages}')

    print_separator('END ensure_site_packages')

class OBJECT_OT_extract_physics_constraints(bpy.types.Operator, ExportHelper):
    """Extract Objects and Physics Constraints"""
    bl_idname = "object.extract_physics_constraints"
    bl_label = "Export Physics Constraints to JSON"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    export_stl: BoolProperty(
        name="Export STL Files",
        description="Export each object as an STL file",
        default=True
    )

    def execute(self, context):
        output_dir = os.path.dirname(self.filepath)
        data = {
            "geometry": [],
            "contact": {
                "friction_coefficient": 0.5
            }
        }

        # Create a mapping from objects to IDs
        object_id_map = {}
        current_id = 1

        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue  # Skip non-mesh objects

            obj_data = {}
            obj_id = obj.pass_index if obj.pass_index != 0 else current_id
            object_id_map[obj.name] = obj_id
            current_id += 1  # Increment ID for next object if pass_index is not used

            # Export object as STL
            if self.export_stl:
                stl_filename = f"{obj.name}.stl"
                stl_filepath = os.path.join(output_dir, stl_filename)
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.export_mesh.stl(
                    filepath=stl_filepath,
                    use_selection=True,
                    global_scale=1.0,
                    use_scene_unit=False,
                    use_mesh_modifiers=True,
                )
                obj_data["mesh"] = stl_filename
            else:
                obj_data["mesh"] = f"{obj.name}.stl"  # Assuming the STL files exist

            # Add transformation
            obj_data["transformation"] = {
                "translation": list(obj.location)
            }

            # Assign volume_selection or id
            obj_data["volume_selection"] = obj_id

            # Determine if object is an obstacle
            if obj.rigid_body and obj.rigid_body.type == 'PASSIVE':
                obj_data["is_obstacle"] = True

            # Extract physics properties
            physics_properties = {}

            # Soft Body properties
            if 'SOFT_BODY' in [mod.type for mod in obj.modifiers]:
                sb_settings = obj.modifiers['Softbody'].settings
                physics_properties['bending_stiffness'] = sb_settings.bending
                physics_properties['self_collision'] = sb_settings.use_self_collision

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

            if physics_properties:
                obj_data["physics_properties"] = physics_properties

            data["geometry"].append(obj_data)

        # Write JSON file
        try:
            with open(self.filepath, 'w') as outfile:
                json.dump(data, outfile, indent=4)
            self.report({'INFO'}, f"Data exported to {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to write file: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class VIEW3D_PT_extract_physics_panel(bpy.types.Panel):
    """Panel for Extracting Physics Constraints"""
    bl_label = "Extract Physics Constraints"
    bl_idname = "VIEW3D_PT_extract_physics_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Physics'

    def draw(self, context):
        layout = self.layout
        layout.operator(OBJECT_OT_extract_physics_constraints.bl_idname, text="Export to JSON")

def register():
    bpy.utils.register_class(OBJECT_OT_extract_physics_constraints)
    bpy.utils.register_class(VIEW3D_PT_extract_physics_panel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_extract_physics_constraints)
    bpy.utils.unregister_class(VIEW3D_PT_extract_physics_panel)

if __name__ == "__main__":
    register()
