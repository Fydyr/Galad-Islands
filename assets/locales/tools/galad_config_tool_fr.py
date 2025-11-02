# -*- coding: utf-8 -*-
"""
Traductions FR pour l'outil Galad Config Tool (Tkinter).
"""

TRANSLATIONS = {
    "window.title": "Galad Config Tool",

    "warn.config_missing.title": "Fichier de configuration manquant",
    "warn.config_missing.message": "Fichier de configuration manquant :\n{path}\n\nUn nouveau fichier sera créé automatiquement lors de la première sauvegarde.",

    "error.config_load.title": "Erreur de configuration",
    "error.config_load.message": "Erreur lors du chargement de la configuration :\n{error}\n\nUtilisation des valeurs par défaut.",

    "info.custom_res.title": "Résolutions personnalisées",
    "info.custom_res.message": "Aucun fichier de résolutions personnalisées trouvé.\n\nIl sera créé automatiquement lors de l'ajout de votre première résolution personnalisée.\n\nEmplacement : {name}",

    "dialog.filetypes.json": "Fichiers JSON",
    "dialog.filetypes.all": "Tous les fichiers",

    "dialog.config.title": "Sélectionner le fichier de configuration",
    "dialog.res.title": "Sélectionner le fichier des résolutions personnalisées",

    "dialog.ok.title": "OK",
    "dialog.error.title": "Erreur",

    "msg.reset_done": "Paramètres remis aux valeurs par défaut",
    "msg.apply_done": "Paramètres appliqués",

    "apply_paths.warn.prefix": "Chemins appliqués avec avertissements:",
    "apply_paths.warn.config_will_create": "Config: {name} sera créé",
    "apply_paths.warn.config_dir_missing": "Config: dossier {parent} introuvable",
    "apply_paths.warn.res_will_create": "Résolutions: {name} sera créé",
    "apply_paths.warn.res_dir_missing": "Résolutions: dossier {parent} introuvable",
    "apply_paths.ok": "Chemins appliqués avec succès",
    "apply_paths.error": "Erreur: {error}",
}
