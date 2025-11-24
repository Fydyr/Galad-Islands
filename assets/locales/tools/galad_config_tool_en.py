# -*- coding: utf-8 -*-
"""
English translations for the Galad Config Tool (Tkinter).
"""

TRANSLATIONS = {
    "window.title": "Galad Config Tool",

    "warn.config_missing.title": "Missing configuration file",
    "warn.config_missing.message": "Configuration file not found:\n{path}\n\nA new file will be created automatically on first save.",

    "error.config_load.title": "Configuration error",
    "error.config_load.message": "Error loading configuration:\n{error}\n\nUsing defaults.",

    "info.custom_res.title": "Custom resolutions",
    "info.custom_res.message": "No custom resolutions file found.\n\nIt will be created automatically when you add your first custom resolution.\n\nLocation: {name}",

    "dialog.filetypes.json": "JSON files",
    "dialog.filetypes.all": "All files",

    "dialog.config.title": "Select configuration file",
    "dialog.res.title": "Select custom resolutions file",

    "dialog.ok.title": "OK",
    "dialog.error.title": "Error",

    "msg.reset_done": "Settings reset to defaults",
    "msg.apply_done": "Settings applied",

    "apply_paths.warn.prefix": "Paths applied with warnings:",
    "apply_paths.warn.config_will_create": "Config: {name} will be created",
    "apply_paths.warn.config_dir_missing": "Config: folder {parent} not found",
    "apply_paths.warn.res_will_create": "Resolutions: {name} will be created",
    "apply_paths.warn.res_dir_missing": "Resolutions: folder {parent} not found",
    "apply_paths.ok": "Paths applied successfully",
    "apply_paths.error": "Error: {error}",
    "button_reset_tutorials": "Reset tutorials",
    "gameplay_info": "Gameplay-related options (tutorials, etc.)",
    "button_check_updates": "Check now",
    "updates_info": "Update checks and release options",
    "options.check_updates": "Check for updates",
    "options.check_updates_result": "Check result: {result}",
    "options.check_updates_error": "Error checking updates: {error}",
    "options.check_updates_none": "No update found",
    "options.check_updates_available": "New version available: {version}\n{url}",
    # Marauder models (models tab)
    "tab.models.title": "Marauder models",
    "btn.choose_folder": "Choose folder…",
    "btn.refresh": "Refresh",
    "btn.open_folder": "Open folder",
    "btn.delete_selected": "Delete selected",
    "btn.delete_all": "Delete ALL",
    "btn.apply": "Apply",
    "label.keep_n": "Keep most recent N:",
    "label.delete_older_days": "Delete older than days:",

    "dialog.select_folder.title": "Select models folder",
    "dialog.select_folder.message": "Default models folder not found:\n{path}\n\nDo you want to choose an existing folder now?\nClick 'No' to create the default folder.",
    "dialog.browse.title": "Select models folder",
    "dialog.confirm.title": "Confirm",
    "dialog.error.title": "Error",
    "dialog.done.title": "Done",
    "dialog.invalid_value.title": "Invalid value",
    "dialog.delete_selected.title": "Delete selected",
    "dialog.delete_all.title": "Delete ALL",
    "dialog.delete_older.title": "Delete older than",

    "status.found_in": "Found {count} model file(s) in {path}",

    "msg.no_selection": "No models selected.",
    "msg.deleted_n": "Deleted {n} file(s).",
    "msg.no_models": "No models to delete.",
    "msg.all_deleted": "All models deleted.",
    "msg.nothing_to_delete": "There are {count} models; nothing to delete.",
    "msg.keep_n_done": "Kept {n}, deleted {m}.",
    "msg.none_older": "No models older than the specified age.",
    "msg.deleted_old": "Deleted {n} old model(s).",

    "confirm.delete_selected": "Delete {n} selected model(s)?",
    "confirm.delete_all": "Delete ALL ({n}) model file(s)?",
    "confirm.keep_n": "Keep {n} most recent, delete {m} older model(s)?",
    "confirm.delete_older": "Delete {n} model(s) older than {days} day(s)?",

    "error.delete_failed": "Failed to delete {name}: {err}",
    "error.keep_n_invalid": "Please enter a valid non-negative integer for N.",
    "error.days_invalid": "Please enter a valid non-negative integer for days."
}
