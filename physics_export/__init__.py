bl_info = {
    "name": "BlenderPluginSimulation",
    "author": "Antoine Boucher",
    "version": (1, 5),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Physics",
    "description": "Extracts objects and their physics constraints and exports to JSON",
    "category": "Object",
    "wiki_url": "https://github.com/ETSTribology/BlenderPluginSimulation",
}

import bpy
from .export.physics_exporter import ExportPhysics
from .panels.physics_panel import ExtractPhysicsPanel
from .properties.export_properties import ExportPhysicsSettings
from .properties.heightmap_properties import HeightmapSettings
from .operators.heightmap_operator import ApplyHeightmapOperator
from .panels.heightmap_panel import HeightmapPanel

classes = [
    # Properties
    ExportPhysicsSettings,
    HeightmapSettings,

    # Exporter
    ExportPhysics,

    # Operators
    ApplyHeightmapOperator,

    # Panels
    ExtractPhysicsPanel,
    HeightmapPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.export_physics_settings = bpy.props.PointerProperty(type=ExportPhysicsSettings)
    print("BlenderPluginSimulation registered successfully.")

def unregister():
    del bpy.types.Scene.export_physics_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("BlenderPluginSimulation unregistered successfully.")
