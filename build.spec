# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all, copy_metadata, collect_dynamic_libs

# NOTE: Building with a single Analysis (above) may add excluded modules or
# heavy libs to all executables. To have finer control we create one
# Analysis per executable. This mirrors the CI flags used in GitHub Actions.

# --- Dependency analysis ---
# We analyze each entry script to find its dependencies.
# Game (main) Analysis: needs assets + models and sklearn forest import
analysis_game = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
    datas=[('assets', 'assets'), ('src/models/*.pkl', 'models')],
    hiddenimports=['sklearn.ensemble._forest'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# Config tool: needs locales + src, exclude heavy libs to keep package small
analysis_config = Analysis(
    ['tools/galad_config.py'],
    pathex=[os.getcwd()],
    datas=[('assets/locales', 'assets/locales'), ('src', 'src')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=['esper', 'llvmlite', 'numba', 'numpy', 'Pillow', 'sklearn', 'joblib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# Maraudeur AI Cleaner: similar to config tool
analysis_maraudeur = Analysis(
    ['tools/maraudeur_ai_cleaner.py'],
    pathex=[os.getcwd()],
    datas=[('assets/locales', 'assets/locales'), ('src', 'src')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=['esper', 'llvmlite', 'numba', 'numpy', 'Pillow', 'sklearn', 'joblib', 'pygame'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# --- Create PYZ (Python modules archive) ---
pyz_game = PYZ(analysis_game.pure, analysis_game.zipped_data, cipher=None)
pyz_config = PYZ(analysis_config.pure, analysis_config.zipped_data, cipher=None)
pyz_maraudeur = PYZ(analysis_maraudeur.pure, analysis_maraudeur.zipped_data, cipher=None)

# --- EXE definitions ---
# Define each executable WITHOUT merging them.
# They will be created in temporary folders by PyInstaller.
exe_game = EXE(
    pyz_game,
    analysis_game.scripts,
    name='galad-islands',
    console=False,  # No console for the game
    icon='assets/logo.ico'
)

exe_config_tool = EXE(
    pyz_config,
    analysis_config.scripts,
    name='galad-config-tool',
    console=False,  # No console for the config tool
    icon='assets/logo.ico'
)

exe_maraudeur = EXE(
    pyz_maraudeur,
    analysis_maraudeur.scripts,
    name='MaraudeurAiCleaner',
    console=False,
    icon='assets/logo.ico'
)

# --- Final collect ---
# This is where all exe outputs and related files are placed into
# the final output directories. This structure is the recommended
# practice for multi-executable applications.
coll_game = COLLECT(exe_game,
                    analysis_game.binaries, analysis_game.datas,
                    name='galad-islands')

coll_config = COLLECT(exe_config_tool,
                      analysis_config.binaries, analysis_config.datas,
                      name='galad-config-tool')

coll_maraudeur = COLLECT(exe_maraudeur,
                         analysis_maraudeur.binaries, analysis_maraudeur.datas,
                         name='MaraudeurAiCleaner')
