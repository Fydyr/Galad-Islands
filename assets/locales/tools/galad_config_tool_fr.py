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
    "button_reset_tutorials": "Réinitialiser les tutoriels",
    "gameplay_info": "Options liées au gameplay (tutoriels, etc.)",
    "button_check_updates": "Vérifier maintenant",
    "updates_info": "Vérification des mises à jour et options de release",
    "options.check_updates": "Vérifier les mises à jour",
    "options.check_updates_result": "Résultat de la vérification: {result}",
    "options.check_updates_error": "Erreur lors de la vérification: {error}",
    "options.check_updates_none": "Aucune mise à jour trouvée",
    "options.check_updates_available": "Nouvelle version disponible : {version}\n{url}",
    # Marauder models (models tab)
    "tab.models.title": "Modèles Maraudeur",
    "btn.choose_folder": "Choisir le dossier…",
    "btn.refresh": "Rafraîchir",
    "btn.open_folder": "Ouvrir le dossier",
    "btn.delete_selected": "Supprimer la sélection",
    "btn.delete_all": "Tout supprimer",
    "btn.apply": "Appliquer",
    "label.keep_n": "Conserver les N plus récents :",
    "label.delete_older_days": "Supprimer plus vieux que (jours) :",

    "dialog.select_folder.title": "Sélectionner le dossier des modèles",
    "dialog.select_folder.message": "Le dossier par défaut n'existe pas :\n{path}\n\nVoulez-vous choisir un dossier existant maintenant ?\nCliquez sur 'Non' pour créer le dossier par défaut.",
    "dialog.browse.title": "Sélectionner le dossier des modèles",
    "dialog.confirm.title": "Confirmer",
    "dialog.error.title": "Erreur",
    "dialog.done.title": "Terminé",
    "dialog.invalid_value.title": "Valeur invalide",
    "dialog.delete_selected.title": "Supprimer la sélection",
    "dialog.delete_all.title": "Tout supprimer",
    "dialog.delete_older.title": "Supprimer plus vieux que",

    "status.found_in": "{count} fichier(s) modèle trouvés dans {path}",

    "msg.no_selection": "Aucun modèle sélectionné.",
    "msg.deleted_n": "{n} fichier(s) supprimé(s).",
    "msg.no_models": "Aucun modèle à supprimer.",
    "msg.all_deleted": "Tous les modèles ont été supprimés.",
    "msg.nothing_to_delete": "Il y a {count} modèle(s) ; rien à supprimer.",
    "msg.keep_n_done": "Conservés {n}, supprimés {m}.",
    "msg.none_older": "Aucun modèle plus ancien que l'âge spécifié.",
    "msg.deleted_old": "{n} ancien(s) modèle(s) supprimé(s).",

    "confirm.delete_selected": "Supprimer {n} modèle(s) sélectionné(s) ?",
    "confirm.delete_all": "Supprimer TOUS les {n} fichier(s) de modèle ?",
    "confirm.keep_n": "Conserver les {n} plus récents, supprimer {m} modèle(s) plus ancien(s) ?",
    "confirm.delete_older": "Supprimer {n} modèle(s) plus ancien(s) que {days} jour(s) ?",

    "error.delete_failed": "Échec de suppression de {name} : {err}",
    "error.keep_n_invalid": "Veuillez saisir un entier non négatif valide pour N.",
    "error.days_invalid": "Veuillez saisir un entier non négatif valide pour le nombre de jours."
}
