import os
import subprocess
import sys

packages = {
    'numpy': '2.1.2',
    'scipy': '1.14.1',
    'noise': '1.2.1',
    'meshio': '5.3.5',
    'trimesh': '4.5.0',
    'tetgen': '0.6.5',
    'rich': '13.9.2',
}

script_dir = os.path.dirname(os.path.abspath(__file__))
wheels_dir = os.path.join(script_dir, 'physics_export/wheels')

if not os.path.exists(wheels_dir):
    os.makedirs(wheels_dir)

for package_name, package_version in packages.items():
    # Construct the pip download command
    command = [
        sys.executable, '-m', 'pip', 'download',
        '--only-binary=:all:',
        '-d', wheels_dir,
        f"{package_name}=={package_version}"
    ]
    print(f"Downloading {package_name}=={package_version}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download {package_name}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while downloading {package_name}: {e}")

print("Done downloading wheels.")
