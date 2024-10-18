# Blender Plugin Simulation to JSON

This is an experimental Blender add-on developed for **ETS Lab**. It allows users to extract objects and their physics constraints from Blender and export them to JSON format, as well as run **PolyFem** simulations directly from Blender. 

> **Note**: This plugin has been tested with Blender **4.2** and may not be compatible with earlier versions.

## Features

- Export objects and their physics constraints to **JSON**.
- Supports exporting meshes in **STL** and **MSH** formats.
- Directly run **PolyFem** simulations from Blender.
- Apply **heightmaps** to selected mesh faces.
- Easy-to-use UI integrated into Blender's sidebar.

## Table of Contents

1. [Installation](#installation)
2. [File Structure](#file-structure)
3. [Usage](#usage)
    - [Enabling the Add-on](#enabling-the-add-on)
    - [Running Simulations](#running-simulations)
    - [Exporting Physics](#exporting-physics)
4. [Known Issues](#known-issues)
5. [Roadmap](#roadmap)
6. [Contributing](#contributing)
7. [License](#license)

---

## Installation

To install the Blender Plugin Simulation to JSON, follow these steps:

1. **Zip the `physics_export` directory**:
   - Navigate to the plugin directory and zip the entire `physics_export` folder. This folder contains the core files required for the plugin to function.

2. **Install the plugin in Blender**:
   - Open Blender.
   - Go to **Edit > Preferences > Add-ons**.
   - Click on the **Install** button and select the zip file you created in the previous step.

3. **Activate the plugin**:
   - After installation, search for `BlenderPluginSimulation` in the add-on preferences and activate it by clicking the checkbox.

---

## File Structure

```
physics_export/
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

## Contributing

We welcome contributions to improve the add-on. If you want to contribute:

1. Fork the repository.
2. Create a new branch (`feature/your-feature` or `fix/your-fix`).
3. Submit a pull request with a detailed explanation of the changes.

---

## License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](./LICENSE) file for more details.

---

## Resources

- [Blender Add-on Development Tutorial](https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html)
- [Blender Extensions](https://docs.blender.org/manual/en/latest/advanced/extensions/index.html)
- [Getting Started with Add-ons](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html)

---

### Authors

- **Antoine Boucher** - Lead Developer and Maintainer
- ETS Lab

For any questions or issues, feel free to reach out or submit an issue on the [GitHub Repository](https://github.com/ETSTribology/BlenderPluginSimulation).