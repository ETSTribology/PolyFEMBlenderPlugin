# Blender Plugin Simulation to JSON

This is the experimental blender exporter for ETS Lab.
This plugin have been only tested for Blender 4.2.

## Installation
The main steps for installing this plugin:
1) Zip the directory `physics_export` inside this directory
2) Open Blender and go to: `Edit > Preferences > Add-ons` and click on the install button. 
3) Select the zip file created in the first step. 
4) Activate the plugin


# File Structure 
```
├── physics_export/
│   ├── __init__.py
│   ├── auto_load.py
│   ├── export/
│   │   ├── export_physics_constraints.py
│   │   ├── physics_exporter.py
│   ├── panels/
│   │   ├── physics_panel.py
│   ├── utils/
│   │   ├── utils.py

```

## Issues
- If the output directory is not specify, the export button crash.

## TODOs
- Export Simulation and Mesh 
- STL and MSH support export
- RUN PolyFem and VTP Simulation in Blender
