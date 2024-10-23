import bpy
from bpy.types import Panel

class PolyFEMPanel(Panel):
    """Creates a panel for configuring PolyFEM JSON settings"""
    bl_label = "PolyFEM"
    bl_idname = "VIEW3D_PT_polyfem"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PolyFEM Config'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.polyfem_settings

        # Export Settings
        box = layout.box()
        box.label(text="Export Settings", icon='EXPORT')
        box.prop(settings, 'export_path')
        box.prop(settings, 'json_filename')
        box.prop(settings, 'export_format')
        box.prop(settings, 'export_stl')
        box.prop(settings, 'export_selected_only')
        box.prop(settings, 'export_point_selection')

        if settings.export_selected_only and not context.selected_objects:
            box.label(text="No objects selected.", icon='ERROR')

        # Project Path
        box = layout.box()
        box.label(text="Project Settings", icon='FILE_FOLDER')
        box.prop(settings, "project_path")

        # Contact Settings
        box = layout.box()
        box.label(text="Contact Settings", icon='MOD_PHYSICS')
        box.prop(settings, "contact_enabled")
        sub = box.column(align=True)
        sub.enabled = settings.contact_enabled
        sub.prop(settings, "contact_dhat")
        sub.prop(settings, "contact_friction_coefficient")
        sub.prop(settings, "contact_epsv")

        # Time Settings
        box = layout.box()
        box.label(text="Time Settings", icon='TIME')
        box.prop(settings, "time_integrator")
        box.prop(settings, "time_tend")
        box.prop(settings, "time_dt")

        # Space Settings
        box = layout.box()
        box.label(text="Space Settings", icon='WORLD')
        box.prop(settings, "space_bc_method")

        # Boundary Conditions
        box = layout.box()
        box.label(text="Boundary Conditions", icon='MOD_DYNAMICPAINT')
        box.prop(settings, "boundary_rhs_x")
        box.prop(settings, "boundary_rhs_y")
        box.prop(settings, "boundary_rhs_z")

        # Materials Section
        box = layout.box()
        box.label(text="Materials", icon='MATERIAL')
        box.prop(settings, "materials_type")
        box.prop(settings, "selected_material")
        box.prop(settings, "materials_E")
        box.prop(settings, "materials_nu")
        box.prop(settings, "materials_rho")

        # Solver Settings
        box = layout.box()
        box.label(text="Solver Settings", icon='MODIFIER')
        box.prop(settings, "solver_linear_solver")
        sub = box.column(align=True)
        sub.prop(settings, "solver_nonlinear_x_delta")
        sub.prop(settings, "solver_advanced_lump_mass_matrix")
        sub.prop(settings, "solver_contact_friction_convergence_tol")
        sub.prop(settings, "solver_contact_friction_iterations")

        # Output Settings
        box = layout.box()
        box.label(text="Output Settings", icon='OUTPUT')
        box.prop(settings, "output_json")
        box.prop(settings, "output_paraview_file_name")
        sub = box.column(align=True)
        sub.prop(settings, "output_paraview_material")
        sub.prop(settings, "output_paraview_body_ids")
        sub.prop(settings, "output_paraview_tensor_values")
        sub.prop(settings, "output_paraview_nodes")
        sub.prop(settings, "output_paraview_vismesh_rel_area")
        sub.prop(settings, "output_advanced_save_solve_sequence_debug")
        sub.prop(settings, "output_advanced_save_time_sequence")

        # Actions
        layout.operator("polyfem.create_json", text="Create JSON Configuration", icon='FILE_TICK')
        layout.operator("polyfem.run_simulation", text="Run PolyFem Simulation", icon='PLAY')
        layout.operator("polyfem.render_animation", text="Render Animation", icon='RENDER_ANIMATION')
        layout.operator("polyfem.clear_cache", text="Clear Cache", icon='X')
        layout.operator("polyfem.open_docs", text="Open PolyFem Docs", icon='URL')
