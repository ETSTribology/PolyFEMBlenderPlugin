# Blender Plugin for PolyFEM

![image](https://github.com/user-attachments/assets/919ffa16-039b-4a6d-822e-faf9c207ad67)


[![Blender](https://img.shields.io/badge/Blender-4.20%2B-orange)](https://www.blender.org/)
[![Release](https://img.shields.io/github/v/release/ETSTribology/BlenderPluginSimulation)](https://github.com/ETSTribology/BlenderPluginSimulation/releases)
[![License](https://img.shields.io/github/license/ETSTribology/BlenderPluginSimulation)](./LICENSE)
[![PolyFem](https://img.shields.io/badge/PolyFem-Compatible-blue)](https://polyfem.github.io/)

This is an experimental Blender add-on developed for **ETS Lab**. It allows users to extract objects and their physics constraints from Blender and export them to JSON format, as well as run **PolyFem** simulations directly from Blender.

> **Note**: This plugin has been tested with Blender **4.2** and may not be compatible with earlier versions.

## Features

- Export objects and their physics constraints to **JSON**.
- Supports exporting meshes in **STL** and **MSH** formats.
- Directly run **PolyFem** simulations from Blender.
- Apply **heightmaps** to selected mesh faces.
- Easy-to-use UI integrated into Blender's sidebar.

![image](https://github.com/user-attachments/assets/53fcc6f8-7211-423a-a67c-a0d715b88822)
![image](https://github.com/user-attachments/assets/6e921f95-2748-4e83-a295-2abc3285f68c)

## Table of Contents
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [File Structure](#file-structure)
4. [Usage](#usage)
    - [Enabling the Add-on](#enabling-the-add-on)
    - [Running Simulations](#running-simulations)
    - [Exporting Physics](#exporting-physics)
5. [Known Issues](#known-issues)
6. [Roadmap](#roadmap)

---

## Requirements

In addition to Python dependencies, this plugin requires **Docker Desktop** for running `TetWild` and `PolyFem` simulations. Ensure that **Docker Desktop** is installed and running on your system.

### Docker Images:

- **TetWild**: Used for mesh generation and refinement.
  - Image: `yixinhu/tetwild:latest`
  
- **PolyFem**: Used for running simulations.
  - Image: `antoinebou12/polyfem:latest`

### Steps to Install Docker and Pull Required Images:

1. **Install Docker Desktop**:
   - Download and install Docker Desktop from [here](https://www.docker.com/products/docker-desktop/).
   - Make sure Docker is running and has access to your local file system.

2. **Pull Docker Images**:
   - Open a terminal and run the following commands to pull the required Docker images:
     ```bash
     docker pull yixinhu/tetwild:latest
     docker pull antoinebou12/polyfem:latest
     ```

3. **Verify Docker Setup**:
   - Ensure that Docker is working correctly by running:
     ```bash
     docker --version
     ```

---

### Python Dependencies

The following Python packages are required for this plugin:

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

Ensure you have Python 3.11 installed. These dependencies are automatically managed within the plugin, but if you are developing or modifying the plugin, you may need to install them manually using `pip`.

---

## Installation

To install the Blender Plugin Simulation to JSON, follow these steps:
https://etstribology.github.io/PolyFEMBlenderPlugin/index.html
![image](https://github.com/user-attachments/assets/fc10fb97-5daf-4a34-ad36-999d82311a2e)
![image](https://github.com/user-attachments/assets/05305448-2c0d-4cbb-8d54-e1ad906be1d7)

1. **Zip the `polyfem` directory**:
   - Navigate to the plugin directory and zip the entire `polyfem` folder. This folder contains the core files required for the plugin to function.

2. **Install the plugin in Blender**:
   - Open Blender.
   - Go to **Edit > Preferences > Add-ons**.
   - Click on the **Install** button and select the zip file you created in the previous step.


3. **Activate the plugin**:
   - After installation, search for `PolyFEM` in the add-on preferences and activate it by clicking the checkbox.

## File Structure

```
polyfem/
├── __init__.py                            # Main entry point for the plugin
├── export/
│   ├── physics_exporter.py                # Handles exporting objects and physics constraints
├── operators/
│   ├── heightmap.py              # Applies heightmaps to mesh faces
│   ├── run_polyfem.py            # Runs PolyFem simulations
│   ├── open_docs.py              # Opens PolyFem documentation in a browser
├── panels/
│   ├── heightmap.py                 # UI panel for heightmap generator
│   ├── poly_fem.py                  # UI panel for PolyFem simulation
│   ├── physics.py                   # UI panel for exporting physics data
├── properties/
│   ├── export.py               # Stores export-related settings
│   ├── heightmap.py            # Stores heightmap settings
│   ├── polyfem.py                # Stores PolyFem simulation settings
│   ├── physics_export_addon.py # Stores add-on preferences
```

---

## Usage

### Enabling the Add-on

Once the add-on is installed and activated, you will find a new sidebar panel in Blender's **3D Viewport** under the categories:

- **Physics**: For exporting physics constraints and mesh data.
- **PolyFem**: For configuring and running PolyFem simulations.
- **Heightmap**: For applying heightmaps to selected mesh faces.

To view these panels:
- Press `N` to open the sidebar.
- Navigate to the relevant tab (Physics, PolyFem, or Heightmap).

### Running Simulations

1. **Configure PolyFem Executable**:
   - In the **PolyFem** panel, set the path to the **PolyFem executable** and provide a valid **JSON configuration** for the simulation.
   
2. **Set Project Path**:
   - Choose a project path where simulation output (e.g., meshes and JSON files) will be saved.

3. **Run Simulation**:
   - Click the **Run PolyFem Simulation** button to start the simulation.
   - You can also open the **PolyFem documentation** by clicking the corresponding button in the panel.

### Exporting Physics

1. **Set Export Options**:
   - In the **Physics** panel, set the output directory, JSON filename, and choose the desired export format (STL, MSH).

2. **Select Objects** (Optional):
   - If you want to export only specific objects, select them in the viewport and enable **Export Selected Only**.

3. **Export to JSON**:
   - Click **Export Physics to JSON** to generate a JSON file containing the object's physics constraints and other properties.

---

## Known Issues

- **Output Directory**: If the output directory is not specified, the **Export Physics to JSON** button may crash Blender. Ensure the output directory is set before exporting.

---

## Roadmap

### Upcoming Features:
- **Simulation Export**: Full support for exporting both simulations and meshes.
- **STL and MSH Export**: Enhanced export options for STL and MSH formats.
- **Integrated PolyFem and VTP Simulation**: Directly run PolyFem and VTP simulations within Blender.

---

## Resources

- [Blender Add-on Development Tutorial](https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html)
- [Blender Extensions](https://docs.blender.org/manual/en/latest/advanced/extensions/index.html)
- [Getting Started with Add-ons](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html)
- [PolyFem GitHub Repository](https://github.com/polyfem/polyfem)

---

### Authors

- **Antoine Boucher** - Lead Developer and Maintainer
- ETS Lab

For any questions or issues, feel free to reach out or submit an issue on the [GitHub Repository](https://github.com/ETSTribology/BlenderPluginSimulation).
