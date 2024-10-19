import bpy
from bpy.types import Panel


class PolyFemJSONConfigPanel(Panel):
    """Creates a panel for configuring PolyFem JSON settings"""
    bl_label = "PolyFem JSON Configuration"
    bl_idname = "VIEW3D_PT_polyfem_json_config"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'PolyFem'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.polyfem_settings

        # Contact Section
        layout.label(text="Contact Settings", icon='CONSTRAINT')
        row = layout.row()
        row.prop(settings, "contact_enabled")
        row = layout.row()
        row.prop(settings, "contact_dhat")
        row = layout.row()
        row.prop(settings, "contact_friction_coefficient")
        row = layout.row()
        row.prop(settings, "contact_epsv")

        layout.separator()

        # Time Section
        layout.label(text="Time Settings", icon='TIME')
        row = layout.row()
        row.prop(settings, "time_integrator")
        row = layout.row()
        row.prop(settings, "time_tend")
        row = layout.row()
        row.prop(settings, "time_dt")

        layout.separator()

        # Space Section
        layout.label(text="Space Settings", icon='MOD_SPACE')
        row = layout.row()
        row.prop(settings, "space_bc_method")

        layout.separator()

        # Boundary Conditions Section
        layout.label(text="Boundary Conditions", icon='BORDER_RECT')
        row = layout.row()
        row.prop(settings, "boundary_rhs_x", text="RHS X")
        row.prop(settings, "boundary_rhs_y", text="RHS Y")
        row.prop(settings, "boundary_rhs_z", text="RHS Z")

        layout.separator()

        # Materials Section
        layout.label(text="Materials", icon='MATERIAL')
        row = layout.row()
        row.prop(settings, "materials_type")
        row = layout.row()
        row.prop(settings, "materials_E")
        row = layout.row()
        row.prop(settings, "materials_nu")
        row = layout.row()
        row.prop(settings, "materials_rho")

        layout.separator()

        # Solver Section
        layout.label(text="Solver Settings", icon='SOLVER')
        row = layout.row()
        row.prop(settings, "solver_linear_solver")
        row = layout.row()
        row.prop(settings, "solver_nonlinear_x_delta")
        row = layout.row()
        row.prop(settings, "solver_advanced_lump_mass_matrix")
        row = layout.row()
        row.prop(settings, "solver_contact_friction_convergence_tol")
        row.prop(settings, "solver_contact_friction_iterations")

        layout.separator()

        # Output Section
        layout.label(text="Output Settings", icon='OUTPUT')
        row = layout.row()
        row.prop(settings, "output_json", text="JSON Output")
        row = layout.row()
        row.prop(settings, "output_paraview_file_name", text="ParaView Filename")
        row = layout.row()
        row.prop(settings, "output_paraview_material")
        row.prop(settings, "output_paraview_body_ids")
        row = layout.row()
        row.prop(settings, "output_paraview_tensor_values")
        row.prop(settings, "output_paraview_nodes")
        row = layout.row()
        row.prop(settings, "output_paraview_vismesh_rel_area")
        row = layout.row()
        row.prop(settings, "output_advanced_save_solve_sequence_debug")
        row.prop(settings, "output_advanced_save_time_sequence")

        layout.separator()

        # Create JSON Button
        layout.operator("polyfem.create_json", text="Create JSON Configuration", icon='FILE_TICK')
