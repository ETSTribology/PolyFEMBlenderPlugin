import bpy
from bpy.props import BoolProperty

class PhysicsExportAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = "physics_export"

    enable_heightmap: BoolProperty(
        name="Enable Heightmap",
        description="Enable the Heightmap Generator feature",
        default=True
    )

    enable_tetwild: BoolProperty(
        name="Enable TetWild Mesh Export",
        description="Enable the TetWild mesh export feature (via Docker)",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Choose which features to enable:")
        layout.prop(self, "enable_heightmap", text="Heightmap Generator")
        layout.prop(self, "enable_tetwild", text="TetWild Mesh Export")
