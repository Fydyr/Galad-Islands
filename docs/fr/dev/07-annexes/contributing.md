---
i18n:
  en: "Contribution Guide"
  fr: "Guide de contribution"
---

# Guide de contribution

## Conventions de commit

Le projet utilise la spécification [Conventional Commits 1.0.0](https://www.conventionalcommits.org/) pour garantir un historique de commits lisible et exploitable par des outils automatisés.

### Structure du message de commit

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Composants obligatoires :**

- `type` : Type de modification
- `subject` : Description courte (72 caractères maximum)

**Composants optionnels :**

- `scope` : Portée de la modification (composant, module, fichier)
- `body` : Description détaillée de la modification
- `footer` : Métadonnées (références d'issues, breaking changes)

### Types de commit

| Type | Description | Impact sur versioning |
|------|-------------|----------------------|
| `feat` | Ajout d'une nouvelle fonctionnalité | MINOR |
| `fix` | Correction d'un bug | PATCH |
| `docs` | Modification de la documentation uniquement | - |
| `style` | Modification n'affectant pas la logique (formatage, espaces, indentation) | - |
| `refactor` | Refactorisation sans modification de fonctionnalité | - |
| `perf` | Amélioration des performances | PATCH |
| `test` | Ajout ou modification de tests | - |
| `build` | Modification du système de build ou des dépendances | - |
| `ci` | Modification de la configuration CI/CD | - |
| `chore` | Tâches de maintenance (ne modifie ni src ni test) | - |
| `revert` | Annulation d'un commit précédent | Dépend du commit annulé |

### Règles de rédaction

!!! info Subject
    - Utiliser l'impératif présent ("add" et non "added" ou "adds")
    - Ne pas commencer par une majuscule
    - Ne pas terminer par un point
    - Maximum 72 caractères

!!! info Body
    - Séparer du subject par une ligne vide
    - Expliquer le "quoi" et le "pourquoi", pas le "comment"
    - Maximum 100 caractères par ligne

!!! info Footer
    - Références aux issues : `Refs: #123, #456`
    - Fermeture d'issues : `Closes: #123`
    - Breaking changes : `BREAKING CHANGE: description`

### Exemples

=== "Nouvelle unité"

    ```bash
    feat(units): add Leviathan unit with siege capabilities
    
    Add the Leviathan unit with high health and powerful attacks.
    Includes new sprite assets and unit factory integration.
    
    Closes: #156
    ```

=== "Correction de bug de combat"

    ```bash
    fix(combat): prevent units from attacking through obstacles
    
    Fixed pathfinding issue where units could attack targets
    through solid terrain. Added line-of-sight validation.
    
    Refs: #203
    ```

=== "Refactorisation de la boutique"

    ```bash
    refactor(shop): extract unit pricing logic to gameplay constants
    
    Moved hardcoded unit costs to centralized constants in gameplay.py.
    Improves maintainability and prevents pricing inconsistencies.
    ```

---

## Workflow de contribution

### Prérequis

- Git 2.0+
- Compte GitHub avec accès au dépôt
- Environnement de développement configuré selon le README

### Processus standard

#### 1. Préparation

```bash
# Fork le dépôt via l'interface GitHub

# Clone le fork
git clone https://github.com/Fydyr/Galad-Islands.git
cd <repository>

# Configure le dépôt upstream
git remote add upstream https://github.com/Fydyr/Galad-Islands.git

# Synchronise avec upstream
git fetch upstream
git checkout main
git merge upstream/main
```

#### 2. Création d'une branche

!!! tip Convention de nommage
    ```text
    <type>/<issue-number>-<short-description>
    ```

**Exemples :**

```bash
git checkout -b feat/123-oauth-integration
git checkout -b fix/456-null-pointer-exception
git checkout -b docs/789-api-documentation
```

**Types de branches :**

- `feat/` : Nouvelle fonctionnalité
- `fix/` : Correction de bug
- `docs/` : Documentation
- `refactor/` : Refactorisation
- `test/` : Tests
- `chore/` : Maintenance

#### 3. Commit

```bash
# Ajout des fichiers modifiés
git add <files>

# Commit avec message conventionnel
git commit -m "type(scope): description"

# Vérification
git log --oneline
```

#### 4. Synchronisation

```bash
# Récupération des dernières modifications
git fetch upstream
git rebase upstream/main

# Résolution des conflits si nécessaire
# Puis continuer le rebase
git rebase --continue
```

#### 5. Push et Pull Request

```bash
# Push vers le fork
git push origin <branch-name>
```

!!! note En cas de rebase
    Vérifier si vos modifications ne risquent pas d'écraser des changements des autres contributeurs.

!!! note Création de la Pull Request
    1. Ouvrir l'interface GitHub
    2. Créer une Pull Request depuis la branche du fork vers `main` d'upstream
    3. Remplir le template de PR avec :
        - **Titre** : Résumé clair de la modification
        - **Description** : Contexte et détails techniques
        - **Type de changement** : Feature, Bug fix, etc.
        - **Issues liées** : Références (#123)


---

## Standards de code

### Principes généraux

!!! abstract SOLID
    - Single Responsibility Principle
    - Open/Closed Principle
    - Liskov Substitution Principle
    - Interface Segregation Principle
    - Dependency Inversion Principle

!!! abstract Clean Code
    - Noms explicites et significatifs
    - Fonctions courtes (< 20 lignes)
    - Commentaires uniquement si nécessaire
    - Pas de code dupliqué (DRY)
    - Gestion appropriée des erreurs

### Conventions de nommage

=== "Variables et fonctions"

    ```javascript
    // camelCase pour variables et fonctions
    const userName = 'John';
    function getUserData() { }
    ```

=== "Classes et composants"

    ```javascript
    // PascalCase pour classes et composants
    class UserService { }
    function UserProfile() { }
    ```

=== "Constantes"

    ```javascript
    // UPPER_SNAKE_CASE pour constantes
    const MAX_RETRY_COUNT = 3;
    const API_BASE_URL = 'https://api.example.com';
    ```

=== "Fichiers"

    - Utilitaires : `camelCase.py`

### Tests

!!! success Couverture de code
    - **Minimum requis** : 80%
    - **Objectif** : 90%+

---

## Processus de revue

### Critères d'acceptation

!!! warning Obligatoires
    - [ ] Au moins une revue approuvée d'un mainteneur
    - [ ] Aucun conflit avec la branche cible
    - [ ] Documentation à jour
    - [ ] Couverture de tests satisfaisante

!!! tip Recommandés
    - [ ] Performance évaluée pour les modifications critiques
    - [ ] Accessibilité vérifiée pour les modifications UI
    - [ ] Sécurité analysée pour les modifications sensibles

### Traitement des retours

**Résolution des commentaires :**

1. Lire et comprendre tous les commentaires
2. Appliquer les modifications demandées
3. Répondre aux commentaires pour expliquer les choix
4. Marquer les commentaires comme résolus
5. Demander une nouvelle revue

**Modifications après revue :**

```bash
# Modifier le code
git add <files>

# Commit de correction
git commit -m "fix(scope): address review comments"

# Push
git push origin <branch-name>
```

---

## Contact

!!! question Pour toute question
    Ouvrir une issue avec le label `question`

### Mainteneurs

- [Enzo Fournier](https://github.com/fydyr)
- [Edouard Alluin](https://github.com/AlluinEdouard)
- [Julien Behani](https://github.com/kinator)
- [Ethan Cailliau](https://github.com/ethann59)
- [Alexandre Damman](https://github.com/kaldex0)
- [Romain Lambert](https://github.com/roro627)

---

!!! info Version du document
    **Version** : 1.0.0