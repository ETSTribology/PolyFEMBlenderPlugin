import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    IntProperty
)
from bpy.types import PropertyGroup

# Material data for the dropdown
material_items = [
    ("Steel", "Steel", "Density: 8000.0 kg/m³, Young's Modulus: 200.0 GPa, Poisson: 0.3"),
    ("Copper", "Copper", "Density: 8940.0 kg/m³, Young's Modulus: 133.0 GPa, Poisson: 0.34"),
    ("Aluminum", "Aluminum", "Density: 2700.0 kg/m³, Young's Modulus: 69.0 GPa, Poisson: 0.33"),
    ("Brass", "Brass", "Density: 8500.0 kg/m³, Young's Modulus: 115.0 GPa, Poisson: 0.34"),
    ("Cadmium", "Cadmium", "Density: 8650.0 kg/m³, Young's Modulus: 64.0 GPa, Poisson: 0.31"),
    ("Cast_Iron", "Cast Iron", "Density: 7200.0 kg/m³, Young's Modulus: 170.0 GPa, Poisson: 0.25"),
    ("Chromium", "Chromium", "Density: 7190.0 kg/m³, Young's Modulus: 248.0 GPa, Poisson: 0.31"),
    ("Glass", "Glass", "Density: 2400.0 kg/m³, Young's Modulus: 60.0 GPa, Poisson: 0.25"),
    ("Nickel", "Nickel", "Density: 8900.0 kg/m³, Young's Modulus: 170.0 GPa, Poisson: 0.31"),
    ("Rubber", "Rubber", "Density: 1200.0 kg/m³, Young's Modulus: 0.01 GPa, Poisson: 0.47"),
    ("Tungsten", "Tungsten", "Density: 19300.0 kg/m³, Young's Modulus: 400.0 GPa, Poisson: 0.28"),
    ("Zinc", "Zinc", "Density: 7135.0 kg/m³, Young's Modulus: 82.7 GPa, Poisson: 0.25"),
    ("Lead", "Lead", "Density: 11340.0 kg/m³, Young's Modulus: 16.0 GPa, Poisson: 0.431"),
    ("Titanium", "Titanium", "Density: 4500.0 kg/m³, Young's Modulus: 105.0 GPa, Poisson: 0.3"),
    ("Gold", "Gold", "Density: 19300.0 kg/m³, Young's Modulus: 78.0 GPa, Poisson: 0.42"),
    ("Silver", "Silver", "Density: 10500.0 kg/m³, Young's Modulus: 83.0 GPa, Poisson: 0.37"),
    ("Aluminum_Bronze", "Aluminum Bronze", "Density: 7700.0 kg/m³, Young's Modulus: 100.0 GPa, Poisson: 0.3"),
    ("Stainless_Steel_18_8", "Stainless Steel 18-8", "Density: 8000.0 kg/m³, Young's Modulus: 193.0 GPa, Poisson: 0.305"),
    ("Plexiglass", "Plexiglass", "Density: 1190.0 kg/m³, Young's Modulus: 3.3 GPa, Poisson: 0.37"),
    ("Wood", "Wood", "Density: 750.0 kg/m³, Young's Modulus: 10.0 GPa, Poisson: 0.35"),
    ("Concrete", "Concrete", "Density: 2400.0 kg/m³, Young's Modulus: 30.0 GPa, Poisson: 0.17"),
    ("Teflon", "Teflon", "Density: 2200.0 kg/m³, Young's Modulus: 0.5 GPa, Poisson: 0.47"),
    ("Leather", "Leather", "Density: 980.0 kg/m³, Young's Modulus: 4.0 GPa, Poisson: 0.35"),
    ("Graphite", "Graphite", "Density: 2050.0 kg/m³, Young's Modulus: 20.0 GPa, Poisson: 0.2"),
    ("Magnesium", "Magnesium", "Density: 1740.0 kg/m³, Young's Modulus: 45.0 GPa, Poisson: 0.35"),
    ("Phosphor_Bronze", "Phosphor Bronze", "Density: 8780.0 kg/m³, Young's Modulus: 110.0 GPa, Poisson: 0.33"),
    ("Titanium_Alloy", "Titanium Alloy", "Density: 4500.0 kg/m³, Young's Modulus: 112.5 GPa, Poisson: 0.3"),
]

