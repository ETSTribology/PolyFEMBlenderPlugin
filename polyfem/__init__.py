import bpy
import sys
import logging
import subprocess
import threading

bl_info = {
    "name": "PolyFem",
    "author": "Antoine Boucher",
    "version": (1, 0, 14),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Physics",
    "description": "PolyFEM simulation plugin for Blender",
    "category": "Object",
    "wiki_url": "https://github.com/ETSTribology/PolyFEMBlenderPlugin",
}


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

REQUIRED_PACKAGES = ["meshio"]

def get_modules_path():
    return bpy.utils.user_resource("SCRIPTS", path="modules", create=True)

def append_modules_to_sys_path(modules_path):
    if modules_path not in sys.path:
        sys.path.append(modules_path)

def display_message(message, title="Notification", icon='INFO'):
    """Schedule a popup message to be shown on the main thread."""
    def draw(self, context):
        self.layout.label(text=message)

    # Schedule the popup on the main thread using bpy.app.timers
    def show_popup():
        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
        return None  # Return None to stop the timer

    # Register a one-time timer to run the popup on the main thread
    bpy.app.timers.register(show_popup)

def background_install_packages(packages, modules_path):
    """Install the required Python packages in the background."""
    def install_packages():
        bpy.context.window_manager.progress_begin(0, len(packages))
        for i, package in enumerate(packages):
            try:
                __import__(package)
                logger.info(f"'{package}' is already installed.")
            except ImportError:
                logger.info(f"Installing '{package}'...")
                try:
                    subprocess.check_call([
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        "--target",
                        modules_path,
                        package
                    ])
                    logger.info(f"'{package}' installed successfully.")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install '{package}'. Error: {e}")
                    display_message(f"Failed to install '{package}'. Check console for details.", icon='ERROR')
            bpy.context.window_manager.progress_update(i + 1)
        bpy.context.window_manager.progress_end()
        display_message("All required packages installed successfully.")

    threading.Thread(target=install_packages, daemon=True).start()

# Import classes from submodules using relative imports
from .operators.run_polyfem import RunPolyFemSimulationOperator, OpenPolyFemDocsOperator, RenderPolyFemAnimationOperator, ClearCachePolyFemOperator
from .operators.create_polyfem_json import CreatePolyFemJSONOperator, PolyFEMApplyMaterial, POLYFEM_OT_ShowMessageBox, PullDockerImages
from .panels.polyfem_json import PolyFEMPanel
from .properties.physics_export_addon import PhysicsExportAddonPreferences
from .properties.polyfem import PolyFEMSettings, PolyFEMObjectProperties

# List of all classes to register/unregister
classes = [
    # PropertyGroups
    PolyFEMSettings,
    PolyFEMObjectProperties,

    # AddonPreferences
    PhysicsExportAddonPreferences,

    # Panels
    PolyFEMPanel,

    # Operators
    RunPolyFemSimulationOperator,
    RenderPolyFemAnimationOperator,
    OpenPolyFemDocsOperator,
    ClearCachePolyFemOperator,
    CreatePolyFemJSONOperator,
    PolyFEMApplyMaterial,

    # ShowMessageBox
    POLYFEM_OT_ShowMessageBox,

    # Add more classes here...
    PullDockerImages
]

def is_class_registered(cls):
    """Check if a class is already registered in Blender."""
    try:
        bpy.utils.unregister_class(cls)
    except RuntimeError:
        pass  # Class wasn't registered, so we can ignore this error.

def register():
    """Register all classes and set up PointerProperties."""
    modules_path = get_modules_path()
    append_modules_to_sys_path(modules_path)

    # Install required packages in the background
    background_install_packages(REQUIRED_PACKAGES, modules_path)

    bl_info = {
        "name": "PolyFem",
        "author": "Antoine Boucher",
        "version": (1, 0, 14),
        "blender": (4, 2, 0),
        "location": "View3D > Sidebar > Physics",
        "description": "PolyFEM simulation plugin for Blender",
        "category": "Object",
        "wiki_url": "https://github.com/ETSTribology/PolyFEMBlenderPlugin",
    }


    try:
        for cls in classes:
            is_class_registered(cls)  # Unregister class if already registered
            bpy.utils.register_class(cls)  # Then register the class

        # Register PointerProperties
        bpy.types.Scene.polyfem_settings = bpy.props.PointerProperty(type=PolyFEMSettings)
        bpy.types.Object.polyfem_props = bpy.props.PointerProperty(type=PolyFEMObjectProperties)

        logger.info(f"{bl_info.get('name', 'Addon')} v{bl_info.get('version', '0.0')} registered successfully.")

    except Exception as e:
        logger.error(f"Error during registration: {e}")
        unregister()  # If error, ensure cleanup
        raise e

def unregister():
    """Unregister all classes and remove PointerProperties."""
    try:

        bl_info = {
            "name": "PolyFem",
            "author": "Antoine Boucher",
            "version": (1, 0, 14),
            "blender": (4, 2, 0),
            "location": "View3D > Sidebar > Physics",
            "description": "PolyFEM simulation plugin for Blender",
            "category": "Object",
            "wiki_url": "https://github.com/ETSTribology/PolyFEMBlenderPlugin",
        }


        # Unregister PointerProperties first to avoid dependency issues
        if hasattr(bpy.types.Scene, "polyfem_settings"):
            del bpy.types.Scene.polyfem_settings
        if hasattr(bpy.types.Object, "polyfem_props"):
            del bpy.types.Object.polyfem_props

        # Unregister classes in reverse order to handle dependencies correctly
        for cls in reversed(classes):
            is_class_registered(cls)

        logger.info(f"{bl_info.get('name', 'Addon')} unregistered successfully.")

    except Exception as e:
        logger.error(f"Error during unregistration: {e}")
