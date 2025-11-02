# -*- coding: utf-8 -*-
"""
Traductions FR pour l'outil GUI de nettoyage des modèles Maraudeur.
"""

TRANSLATIONS = {
    "window.title": "Nettoyeur de Modèles Maraudeur",
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
