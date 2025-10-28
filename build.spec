# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all, copy_metadata, collect_dynamic_libs

# --- Analyse des dépendances ---
# On analyse les deux scripts pour trouver toutes les dépendances communes.
analysis = Analysis(
    ['main.py', 'tools/galad_config.py'], # Scripts d'entrée
    pathex=[os.getcwd()], # Chemin racine du projet
    binaries=[
        ('/usr/lib/libpython3.13.so.1.0', '.') if sys.platform.startswith('linux') else \
        ('/usr/local/Frameworks/Python.framework/Versions/3.13/lib/libpython3.13.dylib', '.') if sys.platform == 'darwin' else []
    ],
    datas=[
        ('assets', 'assets'),
        ('models/*.pkl', 'models')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# --- Création du PYZ (archive des modules Python) ---
pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=None)

# --- Définition des exécutables ---
# On définit chaque exécutable SANS les rassembler.
# Ils seront créés dans des dossiers temporaires par PyInstaller.
exe_game = EXE(
    pyz,
    analysis.scripts,
    name='galad-islands',
    console=False, # Pas de console pour le jeu
    icon='assets/logo.ico'
)

exe_config_tool = EXE(
    pyz,
    analysis.scripts,
    name='galad-config-tool',
    console=False, # Pas de console pour l'outil de config
    icon='assets/logo.ico'
)

# --- Rassemblement final ---
# C'est ici que tout est mis en commun dans le dossier de sortie final.
# Cette structure est la bonne pratique pour les applications multi-exécutables.
coll = COLLECT(exe_game, exe_config_tool, analysis.binaries, analysis.datas, name='galad-dist')
