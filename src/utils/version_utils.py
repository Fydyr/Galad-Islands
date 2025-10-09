"""Utilities for version management."""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None


def get_project_version() -> str:
    """
    Read the project version from pyproject.toml.

    Returns:
        The version string from pyproject.toml, or "unknown" if not found.
    """
    # Get the project root directory (where pyproject.toml should be)
    if getattr(sys, '_MEIPASS', None):
        # Running as PyInstaller bundle
        project_root = Path(sys._MEIPASS).parent
    else:
        # Running as regular Python script
        if hasattr(sys.modules[__name__], '__file__') and sys.modules[__name__].__file__:
            module_file = sys.modules[__name__].__file__
            if module_file:
                project_root = Path(module_file).parent.parent.parent
            else:
                project_root = Path.cwd()
        else:
            project_root = Path.cwd()

    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        return "unknown"

    if tomllib is None:
        # Fallback if tomllib/tomli is not available
        return _read_version_fallback(pyproject_path)

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        return data.get("project", {}).get("version", "unknown")
    except Exception:
        return _read_version_fallback(pyproject_path)


def _read_version_fallback(pyproject_path: Path) -> str:
    """
    Fallback method to read version from pyproject.toml without tomllib.
    Looks for the version line manually.
    """
    try:
        with open(pyproject_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith('version = "'):
                    # Extract version from: version = "x.y.z"
                    return line.split('"')[1]
    except Exception:
        pass
    return "unknown"


def is_dev_mode_enabled() -> bool:
    """
    Check if dev mode is enabled in the configuration.

    Returns:
        True if dev mode is enabled, False otherwise.
    """
    try:
        from src.settings.settings import ConfigManager
        cfg = ConfigManager()
        return cfg.get('dev_mode', False)
    except Exception:
        return False