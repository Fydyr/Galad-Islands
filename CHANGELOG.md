# 🧾 Changelog

## v0.6.0 (2025-10-06)

### ✨ Feat

- Ajout d’un menu en jeu avec options **Reprendre**, **Paramètres** et **Quitter**.

### 🧹 Refactor

- Correction de l’indentation de la clé `spawn_bandits` dans les fichiers de traduction.

---

## v0.5.1 (2025-10-06)

### 🐞 Fix

- Création automatique d’un fichier de configuration avec valeurs par défaut si manquant.  
- Correction du fichier de localisation qui pouvait casser **Galad Settings Tool** sur Windows.  
- Amélioration du chemin d’exécution et des messages d’avertissement dans `galad_config.py`.

---

## v0.5.0 (2025-10-05)

### ✨ Feat

- Changement de l’unité de départ : **Druide → Éclaireur**.  
- Ajout de descriptions aux tours dans l’**Action Bar**.  
- **ProjectileCreator** : ajout de projectiles de soin pour les druides.  
- **Système complet de tours de défense** avec projectiles, notifications et capacités spéciales.  
- Implémentation du **système de ressources d’île** (`islandResources`).  
- Ajout du **Kraken Event**, des tentacules inactives et du **Storm Event**.  
- Ajout d’un **menu de debug enrichi** (spawn de bandits, gestion d’événements, ressources, or, etc.).  
- Intégration d’un **gestionnaire de résolutions personnalisées** et création de **Galad Options Tool**.  
- Ajout de nouvelles capacités spéciales : **Leviathan**, **Maraudeur**, **Scout**, **Barhamus**, **Zasper** et **Draupnir** (cooldowns, effets visuels, logique unifiée).  
- Ajout de sprites pour les unités spéciales (Kamikaze, projectiles ennemis, etc.).  
- Intégration de la gestion de l’or, de la boutique et des sélections d’unités.  
- Implémentation du **système d’affichage centralisé** (résolutions, fenêtres).  
- Ajout du fichier `help_en.md` et de traductions supplémentaires pour la fin de partie.

### 🐞 Fix

- Nombreux correctifs sur les collisions, projectiles, mines, événements et affichage.  
- Les projectiles traversent les îles, explosent à l’impact et disparaissent à la limite de la carte.  
- Les mines interagissent désormais correctement avec toutes les factions.  
- Correction du zoom par défaut, des cooldowns d’UI et de l’affichage de l’or.  
- Réduction du taux d’apparition du Kraken et équilibrage du spawn des tempêtes.  
- Ajustement de nombreux fichiers de composants (`bandits`, `storm`, `collision`, `player`, `health`, etc.).  
- Les paramètres audio enregistrés sont désormais pris en compte au lancement du jeu.  
- Correction des traductions (`options.custom_marker`, messages de fin de partie, etc.).  
- Fenêtre à nouveau redimensionnable et ajustement du zoom caméra.

### 🧹 Refactor

- Refactorisation du système de **BaseManager** (fusionné dans `BaseComponent`).  
- Réorganisation complète des composants pour plus de clarté.  
- Refactor du **gold management**, intégration dans `playerComponent`.  
- Suppression des anciens composants et du code de test.  
- Nettoyage général du code, constantes gameplay unifiées.  
- Amélioration du **UI handling**, des key bindings et du système d’options.

---

## v0.4.5 (2025-10-02)

### 🐞 Fix

- Correction de l’initialisation de `affected_unit_ids` dans le constructeur.

---

## v0.4.4 (2025-10-02)

### 🐞 Fix

- Les projectiles ne disparaissent plus lorsqu’ils touchent une île.

---

## v0.4.3 (2025-10-02)

### 🐞 Fix

- Les mines ne peuvent plus être détruites par les projectiles.

### 🧹 Refactor

- Intégration du gestionnaire de sprites pour le chargement des images de terrain et ajout de constantes de sprite.

---

## v0.4.2 (2025-10-02)

### 🧹 Refactor

- Centralisation des constantes de **modales**, **santé des bases**, **boutique** et **gameplay**.  
- Ajout d’un système de gestion des sprites avec initialisation et préchargement.  
- Refactorisation complète de l’architecture **ECS** pour une meilleure maintenance.

---

## v0.4.1 (2025-10-01)

### 🐞 Fix

- Suppression d’un fichier de test après vérification des hooks.

---

## v0.4.0 (2025-10-01)

### ✨ Feat

- Implémentation du **système de gestion de bases** et intégration au gameplay.

### 🧹 Refactor

- Modularisation de `game.py` en plusieurs classes.  
- Conversion des fichiers audio de **WAV → OGG** pour qualité et taille optimisées.

---

## v0.2.1 (2025-10-01)

### 🐞 Fix

- Ajout du support du chemin PyInstaller pour les builds Windows.

---

## v0.2.0 (2025-10-01)

### ✨ Feat

- Ajout du retour d’entité dans `unitFactory`.

### 🧹 Refactor

- **Options** : désactivation temporaire des résolutions personnalisées.  
- Mise à jour des conseils de résolution pour éviter les erreurs d’affichage.

---

## v0.1.2 (2025-10-01)

### ✨ Feat

- Ajout du **logo** dans l’interface principale.  
- Création de la **documentation technique** et début de la **doc utilisateur**.  
- Ajout du **système de boutique**, d’achat d’unités et de gestion de factions via la classe `Team`.  
- Mise en place du **système de localisation** (FR/EN) et des traductions pour tous les menus.  
- Ajout de la **barre de vie**, de la **barre d’action**, et des contrôles améliorés.  
- Intégration du **système de résolution d’écran**, du redimensionnement et de la sauvegarde des paramètres.  
- Ajout des **événements de debug**, de l’aide en jeu (`help.md`), et de nouveaux easter eggs dans le menu.  
- Début du **système de Vignes** pour le druide.  
- Création du **mouvement**, des collisions, des projectiles et des entités de base.

### 🐞 Fix

- Correction de nombreux bugs d’affichage, collisions, audio et configuration.  
- Ajustements sur les traductions, résolutions et paramètres de la fenêtre.  
- Correction du centrage caméra, des modales et de l’aide multilingue.  
- Nettoyage des imports, suppression de fichiers inutiles et correctifs mineurs sur le gameplay.

### 🧹 Refactor

- Externalisation des composants UI (`settings_ui_component.py`).  
- Refactorisation de la configuration (`settings.py`) et de la caméra (`Camera`).  
- Nettoyage général, renommage cohérent des fichiers et suppression des variables globales.  
- Passage des options Tkinter → modale Pygame.  
- Réorganisation de la documentation et des assets.  
- Amélioration de la structure du code et du rendu des sprites.

### ⚡ Perf

- Suppression automatique des projectiles en bord de carte pour éviter leur persistance.  
- Ajout d’un component dédié aux projectiles pour un traitement plus léger.
