import bpy
import json
import os
from bpy.props import StringProperty
from bpy.types import Operator


class CreatePolyFemJSONOperator(Operator):
    """Create a JSON configuration file for PolyFem simulation"""
    bl_idname = "polyfem.create_json"
    bl_label = "Create PolyFem JSON"
    bl_description = "Generate a JSON configuration file for PolyFem simulation"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Property for JSON filename; defaults to 'polyfem_config.json'
    json_filename: StringProperty(
        name="JSON Filename",
        description="Name of the JSON configuration file",
        default="polyfem_config.json",
        subtype='FILE_NAME'
    )
    
    def execute(self, context):
        settings = context.scene.polyfem_settings
        project_path = bpy.path.abspath(settings.project_path)
        json_filename = self.json_filename
        json_path = os.path.join(project_path, json_filename)
        
        # Define the JSON data structure based on the provided structure
        json_data = {
            "contact": {
                "enabled": settings.contact_enabled,
                "dhat": settings.contact_dhat,
                "friction_coefficient": settings.contact_friction_coefficient,
                "epsv": settings.contact_epsv
            },
            "time": {
                "integrator": settings.time_integrator,
                "tend": settings.time_tend,
                "dt": settings.time_dt
            },
            "space": {
                "advanced": {
                    "bc_method": settings.space_bc_method
                }
            },
            "boundary_conditions": {
                "rhs": [settings.boundary_rhs_x, settings.boundary_rhs_y, settings.boundary_rhs_z]
            },
            "materials": {
                "type": settings.materials_type,
                "E": settings.materials_E,
                "nu": settings.materials_nu,
                "rho": settings.materials_rho
            },
            "solver": {
                "linear": {
                    "solver": [settings.solver_linear_solver]
                },
                "nonlinear": {
                    "x_delta": settings.solver_nonlinear_x_delta
                },
                "advanced": {
                    "lump_mass_matrix": settings.solver_advanced_lump_mass_matrix
                },
                "contact": {
                    "friction_convergence_tol": settings.solver_contact_friction_convergence_tol,
                    "friction_iterations": settings.solver_contact_friction_iterations
                }
            },
            "output": {
                "json": settings.output_json,
                "paraview": {
                    "file_name": settings.output_paraview_file_name,
                    "options": {
                        "material": settings.output_paraview_material,
                        "body_ids": settings.output_paraview_body_ids,
                        "tensor_values": settings.output_paraview_tensor_values,
                        "nodes": settings.output_paraview_nodes
                    },
                    "vismesh_rel_area": settings.output_paraview_vismesh_rel_area
                },
                "advanced": {
                    "save_solve_sequence_debug": settings.output_advanced_save_solve_sequence_debug,
                    "save_time_sequence": settings.output_advanced_save_time_sequence
                }
            }
        }
        
        try:
            with open(json_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            self.report({'INFO'}, f"JSON file created at '{json_path}'")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create JSON file: {e}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        """Invoke the operator and bring up the file browser."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        """Draw the operator's properties in the UI."""
        layout = self.layout
        layout.prop(self, "json_filename")
