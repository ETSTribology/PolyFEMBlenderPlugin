# Blender Plugin Simulation to JSON

[![Blender](https://img.shields.io/badge/Blender-4.20%2B-orange)](https://www.blender.org/)
[![Release](https://img.shields.io/github/v/release/ETSTribology/BlenderPluginSimulation)](https://github.com/ETSTribology/BlenderPluginSimulation/releases)
[![License](https://img.shields.io/github/license/ETSTribology/BlenderPluginSimulation)](./LICENSE)
[![PolyFem](https://img.shields.io/badge/PolyFem-Compatible-blue)](https://polyfem.github.io/)

This experimental Blender add-on, developed by **ETS Lab**, allows users to extract objects and their physics constraints from Blender and export them to JSON format. It also enables users to run **PolyFem** simulations directly within Blender.

> **Note**: This plugin is tested with Blender **4.2**. Compatibility with earlier versions is not guaranteed.

## Features

- Export objects and physics constraints to **JSON**.
- Supports mesh export in **STL** and **MSH** formats.
- Execute **PolyFem** simulations directly in Blender.
- Intuitive user interface integrated into Blender's sidebar.

## Table of Contents

1. [Installation](#installation)
2. [Requirements](#requirements)
3. [File Structure](#file-structure)
4. [Usage](#usage)
    - [Enabling the Add-on](#enabling-the-add-on)
    - [Running Simulations](#running-simulations)
    - [Exporting Physics](#exporting-physics)
5. [Known Issues](#known-issues)
6. [Roadmap](#roadmap)
7. [Contributing](#contributing)
8. [License](#license)

---

## Installation

To install the Blender Plugin Simulation to JSON:

1. **Prepare the Plugin**:
    - Zip the entire `polyfem` directory, which contains the plugin's core files.

2. **Install the Plugin**:
    - Open Blender and go to **Edit > Preferences > Add-ons**.
    - Click **Install** and select the zip file created in step 1.

3. **Activate the Plugin**:
    - Search for `PolyFEM` in the add-on preferences and activate it by checking the corresponding checkbox.

---

## Requirements

In addition to Python dependencies, this plugin requires **Docker Desktop** for running `TetWild` and `PolyFem` simulations. Ensure that **Docker Desktop** is installed and running on your system.

### Python Packages

The following Python packages are required:

```plaintext
tetgen==0.6.5
scipy==1.14.1
meshio==5.3.5
sympy==1.13.3
numpy==2.1.2
trimesh==4.4.9
noise==1.2.2
rich==13.9.1
```

Ensure Python 3.11 is installed. While the plugin manages dependencies automatically, developers may need to install these manually using `pip` if modifying the plugin.

### Docker Images

In addition to the Python dependencies, this plugin relies on Docker for running external simulations:

- **TetWild**: Used for mesh generation and refinement.
  - Docker Image: `yixinhu/tetwild:latest`

- **PolyFem**: Used for running simulations.
  - Docker Image: `antoinebou12/polyfem:latest`

### Steps to Install Docker and Pull Required Images

1. **Install Docker Desktop**:
   - Download and install Docker Desktop from [here](https://www.docker.com/products/docker-desktop/).
   - Ensure Docker is running and configured to access your local file system.

2. **Pull Docker Images**:
   - Open a terminal and run the following commands to pull the required Docker images:
     ```bash
     docker pull yixinhu/tetwild:latest
     docker pull antoinebou12/polyfem:latest
     ```

3. **Verify Docker Setup**:
   - Ensure Docker is working correctly by running:
     ```bash
     docker --version
     ```

---

## File Structure

```
polyfem/
├── __init__.py                 # Main plugin entry point
├── operators/
├── panels/
│   ├── poly_fem.py             # UI panel for PolyFem simulation
├── properties/
│   ├── polyfem.py              # Stores simulation settings
│   ├── physics_export_addon.py  # Stores add-on preferences
```

---

## Usage

### Enabling the Add-on

Once installed and activated, the add-on creates a new sidebar panel in Blender's **3D Viewport**:

- **Physics**: For exporting physics constraints and mesh data.
- **PolyFem**: For setting up and running PolyFem simulations.

To access these panels:

- Press `N` to open the sidebar.
- Navigate to the relevant tab (e.g., **PolyFem**).

### Running Simulations

1. **Configure the PolyFem Executable**:
   - In the **PolyFem** panel, set the path to the **PolyFem executable** and select a valid **JSON configuration** file for the simulation.

2. **Set Project Path**:
   - Choose the path where the simulation output (meshes, JSON files) will be saved.

3. **Start Simulation**:
   - Press **Run PolyFem Simulation** to start the simulation.
   - Optionally, you can open the **PolyFem documentation** from the panel.

### Exporting Physics

1. **Configure Export Options**:
   - In the **PolyFem** panel, set the output directory, JSON filename, and choose between **STL** or **MSH** formats for mesh export.

2. **Select Objects** (Optional):
   - To export specific objects, select them in the 3D Viewport and enable **Export Selected Only**.

3. **Export to JSON**:
   - Click **Create PolyFEM JSON** to generate a JSON file with the object's physics constraints and properties.

---

## Known Issues

- Some edge cases with mesh exporting may not be fully supported.
- PolyFem simulation crashes may occur with complex geometry or specific settings.

---

## Roadmap

### Future Features

- **Simulation Export**: Support for exporting simulations and meshes.
- **STL and MSH Export**: Enhanced functionality for mesh formats.
- **Integrated PolyFem and VTP Simulation**: In-Blender support for PolyFem and VTP simulations.

---

## License

This project is licensed under the **GNU General Public License v3.0**. For more details, check the [LICENSE](./LICENSE) file.

---

## Resources

- [Blender Add-on Development Tutorial](https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html)
- [Blender Extensions](https://docs.blender.org/manual/en/latest/advanced/extensions/index.html)
- [PolyFem GitHub Repository](https://github.com/polyfem/polyfem)

---

### Authors

- **Antoine Boucher** - Lead Developer and Maintainer
- **ETS Lab** - [ETS Lab Homepage](https://www.etsmtl.ca/en/research/chairs-and-labs/lab-multimedia)

For any inquiries, submit an issue on the [GitHub Repository](https://github.com/ETSTribology/BlenderPluginSimulation).
