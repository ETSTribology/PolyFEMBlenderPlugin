bl_info = {
    "name": "BlenderPluginSimulation",
    "author": "Antoine Boucher",
    "version": (1, 8),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Physics",
    "description": "Extracts objects and their physics constraints and exports to JSON",
    "category": "Object",
    "wiki_url": "https://github.com/ETSTribology/BlenderPluginSimulation",
}

import bpy

# Import classes from submodules
from .export.physics_exporter import ExportPhysics
from .properties.polyfem import PolyFemSettings
from .properties.export import ExportPhysicsSettings
from .properties.heightmap import HeightmapSettings
from .operators.heightmap import ApplyHeightmapOperator
from .operators.run_polyfem import RunPolyFemSimulationOperator, OpenPolyFemDocsOperator
from .panels.heightmap import HeightmapPanel
from .panels.poly_fem import PolyFemPanel
from .properties.physics_export_addon import PhysicsExportAddonPreferences
from .panels.physics import ExtractPhysicsPanel

# List of all classes for registration
classes = [
    # PropertyGroups
    ExportPhysicsSettings,
    HeightmapSettings,
    PolyFemSettings,

    # AddonPreferences
    PhysicsExportAddonPreferences,

    # Panels
    ExtractPhysicsPanel,
    HeightmapPanel,
    PolyFemPanel,

    # Exporters
    ExportPhysics,

    # Operators
    ApplyHeightmapOperator,
    RunPolyFemSimulationOperator,
    OpenPolyFemDocsOperator,
]

def register():
    # Unregister all first to ensure a clean state
    try:
        unregister()  # This forces all classes to unregister first
    except Exception as e:
        print(f"Warning: Failed to unregister cleanly: {e}")

    # Try registering all classes again
    try:
        for cls in classes:
            if not hasattr(bpy.types, cls.__name__):
                bpy.utils.register_class(cls)

        # Add PointerProperties after PropertyGroups are registered
        bpy.types.Scene.export_physics_settings = bpy.props.PointerProperty(type=ExportPhysicsSettings)
        bpy.types.Scene.heightmap_settings = bpy.props.PointerProperty(type=HeightmapSettings)
        bpy.types.Scene.polyfem_settings = bpy.props.PointerProperty(type=PolyFemSettings)

        print("BlenderPluginSimulation registered successfully.")

    except Exception as e:
        print(f"Error during registration: {e}")
        unregister()  # Ensure cleanup if registration fails

def unregister():
    # Safely remove PointerProperties first
    if hasattr(bpy.types.Scene, "export_physics_settings"):
        del bpy.types.Scene.export_physics_settings
    if hasattr(bpy.types.Scene, "heightmap_settings"):
        del bpy.types.Scene.heightmap_settings
    if hasattr(bpy.types.Scene, "polyfem_settings"):
        del bpy.types.Scene.polyfem_settings

    # Unregister classes in reverse order
    for cls in reversed(classes):
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)

    print("BlenderPluginSimulation unregistered successfully.")
