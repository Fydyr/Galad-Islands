---
i18n:
  en: "📚 Documentation Technique - Galad Islands"
  fr: "📚 Documentation Technique - Galad Islands"
---

# 📚 Galad Islands — Introduction technique

Cette page est l'introduction technique du projet Galad Islands. Elle vise les développeurs, contributeurs et mainteneurs qui ont besoin d'une vue synthétique et pratique du code, de l'architecture et du démarrage.

## Objectifs

- Présenter les objectifs du projet et l'architecture générale
- Fournir un guide de démarrage rapide pour développer localement
- Pointer vers la documentation détaillée (API, systèmes, outils)

## Vue d'ensemble

Galad Islands est un petit jeu de stratégie/temps réel développé en Python. La base de code utilise une architecture Entity-Component-System (ECS) via la bibliothèque `esper` pour séparer les données et la logique. Le rendu et l'entrée sont pris en charge par `pygame`.

Principaux sous-systèmes

- Moteur de jeu : boucle principale, orchestration et cycle de vie
- ECS : composants (données) et systèmes/processors (logique)
- Interface utilisateur : barre d'action, boutique, UI de debug
- Gestionnaires : audio, sprites, événements, configuration
- Outils : utilitaires et éditeur de configuration (`tools/galad_config.py`)

## Démarrage rapide (développeur)

1. Cloner le dépôt :

```bash
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands
```

1. Créer et activer un environnement virtuel (Linux/macOS) :

```bash
python3 -m venv venv
source venv/bin/activate
```

1. Installer les dépendances :

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

1. Lancer le jeu :

```bash
python main.py
```

## Structure du projet (dossiers importants)

```text
src/                  # Code source du jeu
  components/         # Composants ECS
  systems/            # Systems modernes
  Processors/         # Processors legacys (esper)
  ui/                 # Widgets et écrans UI
  managers/           # Gestionnaires (audio, events...)
assets/               # Images, sons et fichiers de locale
docs/                 # Documentation (mkdocs)
tools/                # Outils et éditeur de configuration
```

## Où lire ensuite

- API et internals : `docs/en/dev/02-systeme/`
- Configuration & localisation : `docs/en/dev/04-Configuration/`
- Exploitation & déploiement : `docs/en/dev/05-exploitation/`

## Contribution & support

- Utilisez la branche `unstable` pour le travail en cours et ouvrez des PRs vers `main` lorsqu'elles sont prêtes.
- Suivez les règles de Conventional Commits décrites dans `docs/en/dev/07-annexes/contributing.md`.
- Pour de l'aide rapide, ouvrez une issue ou une discussion sur GitHub.

---

> 💡 Vous souhaitez une page d'accueil plus courte (checklist développeur) ? Dites-moi quelles sections garder et je la réduis.
