import bpy
import sys
import os
import logging
import zipfile

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Import classes from submodules using relative imports
from .properties.polyfem import PolyFemSettings
from .properties.heightmap import HeightmapSettings
from .operators.heightmap import ApplyHeightmapOperator
from .operators.run_polyfem import RunPolyFemSimulationOperator, OpenPolyFemDocsOperator, RenderPolyFemAnimationOperator, ClearCachePolyFemOperator,  POLYFEM_OT_ShowMessageBox
from .operators.create_polyfem_json import CreatePolyFemJSONOperator
from .operators.convert_normal_to_displacement import ConvertNormalToDisplacementOperator
from .panels.heightmap import HeightmapPanel
from .panels.poly_fem import PolyFemPanel
from .panels.polyfem_json import PolyFEMJSONConfigPanel
from .properties.physics_export_addon import PhysicsExportAddonPreferences
from .properties.polyfem_json import PolyFEMJSONSettings

# List of all classes to register/unregister
classes = [
    # PropertyGroups
    HeightmapSettings,
    PolyFemSettings,
    PolyFEMJSONSettings,

    # AddonPreferences
    PhysicsExportAddonPreferences,

    # Panels
    HeightmapPanel,
    PolyFemPanel,
    PolyFEMJSONConfigPanel,


    # Operators
    ApplyHeightmapOperator,
    ConvertNormalToDisplacementOperator,
    RunPolyFemSimulationOperator,
    RenderPolyFemAnimationOperator,
    OpenPolyFemDocsOperator,
    ClearCachePolyFemOperator,
    CreatePolyFemJSONOperator,

    # ShowMessageBox
    POLYFEM_OT_ShowMessageBox
]

bl_info = {
    "name": "BlenderPluginSimulation",
    "author": "Antoine Boucher",
    "version": (1, 10),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Physics",
    "description": "Extracts objects and their physics constraints and exports to JSON",
    "category": "Object",
    "wiki_url": "https://github.com/ETSTribology/BlenderPluginSimulation",
}

def is_class_registered(cls):
    """Check if a class is already registered in Blender."""
    try:
        bpy.utils.unregister_class(cls)
    except RuntimeError:
        pass  # Class wasn't registered, so we can ignore this error.

def register():
    """Register all classes and set up PointerProperties."""
    bl_info = {
        "name": "BlenderPluginSimulation",
        "version": (1, 8),
        "blender": (4, 2, 0),
    }
    try:
        for cls in classes:
            is_class_registered(cls)  # Unregister class if already registered
            bpy.utils.register_class(cls)  # Then register the class

        # Register PointerProperties
        bpy.types.Scene.heightmap_settings = bpy.props.PointerProperty(type=HeightmapSettings)
        bpy.types.Scene.polyfem_settings = bpy.props.PointerProperty(type=PolyFemSettings)
        bpy.types.Scene.polyfem_json_settings = bpy.props.PointerProperty(type=PolyFEMJSONSettings)

        logger.info(f"{bl_info.get('name', 'Addon')} v{bl_info.get('version', '0.0')} registered successfully.")

    except Exception as e:
        logger.error(f"Error during registration: {e}")
        unregister()  # If error, ensure cleanup
        raise e

def unregister():
    """Unregister all classes and remove PointerProperties."""
    bl_info = {
        "name": "BlenderPluginSimulation",
        "version": (1, 8),
        "blender": (4, 2, 0),
    }
    try:
        # Unregister PointerProperties first to avoid dependency issues
        if hasattr(bpy.types.Scene, "heightmap_settings"):
            del bpy.types.Scene.heightmap_settings
        if hasattr(bpy.types.Scene, "polyfem_settings"):
            del bpy.types.Scene.polyfem_settings
        if hasattr(bpy.types.Scene, "polyfem_json_settings"):
            del bpy.types.Scene.polyfem_json_settings

        # Unregister classes in reverse order to handle dependencies correctly
        for cls in reversed(classes):
            is_class_registered(cls)

        logger.info(f"{bl_info.get('name', 'Addon')} unregistered successfully.")

    except Exception as e:
        logger.error(f"Error during unregistration: {e}")
