# Workflow de Développement - Galad Islands

## 📋 Processus de Développement

### 1. Méthodologie Agile Adaptée

#### Sprints de 2 semaines
- **Planning** : Lundi début de sprint
- **Daily meetings** : Tous les jours à 10h (15 min max)
- **Review** : Vendredi fin de sprint
- **Retrospective** : Vendredi après review

#### Rôles de l'équipe
- **Behani Julien** : Lead Technique + IA/Systèmes
- **Fournier Enzo** : Gameplay + Mécaniques de jeu  
- **Alluin Edouard** : Graphics/UI + Audio

### 2. Workflow Git Détaillé

#### Structure des branches
```
main (production)
├── develop (intégration)
├── feature/nom-fonctionnalite
├── hotfix/correction-urgente
└── release/version-x.x.x
```

#### Convention de nommage des branches
- `feature/ai-pathfinding-astar` : Nouvelle fonctionnalité
- `bugfix/collision-detection-bug` : Correction de bug
- `hotfix/crash-at-startup` : Correction critique
- `refactor/optimize-rendering` : Refactorisation
- `docs/update-readme` : Documentation

#### Process de développement
```bash
# 1. Récupérer les derniers changements
git checkout develop
git pull origin develop

# 2. Créer une branche feature
git checkout -b feature/ai-behavior-trees

# 3. Développer avec commits atomiques
git add src/ai/behavior_trees.py
git commit -m "feat(ai): ajouter nœuds de base pour arbres de comportement"

git add tests/test_behavior_trees.py  
git commit -m "test(ai): ajouter tests unitaires pour arbres comportement"

# 4. Push et création PR
git push origin feature/ai-behavior-trees
# Créer Pull Request sur GitHub

# 5. Après review et merge, nettoyer
git checkout develop
git pull origin develop
git branch -d feature/ai-behavior-trees
```

### 3. Conventions de Commit

#### Format obligatoire
```
type(scope): description courte

Corps du commit optionnel avec plus de détails.

Closes #123
```

#### Types de commit
- **feat** : Nouvelle fonctionnalité
- **fix** : Correction de bug
- **docs** : Documentation
- **style** : Formatage/style (pas de changement de code)
- **refactor** : Refactorisation sans changement de fonctionnalité
- **test** : Ajout/modification de tests
- **perf** : Optimisation de performance
- **chore** : Tâches de maintenance

#### Scopes recommandés
- **core** : Moteur principal
- **ai** : Intelligence artificielle
- **graphics** : Rendu et graphismes
- **ui** : Interface utilisateur
- **world** : Génération monde/cartes
- **entities** : Unités et objets du jeu
- **config** : Configuration

#### Exemples
```bash
feat(ai): implémenter algorithme A* pour pathfinding
fix(graphics): corriger scintillement des sprites lors du zoom
docs(readme): mettre à jour instructions d'installation
perf(entities): optimiser boucle de mise à jour des unités avec NumPy
test(world): ajouter tests pour génération procédurale de cartes
```

### 4. Code Review Process

#### Checklist obligatoire
- [ ] Code respecte les règles définies (commentaires français, etc.)
- [ ] Tests unitaires ajoutés/mis à jour
- [ ] Documentation mise à jour si nécessaire
- [ ] Pas de régression sur tests existants
- [ ] Performance mesurée si impact attendu
- [ ] Pas de code mort ou de TODO en production

#### Template Pull Request
```markdown
## 📝 Description
Brève description des changements apportés.

## 🔧 Type de changement
- [ ] 🆕 Nouvelle fonctionnalité
- [ ] 🐛 Correction de bug
- [ ] ⚡ Optimisation performance
- [ ] 📚 Documentation
- [ ] 🔨 Refactorisation

## 🧪 Tests
- [ ] Tests unitaires ajoutés/mis à jour
- [ ] Tests d'intégration validés
- [ ] Tests manuels effectués
- [ ] Performance benchmarkée si applicable

## 📈 Performance
- [ ] Pas d'impact performance
- [ ] Amélioration mesurée: +XX% FPS
- [ ] Régression acceptable: -XX% justifiée par...

## 📱 Screenshots/Vidéos
[Si applicable - captures d'écran des changements visuels]

## ✅ Checklist finale
- [ ] Code en français selon règles projet
- [ ] Pas de console.log/print en production
- [ ] Variables/fonctions nommées explicitement
- [ ] Optimisations NumPy appliquées si pertinent
```

### 5. Gestion des Issues

#### Labels recommandés
- **Priority**: `P0-Critical`, `P1-High`, `P2-Medium`, `P3-Low`
- **Type**: `bug`, `feature`, `enhancement`, `documentation`
- **Scope**: `ai`, `graphics`, `ui`, `performance`, `core`
- **Status**: `needs-triage`, `in-progress`, `blocked`, `ready-for-review`

