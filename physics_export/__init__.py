bl_info = {
    "name": "BlenderPluginSimulation",
    "author": "Antoine Boucher",
    "version": (1, 4),
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
    
    # Panels
    ExtractPhysicsPanel,
    HeightmapPanel,

    # Exporter
    ExportPhysics,

    # Operators
    ApplyHeightmapOperator,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Ensure settings are added to the Blender context
    bpy.types.Scene.export_physics_settings = bpy.props.PointerProperty(type=ExportPhysicsSettings)
    bpy.types.Scene.heightmap_settings = bpy.props.PointerProperty(type=HeightmapSettings)

    print("BlenderPluginSimulation registered successfully.")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.export_physics_settings
    del bpy.types.Scene.heightmap_settings

    print("BlenderPluginSimulation unregistered successfully.")
