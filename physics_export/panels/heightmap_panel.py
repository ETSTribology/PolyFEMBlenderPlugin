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

        layout.label(text="Apply Heightmap to Selected Face")

        # Display properties
        layout.prop(settings, 'amplitude')
        layout.prop(settings, 'resolution')
        layout.prop(settings, 'noise_type')

        if settings.noise_type == 'FBM':
            layout.prop(settings, 'octaves')
            layout.prop(settings, 'persistence')
            layout.prop(settings, 'lacunarity')

        # Operator button
        layout.operator("object.apply_heightmap", text="Apply Heightmap")