# Define properties for the addon
class PolyFEMSettings(PropertyGroup):
    export_path: StringProperty(
        name="Export Path",
        description="Path to export the JSON file",
        default="//physics_export.json",
        subtype='FILE_PATH'
    )
    json_filename: StringProperty(
        name="JSON Filename",
        description="Name of the JSON file to export",
        default="export.json",
        subtype='NONE'
    )
    export_stl: BoolProperty(
        name="Export Mesh Files",
        description="Export each object as a mesh file",
        default=True
    )
    export_format: EnumProperty(
        name="Export Format",
        description="Choose the mesh export format",
        items=[
            ('STL', "STL (.stl)", "Export as STL"),
            ('OBJ', "OBJ (.obj)", "Export as OBJ"),
            ('FBX', "FBX (.fbx)", "Export as FBX"),
            ('GLTF', "GLTF (.gltf)", "Export as GLTF"),
            ('MSH', "MSH (.msh)", "Export as MSH using TetWild"),
        ],
        default='STL',
    )
    export_selected_only: BoolProperty(
        name="Export Selected Only",
        description="Export only selected objects",
        default=False
    )
    export_point_selection: BoolProperty(
        name="Export Point Selections",
        description="Whether to export selected vertices as point selections",
        default=False
    )

    # Contact Settings
    contact_enabled: BoolProperty(
        name="Enable Contact",
        description="Enable contact in the simulation",
        default=True,
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
        default=5.0,
    )

    time_dt: FloatProperty(
        name="Time Step",
        description="Time step size",
        default=0.025,
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
        default=9.81,
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
        default="NeoHookean",
    )

    # Material dropdown
    selected_material: EnumProperty(
        name="Material",
        description="Select the material for the simulation",
        items=material_items,
        default="Steel",  # Default to Steel
        update=lambda self, context: self.update_material_properties()  # Automatically update material properties
    )

    # Material properties (will be auto-filled based on the selected material)
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

    def update_material_properties(self):
        """Update the material properties based on the selected material."""
        material_data = {
            "Steel": (200.0, 0.3, 8000.0),
            "Copper": (133.0, 0.34, 8940.0),
            "Aluminum": (69.0, 0.33, 2700.0),
            "Brass": (115.0, 0.34, 8500.0),
            "Cadmium": (64.0, 0.31, 8650.0),
            "Cast_Iron": (170.0, 0.25, 7200.0),
            "Chromium": (248.0, 0.31, 7190.0),
            "Glass": (60.0, 0.25, 2400.0),
            "Nickel": (170.0, 0.31, 8900.0),
            "Rubber": (0.01, 0.47, 1200.0),
            "Tungsten": (400.0, 0.28, 19300.0),
            "Zinc": (82.7, 0.25, 7135.0),
            "Lead": (16.0, 0.431, 11340.0),
            "Titanium": (105.0, 0.3, 4500.0),
            "Gold": (78.0, 0.42, 19300.0),
            "Silver": (83.0, 0.37, 10500.0),
            "Aluminum_Bronze": (100.0, 0.3, 7700.0),
            "Stainless_Steel_18_8": (193.0, 0.305, 8000.0),
            "Plexiglass": (3.3, 0.37, 1190.0),
            "Wood": (10.0, 0.35, 750.0),
            "Concrete": (30.0, 0.17, 2400.0),
            "Teflon": (0.5, 0.47, 2200.0),
            "Leather": (4.0, 0.35, 980.0),
            "Graphite": (20.0, 0.2, 2050.0),
            "Magnesium": (45.0, 0.35, 1740.0),
            "Phosphor_Bronze": (110.0, 0.33, 8780.0),
            "Titanium_Alloy": (112.5, 0.3, 4500.0),
        }

        material = self.selected_material
        if material in material_data:
            E, nu, rho = material_data[material]
            self.materials_E = E
            self.materials_nu = nu
            self.materials_rho = rho

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
        default="Eigen::PardisoLDLT",
    )

    solver_nonlinear_x_delta: FloatProperty(
        name="Nonlinear x_delta",
        description="Nonlinear solver x_delta parameter",
        default=1e-05,
    )

    solver_advanced_lump_mass_matrix: BoolProperty(
        name="Lump Mass Matrix",
        description="Use lumped mass matrix",
        default=True,
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
        default=False,
    )

    polyfem_json_input: StringProperty(
        name="PolyFem JSON File",
        description="Path to the JSON file for PolyFem simulation",
        default="",
        subtype='FILE_PATH'
    ) # type: ignore # noqa: F821

    # Directory for project (VTU and OBJ files will be inside this directory)
    project_path: StringProperty(
        name="Project Path",
        description="Directory for saving VTU and OBJ files",
        default="",
        subtype='DIR_PATH'
    ) # type: ignore # noqa: F821
