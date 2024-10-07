import os
import subprocess
import sys
import shutil

def find_blender_executable():
    """
    Attempts to find the Blender executable.
    Modify this function if Blender is installed in a non-standard location.
    """
    blender_executable = None

    # Try to find Blender in common install locations
    if sys.platform == 'win32':
        # Windows
        possible_paths = [
            r"C:\Program Files\Blender Foundation\Blender\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        ]
    elif sys.platform == 'darwin':
        # macOS
        possible_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/Applications/Blender 4.2.app/Contents/MacOS/Blender",
        ]
    else:
        # Linux
        possible_paths = [
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "/snap/bin/blender",
        ]

    for path in possible_paths:
        if os.path.exists(path):
            blender_executable = path
            break

    if blender_executable is None:
        # Try to find Blender in PATH
        blender_executable = shutil.which("blender")

    if blender_executable is None:
        print("Could not find Blender executable. Please specify the path manually.")
        blender_executable = input("Enter the full path to the Blender executable: ").strip()

    if not os.path.exists(blender_executable):
        raise FileNotFoundError(f"Blender executable not found at {blender_executable}")

    return blender_executable

def validate_manifest(blender_executable, manifest_path):
    """
    Validates the blender_manifest.toml file using Blender's command-line tool.
    """
    print("Validating the manifest...")
    command = [
        blender_executable,
        "--background",
        "--python-expr",
        f"import bpy; bpy.ops.preferences.extension_validate(filepath=r'{manifest_path}')"
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("Manifest validation successful.")
    except subprocess.CalledProcessError as e:
        print("Manifest validation failed.")
        print(e.stderr)
        sys.exit(1)

def build_addon(blender_executable, addon_directory):
    """
    Builds the add-on package into a .zip file using Blender's command-line tool.
    """
    output_zip = os.path.join(addon_directory, 'physics_export.zip')
    print("Building the add-on package...")
    command = [
        blender_executable,
        "--background",
        "--python-expr",
        f"import bpy; bpy.ops.preferences.extension_build(directory=r'{addon_directory}', filepath=r'{output_zip}')"
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("Add-on package built successfully.")
    except subprocess.CalledProcessError as e:
        print("Add-on package build failed.")
        print(e.stderr)
        sys.exit(1)

def main():
    # Get the script's directory (assuming it's in the add-on's root directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Paths to the manifest and add-on directory
    manifest_path = os.path.join(script_dir, 'blender_manifest.toml')
    addon_directory = script_dir

    # Find Blender executable
    blender_executable = find_blender_executable()

    # Validate the manifest
    validate_manifest(blender_executable, manifest_path)

    # Build the add-on package
    build_addon(blender_executable, addon_directory)

if __name__ == "__main__":
    main()
