# -*- coding: utf-8 -*-
"""
English translations for Galad Islands
"""

TRANSLATIONS = {}

# Merge new categorized translations if present
try:
  from assets.locales.en import TRANSLATIONS as _EN_CATEGORIES
  if isinstance(_EN_CATEGORIES, dict):
    TRANSLATIONS.update(_EN_CATEGORIES)
except Exception:
  # best-effort: keep existing translations working even if new modules are not available
  pass
