import bpy
from bpy.props import StringProperty

class PolyFemSettings(bpy.types.PropertyGroup):
    """Settings for PolyFem executable, JSON input, and project path"""
    polyfem_executable_path: StringProperty(
        name="PolyFem Executable Path",
        description="Path to the PolyFem executable",
        default="",
        subtype='FILE_PATH'
    )

    polyfem_json_input: StringProperty(
        name="PolyFem JSON Input",
        description="JSON input for PolyFem simulation",
        default='{}',  # Default empty JSON
        options={'TEXTEDIT_UPDATE'},  # Allows large text input
    )

    project_path: StringProperty(
        name="Project Path",
        description="Directory to save meshes and JSON files",
        default="",
        subtype='DIR_PATH'  # Allows users to select a directory
    )
