import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty, EnumProperty

class PolyFemSettings(PropertyGroup):
    # Existing properties
    polyfem_executable_path: StringProperty(
        name="Executable Path",
        description="Path to the PolyFem executable",
        subtype='FILE_PATH',
        default=""
    )
    polyfem_json_input: StringProperty(
        name="JSON Input",
        description="Path to the PolyFem JSON input file",
        subtype='FILE_PATH',
        default=""
    )
    project_path: StringProperty(
        name="Project Directory",
        description="Directory containing simulation files",
        subtype='DIR_PATH',
        default=""
    )
    start_frame: IntProperty(
        name="Start Frame",
        description="Starting frame for the animation",
        default=1
    )
    frame_interval: IntProperty(
        name="Frame Interval",
        description="Number of frames between each visibility change",
        default=10
    )
    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Scale factor to apply to deformation vectors",
        default=1.0
    )
    json_filename: StringProperty(
        name="JSON Filename",
        description="Name of the JSON configuration file",
        default="polyfem_config.json",
        subtype='FILE_NAME'
    )

    # Contact Section
    contact_enabled: BoolProperty(
        name="Contact Enabled",
        description="Enable contact",
        default=True
    )
    contact_dhat: FloatProperty(
        name="Contact DHat",
        description="Value for dhat in contact",
        default=1e-3
    )
    contact_friction_coefficient: FloatProperty(
        name="Friction Coefficient",
        description="Friction coefficient for contact",
        default=0.0
    )
    contact_epsv: FloatProperty(
        name="Contact EpsV",
        description="Value for epsv in contact",
        default=1e-3
    )

    # Time Section
    time_integrator: EnumProperty(
        name="Integrator",
        description="Time integrator method",
        items=[
            ('ImplicitEuler', "Implicit Euler", "Use Implicit Euler integrator"),
            ('ExplicitEuler', "Explicit Euler", "Use Explicit Euler integrator"),
            ('RungeKutta', "Runge-Kutta", "Use Runge-Kutta integrator")
        ],
        default='ImplicitEuler'
    )
    time_tend: FloatProperty(
        name="End Time (tend)",
        description="End time of the simulation",
        default=5.0
    )
    time_dt: FloatProperty(
        name="Time Step (dt)",
        description="Time step size",
        default=0.025
    )
    
    # Space Section
    space_bc_method: EnumProperty(
        name="Boundary Condition Method",
        description="Method for boundary conditions",
        items=[
            ('sample', "Sample", "Use sample boundary condition method"),
            ('standard', "Standard", "Use standard boundary condition method"),
            ('custom', "Custom", "Use custom boundary condition method")
        ],
        default='sample'
    )
    
    # Boundary Conditions Section
    boundary_rhs_x: FloatProperty(
        name="RHS X",
        description="Right-hand side value for X direction",
        default=0.0
    )
    boundary_rhs_y: FloatProperty(
        name="RHS Y",
        description="Right-hand side value for Y direction",
        default=9.81
    )
    boundary_rhs_z: FloatProperty(
        name="RHS Z",
        description="Right-hand side value for Z direction",
        default=0.0
    )
    
    # Materials Section
    materials_type: EnumProperty(
        name="Material Type",
        description="Type of material",
        items=[
            ('NeoHookean', "Neo-Hookean", "Use Neo-Hookean material model"),
            ('StVK', "St. Venant-Kirchhoff", "Use St. Venant-Kirchhoff material model"),
            ('MooneyRivlin', "Mooney-Rivlin", "Use Mooney-Rivlin material model")
        ],
        default='NeoHookean'
    )
    materials_E: FloatProperty(
        name="Young's Modulus (E)",
        description="Young's modulus of the material",
        default=1e5
    )
    materials_nu: FloatProperty(
        name="Poisson's Ratio (nu)",
        description="Poisson's ratio of the material",
        default=0.4
    )
    materials_rho: FloatProperty(
        name="Density (rho)",
        description="Density of the material",
        default=1000.0
    )
    
    # Solver Section
    solver_linear_solver: EnumProperty(
        name="Linear Solver",
        description="Linear solver options",
        items=[
            ('Eigen::PardisoLDLT', "Pardiso LDLT", "Use Eigen's Pardiso LDLT solver"),
            ('Eigen::CholmodDecomposition', "Cholmod Decomposition", "Use Eigen's Cholmod Decomposition solver"),
            ('Other', "Other", "Use another linear solver")
        ],
        default='Eigen::PardisoLDLT'
    )
    solver_nonlinear_x_delta: FloatProperty(
        name="Nonlinear X Delta",
        description="X delta value for nonlinear solver",
        default=1e-05
    )
    solver_advanced_lump_mass_matrix: BoolProperty(
        name="Lump Mass Matrix",
        description="Enable lump mass matrix in advanced solver settings",
        default=True
    )
    solver_contact_friction_convergence_tol: FloatProperty(
        name="Friction Convergence Tolerance",
        description="Tolerance for friction convergence",
        default=0.01
    )
    solver_contact_friction_iterations: IntProperty(
        name="Friction Iterations",
        description="Number of friction iterations",
        default=1
    )
    
    # Output Section
    output_json: StringProperty(
        name="JSON Output",
        description="Filename for JSON output",
        default="results.json",
        subtype='FILE_NAME'
    )
    output_paraview_file_name: StringProperty(
        name="ParaView Filename",
        description="Filename for ParaView output",
        default="sim.pvd",
        subtype='FILE_NAME'
    )
    output_paraview_material: BoolProperty(
        name="Include Material",
        description="Include material information in ParaView output",
        default=True
    )
    output_paraview_body_ids: BoolProperty(
        name="Include Body IDs",
        description="Include body IDs in ParaView output",
        default=True
    )
    output_paraview_tensor_values: BoolProperty(
        name="Include Tensor Values",
        description="Include tensor values in ParaView output",
        default=False
    )
    output_paraview_nodes: BoolProperty(
        name="Include Nodes",
        description="Include nodes in ParaView output",
        default=False
    )
    output_paraview_vismesh_rel_area: FloatProperty(
        name="VisMesh Relative Area",
        description="Relative area for VisMesh in ParaView",
        default=1e7
    )
    output_advanced_save_solve_sequence_debug: BoolProperty(
        name="Save Solve Sequence Debug",
        description="Enable saving of solve sequence debug information",
        default=False
    )
    output_advanced_save_time_sequence: BoolProperty(
        name="Save Time Sequence",
        description="Enable saving of time sequence data",
        default=True
    )
