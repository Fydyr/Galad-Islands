# Questions fréquentes

## 🚀 Installation et premiers pas

### Q: Le jeu ne se lance pas, que faire ?

**Solutions courantes :**

1. **Vérifiez Python** : Version 3.7+ requise
   ```bash
   python --version
   ```

2. **Installez Pygame** :
   ```bash
   pip install pygame
   ```

3. **Droits d'accès** : Lancez depuis le bon répertoire
   ```bash
   cd Galad-Islands
   python main.py
   ```

4. **Dépendances manquantes** :
   ```bash
   pip install -r requirements.txt
   ```

### Q: L'écran reste noir au lancement

**Causes possibles :**
- **Problème graphique** : Pilotes obsolètes
- **Résolution incompatible** : Écran trop petit
- **Pygame mal installé** : Réinstaller la bibliothèque

**Solutions :**
1. Mise à jour des pilotes graphiques
2. Essayer en mode fenêtré
3. Redémarrer l'ordinateur
4. Réinstaller Pygame : `pip uninstall pygame && pip install pygame`

### Q: Comment changer la résolution ?

**Méthode 1 : Options en jeu**
1. Menu principal → Réglages
2. Section "Affichage"
3. Résolution personnalisée ou prédéfinie
4. Appliquer les changements

**Méthode 2 : Fichier de configuration**
- Éditer `galad_config.json`
- Modifier `"resolution": [largeur, hauteur]`
- Sauvegarder et relancer

## 🎮 Gameplay et mécaniques

### Q: Comment gagner de l'or plus rapidement ?

**Stratégies efficaces :**

1. **Exploration précoce** : Coffres = 25-50 or chacun
2. **Contrôle des mines** : +10 or/seconde par mine
3. **Générateurs d'or** : +10 or/seconde par bâtiment
4. **Économie avant militaire** : Investissement rentable

**Calcul de rentabilité :**
- Générateur (200 or) = rentable en 20 secondes
- 3 générateurs = +1800 or/minute
- Focus économie = victoire quasi-assurée

### Q: Quelle est la meilleure composition d'armée ?

**Début de partie (0-5 min) :**
- **2x Zasper** + **1x Barhamus** + **1x Druid**
- Coût : 400 or
- Polyvalent et efficace

**Milieu de partie (5-10 min) :**
- **1x Draupnir** + **2x Barhamus** + **1x Druid** + **1x Architect**
- Focus : Contrôle territorial + économie

**Fin de partie (10+ min) :**
- **2x Draupnir** + **3x Barhamus** + **2x Druid**
- Armée quasi-invincible

### Q: Comment bien utiliser les boosts ?

**Boost d'Attaque (`Q`) :**
- **Timing** : Juste avant un combat important
- **Cible** : Maximum d'unités engagées
- **Durée** : 30 secondes = bien chronométrer

**Boost de Défense (`E`) :**
- **Timing** : Quand vous subissez une attaque
- **Priorité** : Protéger les unités chères (Draupnir)
- **Tactique** : Permet de tenir jusqu'aux renforts

**Optimisation :**
- **Ne jamais** gaspiller sur 1 seule unité
- **Attendre** le bon moment plutôt que spam
- **Combiner** avec mouvements tactiques

### Q: Mes unités ne suivent pas mes ordres

**Problèmes courants :**

1. **Sélection incorrecte** : Vérifiez que vos unités sont bien sélectionnées
2. **Pathfinding** : Parfois l'IA ne trouve pas le chemin
3. **Combat en cours** : Les unités terminent leur action actuelle
4. **Ile inaccessible** : Pas de passage disponible

**Solutions :**
- **Clic maintenu** pour sélection multiple
- **Double-clic** pour déplacer en force
- **Attendre** la fin des animations
- **Vérifier** les connexions entre îles

## 🏗️ Construction et bâtiments

### Q: Pourquoi je ne peux pas construire ?

**Vérifications essentielles :**

1. **Architect présent** : Au moins 1 dans l'armée
2. **Sur une île** : L'Architect doit être positionné
3. **Île libre** : Pas de bâtiment existant
4. **Or suffisant** : Coût affiché dans la boutique

**Cas particuliers :**
- **Générateur d'or** : Require une mine contrôlée
- **Améliorations** : Certains bâtiments ont des prérequis
- **Limite territoriale** : Île sous votre contrôle

### Q: Comment optimiser mes défenses ?

**Placement stratégique :**

1. **Tours de défense** : Aux passages obligés
2. **Tours de soin** : Protégées derrière les combattants
3. **Générateurs** : Loin du front, bien défendus
4. **Redondance** : Plusieurs lignes de défense

