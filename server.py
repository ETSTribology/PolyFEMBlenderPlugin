import os
import subprocess
import sys
import shutil

def find_blender_executable():
    # Modify this function to return the path to your Blender executable
    blender_executable = None

    if sys.platform == 'win32':
        blender_executable = r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
    elif sys.platform == 'darwin':
        blender_executable = "/Applications/Blender.app/Contents/MacOS/Blender"
    else:
        blender_executable = shutil.which("blender")

    if not blender_executable or not os.path.exists(blender_executable):
        raise FileNotFoundError("Blender executable not found. Please update the path in the script.")

    return blender_executable

def generate_repository(blender_executable, repo_dir, generate_html=False):
    print("Generating repository index...")
    # Construct the Python expression to execute
    python_expr = f"import bpy; bpy.ops.preferences.extension_server_generate(repo_dir=r'{repo_dir}', html={'True' if generate_html else 'False'})"
    command = [
        blender_executable,
        "--background",
        "--python-expr",
        python_expr
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("Repository index generated successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to generate repository index.")
        print(e.stderr)
        sys.exit(1)

def main():
    # Set the path to your packages directory
    repo_dir = os.path.join(os.path.dirname(__file__), "physics_export", "packages repository")
    # Set to True if you want to generate the HTML listing
    generate_html = True

    blender_executable = find_blender_executable()
    generate_repository(blender_executable, repo_dir, generate_html=generate_html)

if __name__ == "__main__":
    main()
