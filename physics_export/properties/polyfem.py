import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty

class PolyFemSettings(bpy.types.PropertyGroup):
    """Settings for PolyFem executable and project paths"""

    # Path to PolyFem executable
    polyfem_executable_path: StringProperty(
        name="PolyFem Executable Path",
        description="Path to the PolyFem executable",
        default="",
        subtype='FILE_PATH'
    )

    # JSON configuration file for PolyFem simulation
    polyfem_json_input: StringProperty(
        name="PolyFem JSON File",
        description="Path to the JSON file for PolyFem simulation",
        default="",
        subtype='FILE_PATH'
    )

    # Directory for project (VTU and OBJ files will be inside this directory)
    project_path: StringProperty(
        name="Project Path",
        description="Directory for saving VTU and OBJ files",
        default="",
        subtype='DIR_PATH'
    )

    # Rendering settings
    start_frame: IntProperty(
        name="Start Frame",
        description="Frame to start the animation",
        default=0,
        min=0
    )