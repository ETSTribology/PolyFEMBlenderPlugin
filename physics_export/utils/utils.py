import importlib
import importlib.util
import os
import sys
import typing
import subprocess
import traceback
import textwrap
import json
import inspect

import bpy

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
PYTHON_BINARY = sys.executable if bpy.app.version >= (2, 91, 0) else bpy.app.binary_path_python
BLENDER_EXECUTABLE = bpy.app.binary_path

STATUS_DLL_NOT_FOUND = 3221225781
""" The WindowsApps' rights restriction affects DLLs discovery in PATH """

def pip_fallback(modules_to_install: typing.List[str], directory: str) -> int:
    """
    A fallback to install packages using Blender's executable.
    
    Args:
        modules_to_install (List[str]): List of package names to install.
        directory (str): Target directory for installation.
    
    Returns:
        int: Status code from the pip installation process.
    """
    from pip._internal import main
    return main(['install', '--upgrade', *modules_to_install, "--target", directory, '--verbose'])

def ensurepip_fallback():
    """
    A fallback method to bootstrap ensurepip using Blender's executable.
    """
    import ensurepip
    ensurepip.bootstrap(verbosity=1)

def get_python_expr(func: typing.Callable, *args, **kwargs) -> str:
    """
    Generates a Python expression for subprocess execution.
    
    Args:
        func (Callable): The function to execute.
        *args: Arguments for the function.
        **kwargs: Keyword arguments for the function.
    
    Returns:
        str: A string containing the Python expression.
    """
    expr = [textwrap.dedent(inspect.getsource(func))]
    args_json = repr(json.dumps(args))
    kwargs_json = repr(json.dumps(kwargs))

    if args and kwargs:
        expr += [
            'import json',
            f'args = json.loads({args_json})',
            f'kwargs = json.loads({kwargs_json})',
            f'{func.__name__}(*args, **kwargs)'
        ]
    elif args:
        expr += [
            'import json',
            f'args = json.loads({args_json})',
            f'{func.__name__}(*args)'
        ]
    elif kwargs:
        expr += [
            'import json',
            f'kwargs = json.loads({kwargs_json})',
            f'{func.__name__}(**kwargs)'
        ]
    else:
        expr.append(f'{func.__name__}()')

    return '\n'.join(expr)

def get_terminal_width(fallback: int = 80) -> int:
    """
    Retrieves the terminal width or returns a fallback value.
    
    Args:
        fallback (int): Default width if terminal size cannot be determined.
    
    Returns:
        int: Terminal width.
    """
    try:
        return int(os.environ.get('COLUMNS', fallback))
    except Exception:
        try:
            return os.get_terminal_size(sys.__stdout__.fileno()).columns
        except Exception:
            return fallback

def print_separator(*values: object, sep: str = ' ') -> None:
    """
    Prints a separator line with centered text.
    
    Args:
        *values: Text to include in the separator.
        sep (str): Separator between values.
    """
    width = get_terminal_width() - 1
    text = sep.join(map(str, values))
    text = f' {text} ' if text else ''
    half_width = (width - len(text)) // 2
    print('=' * half_width + text + '=' * (width - len(text) - half_width), flush=True)

def get_os_environ() -> dict:
    """
    Prepares and returns the environment variables for subprocesses.
    
    Returns:
        dict: Environment variables with modified PATH.
    """
    env = os.environ.copy()
    blender_dir = os.path.dirname(BLENDER_EXECUTABLE)
    blender_crt = os.path.join(blender_dir, 'blender.crt')

    def add_to_path(path: str):
        if os.path.exists(path):
            path = os.path.realpath(path)
            if path not in env['PATH']:
                env['PATH'] = path + os.pathsep + env['PATH']

    add_to_path(blender_crt)
    add_to_path(blender_dir)
    return env

def get_site_packages_directory(root_dir: str = ROOT_DIR) -> str:
    """
    Determines the site-packages directory for dependencies.
    
    Args:
        root_dir (str): Root directory for installation.
    
    Returns:
        str: Path to the site-packages directory.
    """
    version = sys.version_info
    return os.path.join(root_dir, '_deps', f"v{version[0]}{version[1]}")

def get_missing_site_packages(packages: typing.List[typing.Tuple[str, str]], directory: str = None) -> list:
    """
    Checks for missing packages in the specified directory.
    
    Args:
        packages (List[Tuple[str, str]]): List of tuples (import name, pip name).
        directory (str): Directory where packages are checked.
    
    Returns:
        list: List of missing packages.
    """
    directory = directory or get_site_packages_directory()
    directory = os.path.abspath(directory)
    if directory not in sys.path and os.path.exists(directory):
        sys.path.append(directory)

    return [package for package in packages if not importlib.util.find_spec(package[0])]

def ensure_site_packages(packages: typing.List[typing.Tuple[str, str]], directory: str = None, forced: bool = False) -> None:
    """
    Ensures the specified packages are installed in the site-packages directory.
    
    Args:
        packages (List[Tuple[str, str]]): List of tuples (import name, pip name).
        directory (str): Directory for package installation.
        forced (bool): If True, installs packages even if they are detected.
    """
    if not packages:
        return

    directory = os.path.abspath(directory or get_site_packages_directory())
    os.makedirs(directory, exist_ok=True)
    if directory not in sys.path:
        sys.path.append(directory)

    modules_to_install = [module[1] for module in packages if forced or not importlib.util.find_spec(module[0])]
    if not modules_to_install:
        return

    print_separator('START ensure_site_packages')

    env = get_os_environ()
    env['PYTHONPATH'] = directory + os.pathsep + env.get('PYTHONPATH', '').strip(os.pathsep)

    # Install pip if necessary
    if not importlib.util.find_spec('pip'):
        print_separator('ensurepip')
        try:
            subprocess.run([PYTHON_BINARY, '-m', 'ensurepip', '--verbose'], check=True, env=env)
        except subprocess.CalledProcessError as e:
            if e.returncode == STATUS_DLL_NOT_FOUND:
                subprocess.run([BLENDER_EXECUTABLE, '--factory-startup', '-b', '--python-expr', get_python_expr(ensurepip_fallback)], check=True, env=env)
            else:
                traceback.print_exc()
        except Exception:
            traceback.print_exc()

    # Upgrade pip and install dependencies
    print_separator('upgrade pip')
    try:
        subprocess.run([PYTHON_BINARY, '-m', 'pip', 'install', '--upgrade', 'pip', "--target", directory, '--verbose'], check=True, env=env)
    except subprocess.CalledProcessError as e:
        if e.returncode == STATUS_DLL_NOT_FOUND:
            subprocess.run([BLENDER_EXECUTABLE, '--factory-startup', '-b', '--python-expr', get_python_expr(pip_fallback, ['pip'], directory)], check=True, env=env)
        else:
            traceback.print_exc()
    except Exception:
        traceback.print_exc()

    print_separator('install dependencies')
    try:
        subprocess.run([PYTHON_BINARY, '-m', 'pip', 'install', '--upgrade', *modules_to_install, "--target", directory, '--verbose'], check=True, env=env)
    except subprocess.CalledProcessError as e:
        if e.returncode == STATUS_DLL_NOT_FOUND:
            subprocess.run([BLENDER_EXECUTABLE, '--factory-startup', '-b', '--python-expr', get_python_expr(pip_fallback, modules_to_install, directory)], check=True, env=env)
        else:
            traceback.print_exc()

    importlib.invalidate_caches()

    missing_packages = get_missing_site_packages(packages, directory)
    if missing_packages:
        raise Exception(f'Failed to install dependencies: {missing_packages}')

    print_separator('END ensure_site_packages')
