import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty

class ExportPhysicsSettings(bpy.types.PropertyGroup):
    export_constraints: BoolProperty(
        name="Export Constraints",
        description="Whether to export physics constraints",
        default=True
    )
    export_path: StringProperty(
        name="Export Path",
        description="Path to export the JSON file",
        default="//physics_export.json",
        subtype='FILE_PATH'
    )
    json_filename: StringProperty(
        name="JSON Filename",
        description="Name of the JSON file to export",
        default="export.json",
        subtype='NONE'
    )
    export_stl: BoolProperty(
        name="Export Mesh Files",
        description="Export each object as a mesh file",
        default=True
    )
    export_format: EnumProperty(
        name="Export Format",
        description="Choose the mesh export format",
        items=[
            ('STL', "STL (.stl)", "Export as STL"),
            ('OBJ', "OBJ (.obj)", "Export as OBJ"),
            ('FBX', "FBX (.fbx)", "Export as FBX"),
            ('GLTF', "GLTF (.gltf)", "Export as GLTF"),
            ('MSH', "MSH (.msh)", "Export as MSH using TetWild"),
        ],
        default='STL',
    )
    export_selected_only: BoolProperty(
        name="Export Selected Only",
        description="Export only selected objects",
        default=False
    )
    export_point_selection: BoolProperty(
        name="Export Point Selections",
        description="Whether to export selected vertices as point selections",
        default=False
    )
