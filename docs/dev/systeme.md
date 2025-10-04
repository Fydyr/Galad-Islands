# Paramètres système critiques

Ces paramètres définissent les contraintes minimales et optimales du moteur de jeu basé sur **Pygame**.  
Ils garantissent un fonctionnement stable, une réactivité correcte et une expérience fluide.

| Paramètre | Description | Valeur par défaut | Impact critique |
|-----------|-------------|-------------------|-----------------|
| **Résolution d’affichage** | Dimensions de la fenêtre de jeu (largeur × hauteur en pixels). | `1168 × 629` | Affecte directement la charge GPU/CPU et la lisibilité de l’interface. |
| **Framerate cible** | Nombre d’images par seconde visé. | `30 FPS` | Détermine la fluidité du gameplay et la consommation CPU. |
| **Taille de la carte** | Dimensions logiques du monde (en pixels). | `5000 × 5000 px` | Impact mémoire (tileset, collisions) et pathfinding. |
| **Gestion des entités actives** | Nombre maximum d’unités/personnages simultanés en mémoire. | `200` | Impact majeur sur la boucle de rendu et l’IA. |
| **Système audio** | Fréquence d’échantillonnage et nombre de canaux. | `44100 Hz, stéréo` | Influence la qualité sonore et l’utilisation mémoire. |
| **Mémoire texture (VRAM simulée)** | Taille maximale des sprites/tiles chargés en cache. | `256 Mo` | Limite la taille des assets utilisables sans swap disque. |
| **Quadtree/Spatial Hash** | Taille des cellules de partition spatiale pour collisions et IA. | `64 px` | Conditionne la performance des calculs de collisions. |
| **Tick de simulation** | Durée fixe d’un cycle logique (physique/IA). | `16 ms (≈60 Hz)` | Assure cohérence des calculs indépendamment du framerate. |

---

## Exemple de fichier de configuration

Ces paramètres peuvent être stockés dans un fichier **config.json** ou **YAML**, modifiables sans recompiler le jeu.

```json
{
  "resolution": [1280, 720],
  "framerate": 30,
  "map_size": [5000, 5000],
  "max_entities": 200,
  "audio": {
    "frequency": 44100,
    "channels": 2
  },
  "texture_cache": 268435456,
  "spatial_hash_size": 64,
  "tick_duration_ms": 16
}
