import os
import subprocess
import sys
import shlex  # Added for safer command construction

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
wheels_dir = os.path.join(script_dir, 'polyfem/wheels')

# Ensure the wheels directory exists
if not os.path.exists(wheels_dir):
    os.makedirs(wheels_dir)

# Validate package names and versions (optional, but recommended)
def is_valid_package_name(name):
    return all(c.isalnum() or c in ('_', '-') for c in name)

for package_name, package_version in packages.items():
    if not is_valid_package_name(package_name):
        print(f"Invalid package name: {package_name}")
        continue

    # Construct the pip download command securely using shlex
    command = [
        sys.executable, '-m', 'pip', 'download',
        '--only-binary=:all:',
        '--python-version=3.11',
        '--platform=win_amd64',
        '-d', wheels_dir,
        shlex.quote(f"{package_name}=={package_version}")  # Safer quoting
    ]

    print(f"Downloading {package_name}=={package_version}")

    try:
        # Safely run the command
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download {package_name}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while downloading {package_name}: {e}")

print("Done downloading wheels.")
