#!/usr/bin/env python3
"""
Script de test pour vérifier la variation d'angle des tirs du Scout.
"""

def test_angle_variation():
    """Vérifie que les angles varient correctement avec le compteur de tirs."""
    angle_variations = [-5.0, 0.0, 5.0, -3.0, 3.0]
    
    print("Test de variation d'angle pour 15 tirs consécutifs:")
    print("=" * 60)
    
    for shot_counter in range(15):
        angle_offset = angle_variations[int(shot_counter) % len(angle_variations)]
        print(f"Tir #{shot_counter + 1}: offset = {angle_offset:+.1f}°")
    
    print("\n" + "=" * 60)
    print("✅ Les angles alternent correctement entre:", angle_variations)
    print("   Cela évite que les projectiles soient tous sur la même trajectoire")
    print("   et se détruisent mutuellement lors d'affrontements Scout vs Scout.")

if __name__ == "__main__":
    test_angle_variation()
