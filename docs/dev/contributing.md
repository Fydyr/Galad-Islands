# Guide de contribution

## Table des matières

1. [Conventions de commit](#conventions-de-commit)
2. [Workflow de contribution](#workflow-de-contribution)
3. [Standards de code](#standards-de-code)
4. [Processus de revue](#processus-de-revue)
5. [Contact](#contact)

---

## Conventions de commit

Le projet utilise la spécification [Conventional Commits 1.0.0](https://www.conventionalcommits.org/) pour garantir un historique de commits lisible et exploitable par des outils automatisés.

### Structure du message de commit

```
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

**Subject :**
- Utiliser l'impératif présent ("add" et non "added" ou "adds")
- Ne pas commencer par une majuscule
- Ne pas terminer par un point
- Maximum 72 caractères

**Body :**
- Séparer du subject par une ligne vide
- Expliquer le "quoi" et le "pourquoi", pas le "comment"
- Maximum 100 caractères par ligne

**Footer :**
- Références aux issues : `Refs: #123, #456`
- Fermeture d'issues : `Closes: #123`
- Breaking changes : `BREAKING CHANGE: description`

### Exemples

**Commit simple :**
```
feat(auth): add OAuth2 authentication support
```

**Commit avec scope et body :**
```
fix(api): handle null response in user endpoint

The user endpoint was throwing an error when the database
returned null. Added proper null checking and error handling.

Closes: #142
```

**Breaking change :**
```
refactor(api)!: change authentication token format

BREAKING CHANGE: The authentication token format has changed
from JWT to custom format. Clients must update their token
parsing logic.

Refs: #234
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
git clone (https://github.com/Fydyr/Galad-Islands.git)
cd <repository>

# Configure le dépôt upstream
git remote add upstream https://github.com/Fydyr/Galad-Islands.git

# Synchronise avec upstream
git fetch upstream
git checkout main
git merge upstream/main
```

#### 2. Création d'une branche

**Convention de nommage :**
```
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

# En cas de rebase, force push
git push --force-with-lease origin <branch-name>
```

**Création de la Pull Request :**

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

**SOLID :**
- Single Responsibility Principle
- Open/Closed Principle
- Liskov Substitution Principle
- Interface Segregation Principle
- Dependency Inversion Principle

**Clean Code :**
- Noms explicites et significatifs
- Fonctions courtes (< 20 lignes)
- Commentaires uniquement si nécessaire
- Pas de code dupliqué (DRY)
- Gestion appropriée des erreurs

### Conventions de nommage

**Variables et fonctions :**
```javascript
// camelCase pour variables et fonctions
const userName = 'John';
function getUserData() { }
```

**Classes et composants :**
```javascript
// PascalCase pour classes et composants
class UserService { }
function UserProfile() { }
```

**Constantes :**
```javascript
// UPPER_SNAKE_CASE pour constantes
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';
```

**Fichiers :**
- Utilitaires : `camelCase.py`

**Couverture de code :**
- Minimum requis : 80%
- Objectif : 90%+

---

## Processus de revue

### Critères d'acceptation

**Obligatoires :**
- [ ] Au moins une revue approuvée d'un mainteneur
- [ ] Aucun conflit avec la branche cible
- [ ] Documentation à jour
- [ ] Couverture de tests satisfaisante

**Recommandés :**
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

**Pour toute question :**
- Ouvrir une issue avec le label `question`

**Mainteneurs :**
- [Enzo Fournier](https://github.com/fydyr)
- [Edouard Alluin](https://github.com/AlluinEdouard)
- [Julien Behani](https://github.com/kinator)
- [Ethan Cailliau](https://github.com/ethann59)
- [Alexandre Damman](https://github.com/kaldex0)
- [Romain Lambert](https://github.com/roro627)

---

**Version du document :** 1.0.0