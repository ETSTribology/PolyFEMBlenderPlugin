import bpy


class PolyFemPanel(bpy.types.Panel):
    """Creates a panel for PolyFem simulation and rendering"""
    bl_label = "PolyFem Runner"
    bl_idname = "VIEW3D_PT_polyfem_runner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PolyFem'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.polyfem_settings

        # PolyFem Simulation Settings
        layout.label(text="PolyFem Settings")
        row = layout.row()
        row.prop(settings, "polyfem_json_input", text="JSON Configuration")
        row = layout.row()
        row.prop(settings, "project_path", text="Project Directory")

        # Run Simulation Button
        layout.separator()
        layout.operator("polyfem.run_simulation", text="Run PolyFem Simulation", icon='PLAY')

        # Rendering Settings
        layout.separator()
        layout.label(text="Rendering Settings")

        # Render Animation Button
        layout.separator()
        layout.operator("polyfem.render_animation", text="Render Animation", icon='RENDER_ANIMATION')

        # Open Documentation Button
        layout.separator()
        layout.operator("polyfem.open_docs", text="Open PolyFem Docs", icon='URL')