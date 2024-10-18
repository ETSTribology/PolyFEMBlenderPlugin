import bpy
import os
import subprocess

import bpy
import os
import subprocess
import webbrowser

class RunPolyFemSimulationOperator(bpy.types.Operator):
    """Run PolyFem simulation using the provided executable and JSON configuration"""
    bl_idname = "polyfem.run_simulation"
    bl_label = "Run PolyFem Simulation"

    def execute(self, context):
        settings = context.scene.polyfem_settings
        polyfem_executable = settings.polyfem_executable_path
        polyfem_json = settings.polyfem_json_input
        project_path = bpy.path.abspath(settings.project_path)

        # Check if the PolyFem executable exists
        if not os.path.isfile(polyfem_executable):
            self.report({'ERROR'}, "PolyFem executable not found. Please provide a valid path.")
            return {'CANCELLED'}

        # Ensure the project path exists
        if not os.path.exists(project_path):
            os.makedirs(project_path)

        # Write the JSON input to a file in the project directory
        temp_json_path = os.path.join(project_path, "polyfem_config.json")
        try:
            with open(temp_json_path, "w") as json_file:
                json_file.write(polyfem_json)

            # Run PolyFem with the JSON file
            result = subprocess.run([polyfem_executable, "--json", temp_json_path], capture_output=True, text=True)

            if result.returncode != 0:
                self.report({'ERROR'}, f"PolyFem failed: {result.stderr}")
                return {'CANCELLED'}

            self.report({'INFO'}, f"PolyFem simulation ran successfully! Config file: {temp_json_path}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to run PolyFem: {e}")
            return {'CANCELLED'}

class OpenPolyFemDocsOperator(bpy.types.Operator):
    """Open PolyFem documentation in a browser"""
    bl_idname = "polyfem.open_docs"
    bl_label = "Open PolyFem Documentation"
    bl_description = "Open PolyFem documentation in the default web browser"

    def execute(self, context):
        doc_url = "https://polyfem.github.io/json_defaults_and_spec/?h=json+s"
        webbrowser.open(doc_url)
        return {'FINISHED'}