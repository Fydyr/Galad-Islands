#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du système de tips traduites
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.settings.localization import t, set_language, get_current_language, get_available_languages, get_all_tips, get_random_tip

def test_tips_translation():
    print("=== Test des tips traduites ===")
    
    # Test en français
    print("\n--- Tips en français ---")
    set_language("fr")
    print(f"Langue: {get_current_language()}")
    
    tips_fr = get_all_tips()
    print(f"Nombre de tips: {len(tips_fr)}")
    print(f"Première tip: {tips_fr[0] if tips_fr else 'Aucune tip'}")
    print(f"Tip aléatoire: {get_random_tip()}")
    
    # Test en anglais
    print("\n--- Tips en anglais ---")
    set_language("en")
    print(f"Langue: {get_current_language()}")
    
    tips_en = get_all_tips()
    print(f"Nombre de tips: {len(tips_en)}")
    print(f"Première tip: {tips_en[0] if tips_en else 'No tips'}")
    print(f"Tip aléatoire: {get_random_tip()}")
    
    # Comparaison
    print(f"\n--- Comparaison ---")
    print(f"Tips français: {len(tips_fr)}")
    print(f"Tips anglaises: {len(tips_en)}")
    print(f"Même nombre de tips: {'✅' if len(tips_fr) == len(tips_en) else '❌'}")
    
    print("\n✅ Test des tips terminé!")

if __name__ == "__main__":
    test_tips_translation()