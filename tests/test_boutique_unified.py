#!/usr/bin/env python3
"""
Test de la boutique unifiée Galad Islands
"""

import sys
import os

# Ajouter le répertoire parent au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui.boutique import UnifiedShop, ShopFaction, ShopCategory
import pygame

def test_unified_shop():
    """Test de base de la boutique unifiée."""
    pygame.init()
    
    # Initialiser la boutique alliée
    ally_shop = UnifiedShop(800, 600, ShopFaction.ALLY)
    print("✅ Boutique alliée créée")
    print(f"   - Items unités: {len(ally_shop.shop_items[ShopCategory.UNITS])}")
    print(f"   - Items bâtiments: {len(ally_shop.shop_items[ShopCategory.BUILDINGS])}")
    
    # Tester le changement de faction
    ally_shop.switch_faction(ShopFaction.ENEMY)
    print("✅ Basculement vers faction ennemie")
    print(f"   - Items unités: {len(ally_shop.shop_items[ShopCategory.UNITS])}")
    print(f"   - Items bâtiments: {len(ally_shop.shop_items[ShopCategory.BUILDINGS])}")
    
    # Retour à la faction alliée
    ally_shop.switch_faction(ShopFaction.ALLY)
    print("✅ Retour à la faction alliée")
    
    # Test des fonctions de base
    ally_shop.open()
    print("✅ Ouverture de la boutique")
    
    ally_shop.set_player_gold(500)
    print(f"✅ Or du joueur défini à: {ally_shop.player_gold}")
    
    ally_shop.close()
    print("✅ Fermeture de la boutique")
    
    pygame.quit()
    print("\n🎉 Tous les tests sont passés avec succès!")

if __name__ == "__main__":
    test_unified_shop()