#### Template Issue Bug
```markdown
## 🐛 Description du bug
Description claire et concise du problème.

## 🔄 Étapes de reproduction
1. Aller à '...'
2. Cliquer sur '...'
3. Voir erreur

## 📱 Comportement attendu
Description du comportement normal attendu.

## 📷 Screenshots/Logs
[Captures d'écran ou logs d'erreur]

## 🖥️ Environnement
- OS: Windows 10
- Python: 3.9.7
- Pygame: 2.5.0
- Commit: abc1234

## ℹ️ Informations additionnelles
Contexte supplémentaire ou détails techniques.
```

#### Template Issue Feature
```markdown
## 🚀 Fonctionnalité demandée
Description claire de la fonctionnalité souhaitée.

## 🎯 Problème résolu
Quel problème cette fonctionnalité résout-elle ?

## 💡 Solution proposée
Description de la solution envisagée.

## 🔄 Alternatives considérées
Autres approches évaluées.

## ✅ Critères d'acceptation
- [ ] Critère 1
- [ ] Critère 2
- [ ] Critère 3

## 📊 Impact estimé
- **Performance**: Aucun/Faible/Moyen/Élevé
- **Complexité**: Faible/Moyenne/Élevée
- **Priorité**: P0/P1/P2/P3
```

### 6. Gestion des Releases

#### Versioning Sémantique
- **MAJOR.MINOR.PATCH** (ex: 1.2.3)
- **MAJOR** : Changements incompatibles
- **MINOR** : Nouvelles fonctionnalités compatibles
- **PATCH** : Corrections de bugs

#### Process de release
```bash
# 1. Créer branche release
git checkout develop
git checkout -b release/v0.2.0

# 2. Préparer la release
# - Mettre à jour version dans config.py
# - Mettre à jour CHANGELOG.md
# - Tests finaux

# 3. Merger dans main
git checkout main
git merge release/v0.2.0
git tag v0.2.0

# 4. Merger dans develop
git checkout develop
git merge release/v0.2.0

# 5. Nettoyer
git branch -d release/v0.2.0
```

### 7. Outils de Développement

#### IDE Configuration (VS Code)
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.testing.pytestEnabled": true,
    "files.associations": {
        "*.py": "python"
    },
    "editor.rulers": [80, 100],
    "editor.formatOnSave": true
}
```

#### Pre-commit hooks
```bash
# Installation
pip install pre-commit
pre-commit install

# .pre-commit-config.yaml
repos:
-   repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
    -   id: black
-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
```

### 8. Tests et Qualité

#### Stratégie de tests
- **Tests unitaires** : Chaque fonction/classe
- **Tests d'intégration** : Systèmes combinés
- **Tests de performance** : Fonctions critiques
- **Tests manuels** : Gameplay et UI

#### Commandes de test
```bash
# Tests rapides (unitaires)
python -m pytest tests/unit/ -v

# Tests complets
python -m pytest tests/ -v --cov=src

# Tests de performance
python -m pytest tests/performance/ --benchmark-only

# Tests avec coverage HTML
python -m pytest --cov=src --cov-report=html tests/
```

#### Métriques qualité
- **Coverage code** : >80% minimum
- **Performance** : Pas de régression >5%
- **Complexité cyclomatique** : <10 par fonction
- **Documentation** : Toutes les fonctions publiques

### 9. Communication et Coordination

#### Daily Meetings Structure
1. **Ce que j'ai fait hier** (2 min max)
2. **Ce que je vais faire aujourd'hui** (2 min max)  
3. **Blocages ou questions** (1 min max)

#### Sprint Planning
- **Estimation** : Story points (1,2,3,5,8,13)
- **Capacity** : 40 story points par sprint par personne
- **Buffer** : 20% pour imprévus et bugs

#### Documentation partagée
- **Confluence/Notion** : Spécifications détaillées
- **GitHub Wiki** : Documentation technique
- **README** : Information générale et setup
- **Inline code** : Documentation de l'API

### 10. Gestion des Conflits Git

#### Résolution de conflits
```bash
# 1. Récupérer les derniers changements
git fetch origin

# 2. Rebase interactif pour nettoyer l'historique
git rebase -i origin/develop

# 3. Résoudre les conflits manuellement
# Éditer les fichiers en conflit
git add fichier_resolu.py
git rebase --continue

# 4. Force push si nécessaire (ATTENTION : seulement sur sa branche)
git push --force-with-lease origin feature/ma-branche
```

#### Prévention des conflits
- **Communication** : Annoncer les gros refactorings
- **Commits atomiques** : Petits commits fréquents
- **Rebase régulier** : Rester à jour avec develop
- **Code modulaire** : Éviter de toucher aux mêmes fichiers

---

*Document maintenu par l'équipe de développement Galad Islands*
*Dernière mise à jour : Décembre 2024*