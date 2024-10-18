import bpy

class PolyFemPanel(bpy.types.Panel):
    """Creates a panel for running PolyFem"""
    bl_label = "PolyFem Runner"
    bl_idname = "VIEW3D_PT_polyfem_runner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PolyFem'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.polyfem_settings

        layout.label(text="PolyFem Executable Path:")
        layout.prop(settings, "polyfem_executable_path", text="")

        layout.label(text="PolyFem JSON Configuration:")
        layout.prop(settings, "polyfem_json_input", text="", expand=True)

        layout.label(text="Project Path:")
        layout.prop(settings, "project_path", text="")

        layout.operator("polyfem.run_simulation", text="Run PolyFem Simulation", icon='PLAY')
        layout.operator("polyfem.open_docs", text="Open PolyFem Docs", icon='URL')
