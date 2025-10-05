# Vue d'ensemble technique

Bienvenue dans la documen## 📚 Pour aller plus loin

### Architecture et systèmes
- [Architecture ECS](architecture.md) - Structure Entity-Component-System
- [Composants](modules/components.md) - Tous les composants du jeu
- [Processeurs](modules/processors.md) - Logique et systèmes de jeu
- [Système de Tours](tower-system-implementation.md) - Implémentation des tours défensives

### Configuration et développement
- [Configuration](configuration.md) - Installation et configuration
- [Galad Config Tool](galad-config-tool-technical.md) - Détails techniques du tool
- [Mode Debug](debug-mode.md) - Fonctionnalités de développement
- [Guide de contribution](contributing.md) - Comment contribuer
- [Maintenance du projet](maintenance.md) - Gestion du projet

### API et références
- [API du moteur de jeu](api/game-engine.md) - Référence du GameEngine
- [Système de localisation](localization.md) - Traductions et i18n

---

> 💡 *N'hésitez pas à proposer des améliorations ou à signaler des erreurs via des issues ou des pull requests !*chnique de **Galad Islands**.

Cette section s'adresse aux développeurs, contributeurs et curieux souhaitant comprendre l'architecture, les choix techniques et les bonnes pratiques du projet.

---

## 🚀 Objectifs de cette documentation

- Présenter l’architecture générale du projet
- Expliquer l’organisation des modules et des dossiers
- Décrire les principaux composants techniques (moteur de jeu, interface, gestionnaires, etc.)
- Donner les clés pour contribuer efficacement au code
- Centraliser les conventions et outils utilisés

---

## 🗂️ Structure du projet

Le projet est organisé selon les grands dossiers suivants :

- `src/` : Code source principal du jeu
    - `components/` : Composants du jeu (carte, caméra, unités, etc.)
    - `managers/` : Gestionnaires (affichage, audio, événements…)
    - `settings/` : Paramètres, configuration, localisation
    - `ui/` : Composants d’interface utilisateur réutilisables
    - `game/` : Logique principale du jeu
- `assets/` : Ressources (images, sons, traductions…)
- `docs/` : Documentation utilisateur et technique
- `tests/` : Tests unitaires et d’intégration

---

## 🛠️ Technologies principales

- **Python 3.10+**
- **Pygame** (affichage, gestion des entrées)
- **MkDocs** (documentation)
- **Git** (gestion de version)
- `requirements.txt` (gestion des dépendances)

---

## 📐 Principes d’architecture

- **Modularité** : chaque composant a une responsabilité claire
- **Séparation UI / logique** : l’interface utilisateur est découplée de la logique du jeu
- **Extensibilité** : le code est pensé pour faciliter l’ajout de nouvelles fonctionnalités
- **Internationalisation** : support multilingue via le module `localization`

---

## 📚 Pour aller plus loin

- [API du moteur de jeu](api/game-engine.md)
- [Guide de contribution](contributing.md)
- [Maintenance du projet](maintenance.md)

---

> 💡 *N’hésitez pas à proposer des améliorations ou à signaler des erreurs via des issues ou des pull requests !*