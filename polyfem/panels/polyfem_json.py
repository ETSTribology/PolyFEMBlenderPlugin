import bpy
from bpy.types import Panel

class PolyFEMPanel(Panel):
    """Creates a panel for configuring PolyFEM JSON settings and applying materials to selected objects"""
    bl_label = "PolyFEM"
    bl_idname = "PHYSICS_PT_polyfem"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'physics'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.polyfem_settings

        # Display selected objects and assign materials
        box = layout.box()
        row = box.row()
        row.label(text="Selected Objects and Materials", icon='OBJECT_DATA')

        if context.selected_objects:
            for obj in context.selected_objects:
                # Access the object's PolyFEM properties
                polyfem_props = obj.polyfem_props

                # Create collapsible box for each object
                obj_box = box.box()
                row = obj_box.row()

                # Add a triangle icon for collapse and expansion, bound to the collapse state
                row.prop(polyfem_props, "collapse", text="", icon="TRIA_DOWN" if polyfem_props.collapse else "TRIA_RIGHT", emboss=False)
                row.label(text=f"Object: {obj.name}", icon='OBJECT_DATA')

                # Only expand the object info if the arrow is clicked
                if polyfem_props.collapse:
                    # Display and allow renaming the object
                    obj_box.prop(obj, "name", text="Rename Object", icon='FONT_DATA')

                    # Display the object's assigned material and material ID
                    material_id = obj.get("material_id", "No Material")
                    obj_box.label(text=f"Material ID: {material_id}")

                    # Show material properties if they exist
                    if "material_type" in obj.keys():
                        obj_box.label(text=f"Material Type: {obj['material_type']}")
                        obj_box.label(text=f"Young's Modulus (E): {obj['material_E']}")
                        obj_box.label(text=f"Poisson's Ratio (nu): {obj['material_nu']}")
                        obj_box.label(text=f"Density (rho): {obj['material_rho']}")
                    else:
                        obj_box.label(text="No Material Applied", icon='ERROR')

                    # Show the actual material assigned to the object
                    if obj.data.materials:
                        obj_box.label(text=f"Assigned Material: {obj.data.materials[0].name}")
                    else:
                        obj_box.label(text="No material assigned to the object", icon='ERROR')

                    # Apply material from dropdown to the object
                    obj_box.prop(context.scene.polyfem_settings, "selected_material", text="Assign Material")

                    # Button to apply the selected material
                    apply_material_btn = obj_box.operator("polyfem.apply_material", text="Apply Material", icon='MATERIAL')
                    apply_material_btn.obj_name = obj.name  # Pass the object name to the operator
        else:
            box.label(text="No objects selected.", icon='ERROR')

        # Export Settings (Collapsible)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_export_settings", icon="TRIA_DOWN" if settings.show_export_settings else "TRIA_RIGHT", emboss=False)
        row.label(text="Export Settings", icon='EXPORT')
        if settings.show_export_settings:
            sub_box = box.box()
            sub_box.prop(settings, 'export_path')
            sub_box.prop(settings, 'json_filename')
            sub_box.prop(settings, 'export_format', icon='FILE')
            sub_box.prop(settings, 'export_stl', icon='MESH_CUBE')
            sub_box.prop(settings, 'export_selected_only', icon='RESTRICT_SELECT_OFF')
            sub_box.prop(settings, 'export_point_selection', icon='VERTEXSEL')
            if settings.export_selected_only and not context.selected_objects:
                sub_box.label(text="No objects selected.", icon='ERROR')

        # Contact Settings (Collapsible)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_contact_settings", icon="TRIA_DOWN" if settings.show_contact_settings else "TRIA_RIGHT", emboss=False)
        row.label(text="Contact Settings", icon='MOD_PHYSICS')
        if settings.show_contact_settings:
            sub_box = box.box()
            sub_box.prop(settings, "contact_enabled", icon='CHECKBOX_HLT')
            sub = sub_box.column(align=True)
            sub.enabled = settings.contact_enabled
            sub.prop(settings, "contact_dhat")
            sub.prop(settings, "contact_friction_coefficient")
            sub.prop(settings, "contact_epsv")

        # Time Settings (Collapsible)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_time_settings", icon="TRIA_DOWN" if settings.show_time_settings else "TRIA_RIGHT", emboss=False)
        row.label(text="Time Settings", icon='TIME')
        if settings.show_time_settings:
            sub_box = box.box()
            sub_box.prop(settings, "time_integrator", icon='TIME')
            sub_box.prop(settings, "time_tend")
            sub_box.prop(settings, "time_dt")

        # Space Settings (Collapsible)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_space_settings", icon="TRIA_DOWN" if settings.show_space_settings else "TRIA_RIGHT", emboss=False)
        row.label(text="Space Settings", icon='GRID')
        if settings.show_space_settings:
            sub_box = box.box()
            sub_box.prop(settings, "space_bc_method")

        # Boundary Conditions (Collapsible)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_boundary_conditions", icon="TRIA_DOWN" if settings.show_boundary_conditions else "TRIA_RIGHT", emboss=False)
        row.label(text="Boundary Conditions", icon='CONSTRAINT')
        if settings.show_boundary_conditions:
            sub_box = box.box()
            sub_box.prop(settings, "boundary_rhs_x", icon='AXIS_FRONT')
            sub_box.prop(settings, "boundary_rhs_y", icon='AXIS_SIDE')
            sub_box.prop(settings, "boundary_rhs_z", icon='AXIS_TOP')

        # Materials Section (Collapsible)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_materials", icon="TRIA_DOWN" if settings.show_materials else "TRIA_RIGHT", emboss=False)
        row.label(text="Materials", icon='MATERIAL')
        if settings.show_materials:
            sub_box = box.box()
            sub_box.prop(settings, "materials_type", icon='SHADING_RENDERED')
            sub_box.prop(settings, "selected_material", icon='MATERIAL')
            sub_box.prop(settings, "materials_E", icon='PHYSICS')
            sub_box.prop(settings, "materials_nu", icon='PHYSICS')
            sub_box.prop(settings, "materials_rho", icon='PHYSICS')


        # Solver Settings (Collapsible)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_solver_settings", icon="TRIA_DOWN" if settings.show_solver_settings else "TRIA_RIGHT", emboss=False)
        row.label(text="Solver Settings", icon='MODIFIER')
        if settings.show_solver_settings:
            sub_box = box.box()
            sub_box.prop(settings, "solver_linear_solver", icon='MOD_SIMPLIFY')
            sub_box.prop(settings, "solver_nonlinear_x_delta", icon='MOD_SCREW')
            sub_box.prop(settings, "solver_advanced_lump_mass_matrix", icon='MOD_LATTICE')
            sub_box.prop(settings, "solver_contact_friction_convergence_tol", icon='MOD_CLOTH')
            sub_box.prop(settings, "solver_contact_friction_iterations", icon='FORCE_FIELD')

        # Output Settings (Collapsible)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_output_settings", icon="TRIA_DOWN" if settings.show_output_settings else "TRIA_RIGHT", emboss=False)
        row.label(text="Output Settings", icon='OUTPUT')
        if settings.show_output_settings:
            sub_box = box.box()
            sub_box.prop(settings, "output_json", icon='FILE')
            sub_box.prop(settings, "output_paraview_file_name", icon='FILE_BLEND')
            sub_box.prop(settings, "output_paraview_material", icon='MATERIAL')
            sub_box.prop(settings, "output_paraview_body_ids", icon='OBJECT_DATAMODE')
            sub_box.prop(settings, "output_paraview_tensor_values", icon='MOD_WARP')
            sub_box.prop(settings, "output_paraview_nodes", icon='VERTEXSEL')
            sub_box.prop(settings, "output_paraview_vismesh_rel_area", icon='MESH_GRID')
            sub_box.prop(settings, "output_advanced_save_solve_sequence_debug", icon='SEQUENCE')
            sub_box.prop(settings, "output_advanced_save_time_sequence", icon='TIME')

        # Actions
        layout.operator("polyfem.create_json", text="Create JSON Configuration", icon='FILE_TICK')
        layout.operator("polyfem.run_simulation", text="Run PolyFem Simulation", icon='PLAY')
        layout.operator("polyfem.render_animation", text="Render Animation", icon='RENDER_ANIMATION')
        layout.operator("polyfem.clear_cache", text="Clear Cache", icon='X')
        layout.operator("polyfem.open_docs", text="Open PolyFem Docs", icon='URL')