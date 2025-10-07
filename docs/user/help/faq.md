# Questions fréquentes

## 🚀 Installation et premiers pas

### Q: Le jeu ne se lance pas, que faire ?

**Solutions courantes :**

1. **Mettre à jour le jeu** : Télécharger la dernière version depuis la [page des releases](
2. **Vérifier la structure des fichiers** : Le dossier `assets/` doit être au même niveau que l'exécutable `galad-islands`.
3. **Retélécharger le jeu** : Le fichier peut être corrompu.
4. **Lancer le jeu via terminal/console pour savoir plus sur l'erreur** :
   - Windows : Ouvrir `cmd`, naviguer vers le dossier du jeu et exécuter `galad-islands.exe`
   - macOS/Linux : Ouvrir un terminal, naviguer vers le dossier du jeu et exécuter `./galad-islands`
   - Créer une issue sur la [page GitHub du projet](https://github.com/fydyr/Galad-Islands/issues) avec les messages d'erreur affichés.
  
### Q: L'écran reste noir au lancement

**Causes possibles :**

- **Problème graphique** : Pilotes obsolètes
- **Résolution incompatible** : Écran trop petit ou trop grand
- **Jeu corrompu** : Fichiers manquants ou endommagés

**Solutions :**

1. Mise à jour des pilotes graphiques
2. Essayer en mode fenêtré
3. Redémarrer l'ordinateur
4. Retélécharger le jeu

### Q: Comment changer la résolution ?

**Méthode 1 : Options en jeu**

1. Menu principal → Réglages
2. Section "Affichage"
3. Résolution personnalisée ou prédéfinie
4. Appliquer les changements

**Méthode 2 : Galad Config Tool**

1. Ouvrir `galad-config-tool` (inclus dans les releases)
2. Onglet "Affichage"
3. Choisir la résolution
4. Cliquer "Appliquer" puis lancer le jeu

## 🎮 Gameplay et mécaniques

### Q: Quelle est la meilleure composition d'armée ?

**Début de partie (0-5 min) :**

- **2x Scout** + **1x Maraudeur** + **1x Druid**
- Coût : 400 or
- Polyvalent et efficace

**Milieu de partie (5-10 min) :**

- **1x Leviathan** + **2x Maraudeur** + **1x Druid** + **1x Architect**
- Focus : Contrôle territorial + économie

**Fin de partie (10+ min) :**

- **2x Leviathan** + **3x Maraudeur** + **2x Druid**
- Armée quasi-invincible

### Q: Mes unités ne suivent pas mes ordres

**Problèmes courants :**

1. **Sélection incorrecte** : Vérifiez que vos unités sont bien sélectionnées
2. **Pathfinding** : Parfois l'IA ne trouve pas le chemin
3. **Combat en cours** : Les unités terminent leur action actuelle
4. **Ile inaccessible** : Pas de passage disponible

**Solutions :**

- **Utiliser** les groupes (`Ctrl + numéro`) pour rappeler rapidement l'unité voulue
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

### Q: Comment optimiser mes défenses ?

**Placement stratégique :**

1. **Tours de défense** : Aux passages obligés
2. **Tours de soin** : Protégées derrière les combattants
3. **Redondance** : Plusieurs lignes de défense

**Formations défensives :**

```
  Tour Défense    Tour Défense
      \              /
       \            /
        Tour de Soin
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
2. **Défendre** jusqu'à égalisation des forces
3. **Exploiter** ses erreurs tactiques

**Techniques spécifiques :**

- **Hit-and-run** avec Scout
- **Focus fire** sur ses unités chères
- **Contrôle territorial** sur ses mines
- **Patience** et opportunisme

### Q: Mes Scouts meurent trop vite

**Micro-management des Scouts :**

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
2. **Plein écran** : Souvent plus fluide

**Optimisations système :**

- Fermer les applications inutiles
- Libérer de la RAM
- Mettre à jour le jeu
- Redémarrer régulièrement

## 🐛 Résolution de problèmes

### Q: J'ai trouvé un bug, comment le signaler ?

**Informations à fournir :**

1. **Version** : Numéro du jeu
2. **Système** : OS + configuration
3. **Reproduction** : Étapes pour reproduire
4. **Logs** : Messages d'erreur dans la console

**Canaux de signalement :**

- GitHub Issues (recommandé)
- Email développeur

### Q: Le son ne fonctionne pas

**Diagnostic audio :**

1. **Volume du jeu** : Vérifier dans les options
2. **Volume système** : Vérifier les réglages OS
3. **Codecs audio** : Installer les codecs manquants
4. **Fichiers audio** : Vérifier présence dans `/assets/sounds/`

### Q: Crash au lancement avec erreur Python

**Permission denied**

- Droits d'administrateur
- Antivirus qui bloque

---

*D'autres questions ? Consultez les [crédits et contacts](credits.md) pour obtenir de l'aide !*
