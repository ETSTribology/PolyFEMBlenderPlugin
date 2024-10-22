import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty

class PolyFemSettings(bpy.types.PropertyGroup):
    """Settings for PolyFem executable and project paths"""
    # JSON configuration file for PolyFem simulation
    polyfem_json_input: StringProperty(
        name="PolyFem JSON File",
        description="Path to the JSON file for PolyFem simulation",
        default="",
        subtype='FILE_PATH'
    ) # type: ignore # noqa: F821

    # Directory for project (VTU and OBJ files will be inside this directory)
    project_path: StringProperty(
        name="Project Path",
        description="Directory for saving VTU and OBJ files",
        default="",
        subtype='DIR_PATH'
    ) # type: ignore # noqa: F821