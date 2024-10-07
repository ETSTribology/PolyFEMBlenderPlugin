import bpy

class HeightmapPanel(bpy.types.Panel):
    bl_label = "Heightmap Generator"
    bl_idname = "VIEW3D_PT_heightmap_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Heightmap'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.heightmap_settings

        if not settings:
            layout.label(text="Heightmap Settings not found.")
            return

        layout.label(text="Apply Heightmap to Selected Face")

        # Operator Button
        layout.operator("object.apply_heightmap", text="Apply Heightmap")  # Ensure this line is present

        layout.separator()

        # Display properties in a collapsible box
        box = layout.box()
        box.label(text="Heightmap Settings")

        box.prop(settings, 'amplitude')
        box.prop(settings, 'resolution')
        box.prop(settings, 'noise_type')

        if settings.noise_type == 'FBM':
            box.prop(settings, 'octaves')
            box.prop(settings, 'persistence')
            box.prop(settings, 'lacunarity')
