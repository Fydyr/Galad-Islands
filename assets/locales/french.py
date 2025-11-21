# -*- coding: utf-8 -*-
"""
Traductions françaises pour Galad Islands
"""

TRANSLATIONS = {}

# Merge new categorized translations if present
try:
    from assets.locales.fr import TRANSLATIONS as _FR_CATEGORIES
    if isinstance(_FR_CATEGORIES, dict):
        TRANSLATIONS.update(_FR_CATEGORIES)
except Exception:
    # Keep working if the new structure isn't present
    pass
