import bpy
import json
import os
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
)
from bpy.types import Operator, Panel, PropertyGroup


# Define properties for the addon
class PolyFEMSettings(PropertyGroup):
    # Contact Settings
    contact_enabled: BoolProperty(
        name="Enable Contact",
        description="Enable contact in the simulation",
        default=False,
    )

    contact_dhat: FloatProperty(
        name="dhat",
        description="Barrier activation distance",
        default=0.001,
    )

    contact_friction_coefficient: FloatProperty(
        name="Friction Coefficient",
        description="Coefficient of friction for contact",
        default=0.0,
    )

    contact_epsv: FloatProperty(
        name="epsv",
        description="Tangent velocity threshold",
        default=0.001,
    )

    # Time Settings
    time_integrator_items = [
        ("ImplicitEuler", "Implicit Euler", "Use Implicit Euler integrator"),
        ("ExplicitEuler", "Explicit Euler", "Use Explicit Euler integrator"),
        ("ImplicitNewmark", "Implicit Newmark", "Use Implicit Newmark integrator"),
    ]
    time_integrator: EnumProperty(
        name="Integrator",
        description="Time integration method",
        items=time_integrator_items,
        default="ImplicitEuler",
    )

    time_tend: FloatProperty(
        name="End Time",
        description="Simulation end time",
        default=1.0,
    )

    time_dt: FloatProperty(
        name="Time Step",
        description="Time step size",
        default=0.01,
    )

    # Space Settings
    space_bc_method_items = [
        ("sample", "Sample", "Sample method"),
        ("project", "Project", "Project method"),
    ]
    space_bc_method: EnumProperty(
        name="BC Method",
        description="Boundary condition method",
        items=space_bc_method_items,
        default="sample",
    )

    # Boundary Conditions
    boundary_rhs_x: FloatProperty(
        name="RHS X",
        description="Boundary condition RHS X",
        default=0.0,
    )

    boundary_rhs_y: FloatProperty(
        name="RHS Y",
        description="Boundary condition RHS Y",
        default=0.0,
    )

    boundary_rhs_z: FloatProperty(
        name="RHS Z",
        description="Boundary condition RHS Z",
        default=0.0,
    )

    # Materials Settings
    materials_type_items = [
        ("LinearElasticity", "Linear Elasticity", "Linear Elasticity material"),
        ("NeoHookean", "Neo-Hookean", "Neo-Hookean material"),
        ("SaintVenantKirchhoff", "Saint Venant-Kirchhoff", "Saint Venant-Kirchhoff material"),
    ]
    materials_type: EnumProperty(
        name="Material Type",
        description="Type of material model",
        items=materials_type_items,
        default="LinearElasticity",
    )

    materials_E: FloatProperty(
        name="Young's Modulus (E)",
        description="Young's Modulus of the material",
        default=210000.0,
    )

    materials_nu: FloatProperty(
        name="Poisson's Ratio (nu)",
        description="Poisson's Ratio of the material",
        default=0.3,
    )

    materials_rho: FloatProperty(
        name="Density (rho)",
        description="Density of the material",
        default=1000.0,
    )

    # Solver Settings
    solver_linear_solver_items = [
        ("Eigen::SparseLU", "SparseLU", "Use Eigen's SparseLU solver"),
        ("Eigen::PardisoLDLT", "PardisoLDLT", "Use Eigen's PardisoLDLT solver"),
        ("Eigen::ConjugateGradient", "Conjugate Gradient", "Use Eigen's Conjugate Gradient solver"),
    ]
    solver_linear_solver: EnumProperty(
        name="Linear Solver",
        description="Linear solver for the simulation",
        items=solver_linear_solver_items,
        default="Eigen::SparseLU",
    )

    solver_nonlinear_x_delta: FloatProperty(
        name="Nonlinear x_delta",
        description="Nonlinear solver x_delta parameter",
        default=0.0,
    )

    solver_advanced_lump_mass_matrix: BoolProperty(
        name="Lump Mass Matrix",
        description="Use lumped mass matrix",
        default=False,
    )

    solver_contact_friction_convergence_tol: FloatProperty(
        name="Friction Convergence Tolerance",
        description="Tolerance for friction convergence",
        default=0.01,
    )

    solver_contact_friction_iterations: IntProperty(
        name="Friction Iterations",
        description="Number of friction iterations",
        default=1,
    )

    # Output Settings
    output_json: StringProperty(
        name="JSON Output",
        description="Name of the JSON output file",
        default="results.json",
    )

    output_paraview_file_name: StringProperty(
        name="ParaView Filename",
        description="Name of the ParaView output file",
        default="result.vtu",
    )

    output_paraview_material: BoolProperty(
        name="Export Material",
        description="Export material data to ParaView",
        default=True,
    )

    output_paraview_body_ids: BoolProperty(
        name="Export Body IDs",
        description="Export body IDs to ParaView",
        default=True,
    )

    output_paraview_tensor_values: BoolProperty(
        name="Export Tensor Values",
        description="Export tensor values to ParaView",
        default=True,
    )

    output_paraview_nodes: BoolProperty(
        name="Export Nodes",
        description="Export nodes to ParaView",
        default=True,
    )

    output_paraview_vismesh_rel_area: FloatProperty(
        name="VisMesh Relative Area",
        description="Relative area for visualization mesh",
        default=1e-5,
    )

    output_advanced_save_solve_sequence_debug: BoolProperty(
        name="Save Solve Sequence Debug",
        description="Save debug information for solve sequence",
        default=False,
    )

    output_advanced_save_time_sequence: BoolProperty(
        name="Save Time Sequence",
        description="Save time sequence data",
        default=True,
    )

    # Project Path
    project_path: StringProperty(
        name="Project Path",
        description="Path to the project directory",
        default="//",
        subtype='DIR_PATH',
    )


