# panels/heightmap.py
import bpy

class HeightmapPanel(bpy.types.Panel):
    """Creates a panel in the 3D Viewport's sidebar for heightmap generation"""
    bl_label = "Heightmap Generator"
    bl_idname = "VIEW3D_PT_heightmap_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Heightmap'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.heightmap_settings

        layout.label(text="Apply Heightmap to Selected Face")

        # Operator Button
        layout.operator("object.apply_heightmap", text="Apply Heightmap")

        layout.separator()

        # Display properties in a collapsible box
        box = layout.box()
        box.label(text="Heightmap Settings")

        box.prop(settings, 'amplitude')
        box.prop(settings, 'resolution')
        box.prop(settings, 'noise_type')

        if settings.noise_type == 'FBM':
            box.prop(settings, 'H')
            box.prop(settings, 'lacunarity')
            box.prop(settings, 'octaves')

        if settings.noise_type == 'GABOR':
            box.prop(settings, 'orientation')
            box.prop(settings, 'bandwidth')
            box.prop(settings, 'power_spectrum')

        layout.separator()
        box = layout.box()
        box.label(text="Normal Map to Displacement Map")

        box.prop(settings, 'normal_map')
        box.prop(settings, 'project_path')

        # New properties for displacement map generation
        box.prop(settings, 'contrast')
        box.prop(settings, 'invert_displacement')

        box.operator("object.convert_normal_to_displacement", text="Convert to Displacement Map")

        layout.separator()