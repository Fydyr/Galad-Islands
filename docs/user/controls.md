# Contrôles du jeu

## 🎮 Contrôles principaux

### Déplacement de la caméra
| Touche | Action |
|--------|--------|
| `⬅️` ou `A` | Déplacer la caméra vers la gauche |
| `➡️` ou `D` | Déplacer la caméra vers la droite |
| `⬆️` ou `W` | Déplacer la caméra vers le haut |
| `⬇️` ou `S` | Déplacer la caméra vers le bas |
| `Molette ⬆️` | Zoom avant |
| `Molette ⬇️` | Zoom arrière |

### Sélection d'unités
| Touche | Unité |
|--------|-------|
| `1` | Première unité (Zasper) |
| `2` | Deuxième unité (Barhamus) |
| `3` | Troisième unité (Draupnir) |
| `4` | Quatrième unité (Druid) |
| `5` | Cinquième unité (Architect) |
| `6-9` | Unités supplémentaires |
| `Tab` | Unité suivante |
| `Shift+Tab` | Unité précédente |

## ⚔️ Contrôles de combat

### Actions d'unité
| Touche | Action |
|--------|--------|
| `R` | Capacité spéciale de l'unité sélectionnée |
| `A` | Mode attaque (cibler manuellement) |
| `H` | Arrêter l'unité / Hold position |
| `P` | Patrouille automatique |

### Commandes globales
| Touche | Action |
|--------|--------|
| `Q` | Boost d'attaque global (coût : 50 or) |
| `E` | Boost de défense global (coût : 50 or) |
| `T` | Changer de camp (Allié/Ennemi) |

## 🛒 Interface et menus

### Navigation
| Touche | Action |
|--------|--------|
| `B` | Ouvrir/Fermer la boutique |
| `Échap` | Menu pause / Retour |
| `F1` | Aide rapide |
| `F3` | Mode debug (informations techniques) |
| `Entrée` | Confirmer une action |

### Raccourcis boutique
| Touche | Action |
|--------|--------|
| `1-5` | Acheter l'unité correspondante |
| `Échap` | Fermer la boutique |
| `Flèches` | Navigation dans les catégories |

## 🎯 Contrôles avancés

### Gestion de la caméra
| Combinaison | Action |
|-------------|--------|
| `Ctrl + Flèches` | Déplacement rapide de la caméra |
| `Shift + Molette` | Zoom précis |
| `Espace` | Recentrer sur l'unité sélectionnée |
| `C` | Basculer entre vue libre et suivi d'unité |

### Groupes de contrôle
| Combinaison | Action |
|-------------|--------|
| `Ctrl + Shift + 1-9` | Assigner l'unité courante au groupe |
| `Ctrl + 1-9` | Rappeler un groupe enregistré |
| `Ctrl + A` | Cibler l'unité principale de la faction active |

## 📱 Interface tactile (si supportée)

### Gestes de base
- **Glisser** : Déplacer la caméra
- **Pincer** : Zoomer/Dézoomer
- **Tap** : Sélectionner une unité
- **Double tap** : Centrer sur une unité
- **Long press** : Menu contextuel

## ⚙️ Personnalisation des contrôles

!!! info "Configuration"
    Les contrôles peuvent être personnalisés dans le fichier `config.json` du jeu. Modifiez les valeurs suivantes :
    
    ```json
    {
      "controls": {
        "camera_speed": 200,
        "zoom_speed": 0.1,
        "camera_sensitivity": 1.0
      }
    }
    ```

### Paramètres ajustables
- **camera_speed** : Vitesse de déplacement de la caméra (pixels/seconde)
- **zoom_speed** : Vitesse du zoom (0.1 = lent, 0.5 = rapide)
- **camera_sensitivity** : Sensibilité générale (0.5 = moins sensible, 2.0 = plus sensible)

## 🔧 Contrôles spéciaux par unité

### Zasper (Scout)
- `R` : **Vision étendue** - Révèle une large zone pendant 10s
- **Mouvement** : 2x plus rapide que les autres unités

### Barhamus (Maraudeur)
- `R` : **Charge** - Attaque rapide avec dégâts augmentés
- **Défense** : Résistance accrue aux projectiles

### Draupnir (Léviathan)
- `R` : **Bombardement** - Attaque de zone dévastatrice
- **Mouvement** : Plus lent mais très résistant

### Druid (Soigneur)
- `R` : **Soin de groupe** - Soigne toutes les unités alliées proches
- **Support** : Pas d'attaque directe

### Architect (Constructeur)
- `R` : **Construction rapide** - Construit instantanément une tour
- **Bâtiment** : Peut construire des défenses

## 🆘 Raccourcis d'urgence

| Touche | Action |
|--------|--------|
| `Alt + F4` | Fermer le jeu immédiatement |
| `F11` | Basculer plein écran / fenêtré |
| `Ctrl + R` | Redémarrer la partie actuelle |
| `Ctrl + S` | Sauvegarder la partie |
| `Ctrl + Q` | Quitter vers le menu principal |

!!! warning "Attention"
    Certains raccourcis d'urgence peuvent faire perdre la progression non sauvegardée !

---

*Maintenant que vous maîtrisez les contrôles, découvrez le [guide des unités](units.md) !*