import os
import subprocess
import sys

packages = {
    'numpy': '1.26.0',
    'scipy': '1.14.1',
    'noise': '1.2.2',
    'meshio': '5.3.5',
    'trimesh': '4.4.9',
    'tetgen': '0.6.5'
}

script_dir = os.path.dirname(os.path.abspath(__file__))

wheels_dir = os.path.join(script_dir, 'physics_export/wheels')

if not os.path.exists(wheels_dir):
    os.makedirs(wheels_dir)

for package_name, package_version in packages.items():
    # Construct the pip download command
    command = [
        'python', '-m', 'pip', 'download',
        '--only-binary=:all:',
        '-d', wheels_dir,
        f"{package_name}=={package_version}"
    ]
    print(f"Downloading {package_name}=={package_version}")
    print(' '.join(command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download {package_name}: {e}")

print("Done downloading wheels.")
