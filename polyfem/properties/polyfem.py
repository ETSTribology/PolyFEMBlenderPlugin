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
    ("Steel", "Steel", "Density: 8000.0 , Young's Modulus: 200.0e9, Poisson: 0.3"),
    ("Copper", "Copper", "Density: 8940.0 , Young's Modulus: 133.0e9, Poisson: 0.34"),
    ("Aluminum", "Aluminum", "Density: 2700.0 , Young's Modulus: 69.0e9, Poisson: 0.33"),
    ("Brass", "Brass", "Density: 8500.0 , Young's Modulus: 115.0e9, Poisson: 0.34"),
    ("Cadmium", "Cadmium", "Density: 8650.0 , Young's Modulus: 64.0e9, Poisson: 0.31"),
    ("Cast_Iron", "Cast Iron", "Density: 7200.0 , Young's Modulus: 170.0e9, Poisson: 0.25"),
    ("Chromium", "Chromium", "Density: 7190.0 , Young's Modulus: 248.0e9, Poisson: 0.31"),
    ("Glass", "Glass", "Density: 2400.0 , Young's Modulus: 60.0e9, Poisson: 0.25"),
    ("Nickel", "Nickel", "Density: 8900.0 , Young's Modulus: 170.0e9, Poisson: 0.31"),
    ("Rubber", "Rubber", "Density: 1200.0 , Young's Modulus: 0.01e9, Poisson: 0.47"),
    ("Tungsten", "Tungsten", "Density: 19300.0 , Young's Modulus: 400.0e9, Poisson: 0.28"),
    ("Zinc", "Zinc", "Density: 7135.0 , Young's Modulus: 82.7e9, Poisson: 0.25"),
    ("Lead", "Lead", "Density: 11340.0 , Young's Modulus: 16.0e9, Poisson: 0.431"),
    ("Titanium", "Titanium", "Density: 4500.0 , Young's Modulus: 105.0e9, Poisson: 0.3"),
    ("Gold", "Gold", "Density: 19300.0 , Young's Modulus: 78.0e9, Poisson: 0.42"),
    ("Silver", "Silver", "Density: 10500.0 , Young's Modulus: 83.0e9, Poisson: 0.37"),
    ("Aluminum_Bronze", "Aluminum Bronze", "Density: 7700.0 , Young's Modulus: 100.0e9, Poisson: 0.3"),
    ("Stainless_Steel_18_8", "Stainless Steel 18-8", "Density: 8000.0 , Young's Modulus: 193.0e9, Poisson: 0.305"),
    ("Plexiglass", "Plexiglass", "Density: 1190.0 , Young's Modulus: 3.3e9, Poisson: 0.37"),
    ("Wood", "Wood", "Density: 750.0 , Young's Modulus: 10.0e9, Poisson: 0.35"),
    ("Concrete", "Concrete", "Density: 2400.0 , Young's Modulus: 30.0e9, Poisson: 0.17"),
    ("Teflon", "Teflon", "Density: 2200.0 , Young's Modulus: 0.5e9, Poisson: 0.47"),
    ("Leather", "Leather", "Density: 980.0 , Young's Modulus: 4.0e9, Poisson: 0.35"),
    ("Graphite", "Graphite", "Density: 2050.0 , Young's Modulus: 20.0e9, Poisson: 0.2"),
    ("Magnesium", "Magnesium", "Density: 1740.0 , Young's Modulus: 45.0e9, Poisson: 0.35"),
    ("Phosphor_Bronze", "Phosphor Bronze", "Density: 8780.0 , Young's Modulus: 110.0e9, Poisson: 0.33"),
    ("Titanium_Alloy", "Titanium Alloy", "Density: 4500.0 , Young's Modulus: 112.5e9, Poisson: 0.3"),
    ("Silicone_Rubber", "Silicone Rubber", "Density: 1100.0 , Young's Modulus: 0.0018e9, Poisson: 0.47"),
    ("Polyurethane_Foam", "Polyurethane Foam", "Density: 150.0 , Young's Modulus: 0.003e9, Poisson: 0.4"),
    ("Hydrogel", "Hydrogel", "Density: 1050.0 , Young's Modulus: 0.0001e9, Poisson: 0.45"),
    ("PDMS", "PDMS (Polydimethylsiloxane)", "Density: 970.0 , Young's Modulus: 0.002e9, Poisson: 0.5"),
    ("Neoprene_Rubber", "Neoprene Rubber", "Density: 1300.0 , Young's Modulus: 0.01e9, Poisson: 0.48"),
    ("Polyethylene", "Polyethylene (Low-Density)", "Density: 930.0 , Young's Modulus: 0.3e9, Poisson: 0.42"),
    ("Nylon", "Nylon", "Density: 1150.0 , Young's Modulus: 2.4e9, Poisson: 0.4"),
    ("Silicone_Gel", "Silicone Gel", "Density: 1000.0 , Young's Modulus: 0.0002e9, Poisson: 0.48"),
]

