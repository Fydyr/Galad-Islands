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
}
