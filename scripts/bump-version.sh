#!/bin/bash
# Script de bump de version local pour Galad Islands
# Usage: ./scripts/bump-version.sh [patch|minor|major|auto]

set -e

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Galad Islands - Bump de version local${NC}"

# S'assurer qu'on est dans le bon répertoire
cd "$(dirname "$0")/.."

# Vérifier que l'environnement virtuel est activé
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  Activation de l'environnement virtuel...${NC}"
    source venv/bin/activate
fi

# Vérifier que commitizen est installé
if ! python -m commitizen version &>/dev/null; then
    echo -e "${RED}❌ Commitizen n'est pas installé dans l'environnement virtuel${NC}"
    echo "Installez-le avec: pip install commitizen"
    exit 1
fi

# Branche cible (optionnel: 2ème argument) — default: main
TARGET_BRANCH="${2:-main}"
echo -e "${YELLOW}📥 Mise à jour de la branche ${TARGET_BRANCH}...${NC}"
git checkout "${TARGET_BRANCH}"
git pull origin "${TARGET_BRANCH}"

# Déterminer le type de bump
BUMP_TYPE="${1:-auto}"

echo -e "${YELLOW}🔍 Vérification des commits depuis le dernier tag...${NC}"

# Vérifier s'il y a des commits nécessitant un bump
LAST_TAG=$(git tag --sort=-version:refname | head -1)
if [ -n "$LAST_TAG" ]; then
    echo "Dernier tag: $LAST_TAG"
    
    # Compter les commits depuis le dernier tag
    COMMITS_COUNT=$(git log $LAST_TAG..HEAD --oneline | wc -l)
    
    if [ "$COMMITS_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}ℹ️  Aucun nouveau commit depuis le dernier tag${NC}"
        exit 0
    fi
    
    echo "Commits depuis $LAST_TAG:"
    git log $LAST_TAG..HEAD --oneline --color=always
    
    # Détecter automatiquement le type de bump si demandé
    if [ "$BUMP_TYPE" = "auto" ]; then
        if git log $LAST_TAG..HEAD --oneline | grep -E "^[a-f0-9]+ (feat|feat\(.*\))"; then
            BUMP_TYPE="minor"
            echo -e "${GREEN}🔍 Détection automatique: MINOR (nouvelles fonctionnalités)${NC}"
        elif git log $LAST_TAG..HEAD --oneline | grep -E "^[a-f0-9]+ (fix|perf|fix\(.*\)|perf\(.*\))"; then
            BUMP_TYPE="patch"
            echo -e "${GREEN}🔍 Détection automatique: PATCH (corrections/améliorations)${NC}"
        else
            BUMP_TYPE="patch"
            echo -e "${GREEN}🔍 Détection automatique: PATCH (par défaut)${NC}"
        fi
    fi
else
    echo "Aucun tag trouvé, création du tag initial"
    BUMP_TYPE="patch"
fi

echo -e "${YELLOW}📦 Bump de version ($BUMP_TYPE)...${NC}"

# Effectuer le bump
if [ "$BUMP_TYPE" = "auto" ]; then
    # Laisser commitizen décider
    if python -m commitizen bump --yes --changelog; then
        echo -e "${GREEN}✅ Bump automatique réussi${NC}"
    else
        echo -e "${YELLOW}⚠️  Échec du bump automatique, tentative manuelle...${NC}"
        python -m commitizen bump --increment patch --yes --changelog
    fi
else
    # Bump manuel avec type spécifié
    python -m commitizen bump --increment "$BUMP_TYPE" --yes --changelog
fi

# Vérifier que le tag a été créé
NEW_TAG=$(git tag --sort=-version:refname | head -1)
echo -e "${GREEN}🏷️  Nouveau tag créé: $NEW_TAG${NC}"

# Afficher les changements
echo -e "${YELLOW}📝 Résumé des changements:${NC}"
git log --oneline -3

# Demander confirmation avant push
echo -e "${YELLOW}❓ Voulez-vous pousser les changements vers GitHub ? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}📤 Push des changements et tags...${NC}"
    git push origin "${TARGET_BRANCH}"
    git push origin --tags

    echo -e "${GREEN}✅ Version $NEW_TAG publiée avec succès !${NC}"
    echo -e "${GREEN}🎯 La release automatique devrait se déclencher sur GitHub Actions${NC}"
else
    echo -e "${YELLOW}⏸️  Push annulé. Les changements sont prêts localement.${NC}"
    echo "Pour pousser plus tard: git push origin ${TARGET_BRANCH} && git push origin --tags"
fi