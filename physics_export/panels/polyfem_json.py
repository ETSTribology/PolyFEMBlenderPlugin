import bpy
from bpy.types import Panel

class PolyFEMJSONConfigPanel(Panel):
    """Creates a panel for configuring PolyFEM JSON settings"""
    bl_label = "PolyFEM JSON Configuration"
    bl_idname = "VIEW3D_PT_polyfem_json_config"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PolyFEM Config'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.polyfem_json_settings

        # Display the properties
        layout.prop(settings, 'export_path')
        layout.prop(settings, 'json_filename')
        layout.prop(settings, 'export_format')
        layout.prop(settings, 'export_stl')
        layout.prop(settings, 'export_selected_only')
        layout.prop(settings, 'export_point_selection')

        # Operator button
        layout.operator("physics_export.export_physics", text="Export Physics to JSON")

        if settings.export_selected_only and not context.selected_objects:
            layout.label(text="No objects selected.", icon='ERROR')

        # Project Path
        layout.label(text="Project Settings", icon='FILE_FOLDER')
        layout.prop(settings, "project_path")

        layout.separator()

        # Contact Section
        layout.label(text="Contact Settings", icon='MOD_PHYSICS')
        layout.prop(settings, "contact_enabled")
        layout.prop(settings, "contact_dhat")
        layout.prop(settings, "contact_friction_coefficient")
        layout.prop(settings, "contact_epsv")

        layout.separator()

        # Time Section
        layout.label(text="Time Settings", icon='TIME')
        layout.prop(settings, "time_integrator")
        layout.prop(settings, "time_tend")
        layout.prop(settings, "time_dt")

        layout.separator()

        # Space Section
        layout.label(text="Space Settings", icon='WORLD')
        layout.prop(settings, "space_bc_method")

        layout.separator()

        # Boundary Conditions Section
        layout.label(text="Boundary Conditions", icon='MOD_DYNAMICPAINT')
        layout.prop(settings, "boundary_rhs_x")
        layout.prop(settings, "boundary_rhs_y")
        layout.prop(settings, "boundary_rhs_z")

        layout.separator()

        # Materials Section
        layout.label(text="Materials", icon='MATERIAL')
        layout.prop(settings, "materials_type")
        layout.prop(settings, "materials_E")
        layout.prop(settings, "materials_nu")
        layout.prop(settings, "materials_rho")

        layout.separator()

        # Solver Section
        layout.label(text="Solver Settings", icon='MODIFIER')
        layout.prop(settings, "solver_linear_solver")
        layout.prop(settings, "solver_nonlinear_x_delta")
        layout.prop(settings, "solver_advanced_lump_mass_matrix")
        layout.prop(settings, "solver_contact_friction_convergence_tol")
        layout.prop(settings, "solver_contact_friction_iterations")

        layout.separator()

        # Output Section
        layout.label(text="Output Settings", icon='OUTPUT')
        layout.prop(settings, "output_json")
        layout.prop(settings, "output_paraview_file_name")
        layout.prop(settings, "output_paraview_material")
        layout.prop(settings, "output_paraview_body_ids")
        layout.prop(settings, "output_paraview_tensor_values")
        layout.prop(settings, "output_paraview_nodes")
        layout.prop(settings, "output_paraview_vismesh_rel_area")
        layout.prop(settings, "output_advanced_save_solve_sequence_debug")
        layout.prop(settings, "output_advanced_save_time_sequence")

        layout.separator()

        # Create JSON Button
        layout.operator("polyfem.create_json", text="Create JSON Configuration", icon='FILE_TICK')