**Formations défensives :**
```
  Tour Défense    Tour Défense
      \              /
       \            /
        Tour de Soin
       /            \
  Générateur    Générateur
```

### Q: Mes bâtiments sont détruits trop facilement

**Renforcement défensif :**

1. **Escorte militaire** : Unités près des bâtiments
2. **Défenses actives** : Tours de protection
3. **Réparations** : Druid peut soigner les bâtiments
4. **Positionnement** : Éviter les zones exposées

**Tactiques de protection :**
- **Jamais** de bâtiment isolé
- **Toujours** prévoir une défense
- **Anticiper** les attaques ennemies
- **Diversifier** les positions

## ⚔️ Combat et stratégie

### Q: Comment battre un joueur plus fort ?

**Stratégies de retournement :**

1. **Éviter** les combats frontaux
2. **Harceler** son économie (générateurs)
3. **Défendre** jusqu'à égalisation des forces
4. **Exploiter** ses erreurs tactiques

**Techniques spécifiques :**
- **Hit-and-run** avec Zasper
- **Focus fire** sur ses unités chères
- **Contrôle territorial** sur ses mines
- **Patience** et opportunisme

### Q: Mes Zasper meurent trop vite

**Micro-management des Zasper :**

1. **Kiting** : Attaquer puis reculer
2. **Groupe** : Jamais seuls, toujours en meute
3. **Support** : Druid à proximité pour les soins
4. **Terrain** : Utiliser les obstacles naturels

**Erreurs à éviter :**
- **Foncer** tête baissée
- **Isoler** les unités
- **Négliger** les soins
- **Sous-estimer** la portée ennemie

### Q: Comment gérer plusieurs fronts ?

**Multi-tasking stratégique :**

1. **Prioriser** : Front principal vs secondaire
2. **Défense mobile** : Unités rapides entre zones
3. **Téléporation** : Pour renforcer rapidement
4. **Économie solide** : Pour remplacer les pertes

**Organisation :**
- **Groupes de contrôle** : `Ctrl + 1-9`
- **Rotation** rapide entre zones
- **Anticipation** des menaces
- **Communication** avec votre équipe (si applicable)

## 🔧 Paramètres et performance

### Q: Le jeu rame, comment l'optimiser ?

**Optimisations graphiques :**

1. **Résolution** : Réduire si nécessaire
2. **Particules** : Désactiver les effets non-essentiels
3. **Framerate** : Limiter à 30 FPS si besoin
4. **Plein écran** : Souvent plus fluide

**Optimisations système :**
- Fermer les applications inutiles
- Libérer de la RAM
- Mettre à jour Python/Pygame
- Redémarrer régulièrement

### Q: Comment sauvegarder ma partie ?

**Système de sauvegarde :**

**Automatique :**
- Configuration dans `galad_config.json`
- Réglages d'interface sauvés automatiquement
- Statistiques de jeu conservées

**Manuelle :**
- Pas de sauvegarde en cours de partie
- Jeu conçu pour des parties courtes (10-20 min)
- Focus sur la rejouabilité

### Q: Comment jouer en multijoueur ?

**Statut actuel :**
- Version actuelle : **Solo uniquement**
- Multijoueur : **En développement**
- Alternatives : **Hot-seat** possible (tour par tour)

**Contournements :**
- Partage d'écran en ligne
- Jeu en local sur le même PC
- Défis/scores entre amis

## 🐛 Résolution de problèmes

### Q: J'ai trouvé un bug, comment le signaler ?

**Informations à fournir :**

1. **Version** : Python + Pygame
2. **Système** : OS + configuration
3. **Reproduction** : Étapes pour reproduire
4. **Logs** : Messages d'erreur dans la console

**Canaux de signalement :**
- GitHub Issues (recommandé)
- Email développeur
- Forums communautaires

### Q: Le son ne fonctionne pas

**Diagnostic audio :**

1. **Volume système** : Vérifier les réglages OS
2. **Pygame audio** : Réinstaller si nécessaire
3. **Codecs audio** : Installer les codecs manquants
4. **Fichiers audio** : Vérifier présence dans `/sounds/`

**Solutions communes :**
```bash
pip install pygame --upgrade
```

### Q: Crash au lancement avec erreur Python

**Erreurs fréquentes :**

**ModuleNotFoundError: No module named 'pygame'**
```bash
pip install pygame
```

**ImportError: DLL load failed**
- Réinstaller Pygame
- Vérifier version Python 64/32 bits

**Permission denied**
- Droits d'administrateur
- Antivirus qui bloque

---

*D'autres questions ? Consultez les [crédits et contacts](credits.md) pour obtenir de l'aide !*