# Define properties for the addon with high precision
class PolyFEMSettings(PropertyGroup):
    export_path: StringProperty(
        name="Export Path",
        description="Path to export the JSON file",
        default="physics_export",
        subtype='FILE_PATH'
    ) # type: ignore
    json_filename: StringProperty(
        name="JSON Filename",
        description="Name of the JSON file to export",
        default="export.json",
        subtype='NONE'
    ) # type: ignore
    export_stl: BoolProperty(
        name="Export Mesh Files",
        description="Export each object as a mesh file",
        default=True
    ) # type: ignore
    export_selected_only: BoolProperty(
        name="Export Selected Only",
        description="Export only selected objects",
        default=False
    ) # type: ignore
    export_point_selection: BoolProperty(
        name="Export Point Selections",
        description="Whether to export selected vertices as point selections",
        default=False
    ) # type: ignore

    # Contact Settings
    contact_enabled: BoolProperty(
        name="Enable Contact",
        description="Enable contact in the simulation",
        default=True,
    ) # type: ignore

    contact_dhat: FloatProperty(
        name="dhat",
        description="Barrier activation distance",
        default=0.001,
        precision=6,  # Set precision to 6 decimal places
    ) # type: ignore

    contact_friction_coefficient: FloatProperty(
        name="Friction Coefficient",
        description="Coefficient of friction for contact",
        default=0.0,
        precision=4,  # Set precision to 4 decimal places
    ) # type: ignore

    contact_epsv: FloatProperty(
        name="epsv",
        description="Tangent velocity threshold",
        default=0.001,
        precision=6,  # Set precision to 6 decimal places
    ) # type: ignore

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
    ) # type: ignore

    time_tend: FloatProperty(
        name="End Time",
        description="Simulation end time",
        default=5.0,
        precision=3,  # Set precision to 3 decimal places
    ) # type: ignore

    time_dt: FloatProperty(
        name="Time Step",
        description="Time step size",
        default=0.025,
        precision=6,  # Set precision to 6 decimal places
    ) # type: ignore

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
    ) # type: ignore

    # Boundary Conditions
    boundary_rhs_x: FloatProperty(
        name="RHS X",
        description="Boundary condition RHS X",
        default=0.0,
        precision=4,  # Set precision to 4 decimal places
    ) # type: ignore

    boundary_rhs_y: FloatProperty(
        name="RHS Y",
        description="Boundary condition RHS Y",
        default=9.81,
        precision=4,  # Set precision to 4 decimal places
    ) # type: ignore

    boundary_rhs_z: FloatProperty(
        name="RHS Z",
        description="Boundary condition RHS Z",
        default=0.0,
        precision=4,  # Set precision to 4 decimal places
    ) # type: ignore

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
    ) # type: ignore

    # Material dropdown
    selected_material: EnumProperty(
        name="Material",
        description="Select the material for the simulation",
        items=material_items,
        default="Steel",  # Default to Steel
        update=lambda self, context: self.update_material_properties()  # Automatically update material properties
    ) # type: ignore

    # Material properties (will be auto-filled based on the selected material)
    materials_E: FloatProperty(
        name="Young's Modulus (E)",
        description="Young's Modulus of the material",
        default=210000.0,
        precision=6,  # Set precision to 6 decimal places for Young's modulus
    ) # type: ignore

    materials_nu: FloatProperty(
        name="Poisson's Ratio (nu)",
        description="Poisson's Ratio of the material",
        default=0.3,
        precision=4,  # Set precision to 4 decimal places
    ) # type: ignore

    materials_rho: FloatProperty(
        name="Density (rho)",
        description="Density of the material",
        default=1000.0,
        precision=3,  # Set precision to 3 decimal places for density
    ) # type: ignore

    def update_material_properties(self):
        """Update the material properties based on the selected material."""
        material_data = {
            "Steel": material_items[0][2],
            "Copper": material_items[1][2],
            "Aluminum": material_items[2][2],
            "Brass": material_items[3][2],
            "Cadmium": material_items[4][2],
            "Cast_Iron": material_items[5][2],
            "Chromium": material_items[6][2],
            "Glass": material_items[7][2],
            "Nickel": material_items[8][2],
            "Rubber": material_items[9][2],
            "Tungsten": material_items[10][2],
            "Zinc": material_items[11][2],
            "Lead": material_items[12][2],
            "Titanium": material_items[13][2],
            "Gold": material_items[14][2],
            "Silver": material_items[15][2],
            "Aluminum_Bronze": material_items[16][2],
            "Stainless_Steel_18_8": material_items[17][2],
            "Plexiglass": material_items[18][2],
            "Wood": material_items[19][2],
            "Concrete": material_items[20][2],
            "Teflon": material_items[21][2],
            "Leather": material_items[22][2],
            "Graphite": material_items[23][2],
            "Magnesium": material_items[24][2],
            "Phosphor_Bronze": material_items[25][2],
            "Titanium_Alloy": material_items[26][2],
            "Silicone_Rubber": material_items[27][2],
            "Polyurethane_Foam": material_items[28][2],
            "Hydrogel": material_items[29][2],
            "PDMS": material_items[30][2],
            "Neoprene_Rubber": material_items[31][2],
            "Polyethylene": material_items[32][2],
            "Nylon": material_items[33][2],
            "Silicone_Gel": material_items[34][2],
        }

        material = self.selected_material
        if material in material_data:
            try:
                data_str = material_data[material]
                import re
                density_match = re.search(r"Density:\s*([\d\.eE+-]+)", data_str)
                youngs_match = re.search(r"Young's Modulus:\s*([\d\.eE+-]+)", data_str)
                poisson_match = re.search(r"Poisson:\s*([\d\.eE+-]+)", data_str)

                if density_match and youngs_match and poisson_match:
                    self.materials_rho = float(density_match.group(1))
                    self.materials_E = float(youngs_match.group(1))
                    self.materials_nu = float(poisson_match.group(1))
                else:
                    self.report({'ERROR'}, f"Failed to parse material properties for '{material}'.")
            except Exception as e:
                self.report({'ERROR'}, f"Error updating material properties for '{material}': {e}")

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
    ) # type: ignore

    solver_nonlinear_x_delta: FloatProperty(
        name="Nonlinear x_delta",
        description="Nonlinear solver x_delta parameter",
        default=1e-05,
        precision=6,  # Set precision to 6 decimal places
    ) # type: ignore

    solver_advanced_lump_mass_matrix: BoolProperty(
        name="Lump Mass Matrix",
        description="Use lumped mass matrix",
        default=True,
    ) # type: ignore

    solver_contact_friction_convergence_tol: FloatProperty(
        name="Friction Convergence Tolerance",
        description="Tolerance for friction convergence",
        default=0.01,
        precision=4,  # Set precision to 4 decimal places
    ) # type: ignore

    solver_contact_friction_iterations: IntProperty(
        name="Friction Iterations",
        description="Number of friction iterations",
        default=1,
    ) # type: ignore

    # Output Settings
    output_json: StringProperty(
        name="JSON Output",
        description="Name of the JSON output file",
        default="results.json",
    ) # type: ignore

    output_paraview_file_name: StringProperty(
        name="ParaView Filename",
        description="Name of the ParaView output file",
        default="result.pvd",
    ) # type: ignore

    output_paraview_material: BoolProperty(
        name="Export Material",
        description="Export material data to ParaView",
        default=True,
    ) # type: ignore

    output_paraview_body_ids: BoolProperty(
        name="Export Body IDs",
        description="Export body IDs to ParaView",
        default=True,
    ) # type: ignore

    output_paraview_tensor_values: BoolProperty(
        name="Export Tensor Values",
        description="Export tensor values to ParaView",
        default=True,
    ) # type: ignore

    output_paraview_nodes: BoolProperty(
        name="Export Nodes",
        description="Export nodes to ParaView",
        default=True,
    ) # type: ignore

    output_paraview_vismesh_rel_area: FloatProperty(
        name="VisMesh Relative Area",
        description="Relative area for visualization mesh",
        default=1e-5,
        precision=6,  # Set precision to 6 decimal places
    ) # type: ignore

    output_advanced_save_solve_sequence_debug: BoolProperty(
        name="Save Solve Sequence Debug",
        description="Save debug information for solve sequence",
        default=False,
    ) # type: ignore

    output_advanced_save_time_sequence: BoolProperty(
        name="Save Time Sequence",
        description="Save time sequence data",
        default=False,
    ) # type: ignore

    polyfem_json_input: StringProperty(
        name="PolyFem JSON File",
        description="Path to the JSON file for PolyFem simulation",
        default="",
        subtype='FILE_PATH'
    ) # type: ignore

    show_export_settings: BoolProperty(name="Show Export Settings", description="Show export settings", default=False) # type: ignore

    show_contact_settings: BoolProperty(name="Show Contact Settings", description="Show contact settings", default=False) # type: ignore

    show_time_settings: BoolProperty(name="Show Time Settings", description="Show time settings", default=False) # type: ignore

    show_space_settings: BoolProperty(name="Show Space Settings", description="Show space settings", default=False) # type: ignore

    show_boundary_conditions: BoolProperty(name="Show Boundary Conditions", description="Show boundary conditions", default=False) # type: ignore

    show_materials: BoolProperty(name="Show Materials", description="Show materials", default=False) # type: ignore

    show_solver_settings: BoolProperty(name="Show Solver Settings", description="Show solver settings", default=False) # type: ignore

    show_output_settings: BoolProperty(name="Show Output Settings", description="Show output settings", default=False) # type: ignore

    execution_mode_tetwild: EnumProperty(
        name="Execution Mode TetWild",
        description="Choose between Docker or a local executable for running TetWild",
        items=[
            ('DOCKER', "Docker", "Use Docker for running TetWild"),
            ('EXECUTABLE', "Executable", "Use a local executable for running TetWild")
        ],
        default='DOCKER'
    ) # type: ignore

    executable_path_tetwild: StringProperty(
        name="Executable Path TetWild",
        description="Path to the TetWild executable",
        subtype='FILE_PATH'
    ) # type: ignore

    docker_image_tetwild: StringProperty(
        name="Docker Image TetWild",
        description="Docker image for running TetWild",
        default="yixinhu/tetwild:latest"
    ) # type: ignore

    execution_mode_polyfem: EnumProperty(
        name="Execution Mode PolyFem",
        description="Choose between Docker or a local executable for running PolyFEM",
        items=[
            ('DOCKER', "Docker", "Use Docker for running PolyFEM"),
            ('EXECUTABLE', "Executable", "Use a local executable for running PolyFEM")
        ],
        default='DOCKER'
    ) # type: ignore

    executable_path_polyfem: StringProperty(
        name="Executable Path PolyFem",
        description="Path to the PolyFem executable",
        subtype='FILE_PATH'
    ) # type: ignore

    docker_image_polyfem: StringProperty(
        name="Docker Image PolyFem",
        description="Docker image for running PolyFEM",
        default="antoinebou12/polyfem:cuda-latest"
    ) # type: ignore

    show_polyfem_execution_mode: BoolProperty(name="Show PolyFEM Execution Mode", default=True) # type: ignore
    show_tetwild_execution_mode: BoolProperty(name="Show TetWild Execution Mode", default=True) # type: ignore


     # TetWild Parameters
    tetwild_max_tets: IntProperty(
        name="Max Tetrahedrons",
        description="Maximum number of tetrahedrons in the mesh",
        default=4,
        min=4,
        max=100,
    )  # type: ignore

    tetwild_min_tets: IntProperty(
        name="Min Tetrahedrons",
        description="Minimum number of tetrahedrons in the mesh",
        default=80,
        min=80,
        max=1000,
    )  # type: ignore

    tetwild_mesh_quality: FloatProperty(
        name="Mesh Quality",
        description="Quality threshold for mesh generation",
        default=0.9,
        min=0.1,
        max=1.0,
        precision=3,
    )  # type: ignore

    docker_image: bpy.props.StringProperty(name="Docker Image", default="yixinhu/tetwild") # type: ignore

class PolyFEMObjectProperties(bpy.types.PropertyGroup):
    collapse: BoolProperty(
        name="Collapse",
        default=False
    )  # type: ignore

    export_type: EnumProperty(
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
    ) # type: ignore
    is_obstacle: BoolProperty(
        name="Obstacle",
        default=False
    )  # type: ignore