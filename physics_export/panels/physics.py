import bpy

class ExtractPhysicsPanel(bpy.types.Panel):
    """Creates a panel in the 3D Viewport's sidebar for exporting physics constraints"""
    bl_label = "Extract Physics Constraints"
    bl_idname = "VIEW3D_PT_extract_physics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Physics'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.export_physics_settings

        # Display the properties
        layout.prop(settings, 'export_directory')
        layout.prop(settings, 'json_filename')
        layout.prop(settings, 'export_format')
        layout.prop(settings, 'export_stl')
        layout.prop(settings, 'export_selected_only')
        layout.prop(settings, 'export_point_selection')

        # Operator button
        layout.operator("physics_export.export_physics", text="Export Physics to JSON")

        if settings.export_selected_only and not context.selected_objects:
            layout.label(text="No objects selected.", icon='ERROR')
