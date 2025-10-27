---
i18n:
  en: "Version Management"
  fr: "Gestion des versions"
---

# Version Management

## 🎯 Objective

This document explains how to manage versions for the Galad Islands project using a manual version management system.

### How to Manage Versions Manually

1. **Activate the Virtual Environment**:

   ```bash
   source venv/bin/activate  # Unix/Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Ensure you are up-to-date**:

   ```bash
   git checkout main && git pull origin main
   ```

3. **Perform the bump**:

   ```bash
   python -m commitizen bump --increment patch --yes --changelog
   ```

4. **Push the changes**:

   ```bash
   git push origin main && git push origin --tags
   ```

### Commit Types and Their Impact

- ✅ **feat**: new feature → **minor** bump
- ✅ **fix**: bug fix → **patch** bump
- ✅ **perf**: performance improvement → **patch** bump
- ✅ **refactor**: refactoring → **patch** bump
- ❌ **docs**, **style**, **test**, **chore**, **ci**: no bump

## 🔄 Recommended Workflow

1. **Initial setup**: `python setup_dev.py` (only once)
2. **Normal development**: Commits with conventional messages
3. **Manual bump**: Use Commitizen to manage versions
4. **Push with tags**: `git push origin main && git push origin --tags`

## 🚫 Removal of Pre-commit Hooks

> **⚠️ Warning: Hooks Removed**
>
> The automatic bump system via pre-commit hooks has been **disabled**. Versions must now be managed manually.
>
> - ✅ **New**: Manual version management
> - 🔄 **Legacy**: Hooks are no longer installed by default
>

## 🎯 Advantages of This Approach

- ✅ **Total control**: You decide when to make a release
- ✅ **No sync issues**: Tags are created and pushed together
- ✅ **Consistent changelog**: Generated locally with the full history
- ✅ **Confirmation**: Ability to verify before publishing
- ✅ **Easy rollback**: Reversal is possible before pushing

## 🔍 Troubleshooting

### Installation and tests

```bash
# Reinstall Commitizen
python -m pip install commitizen

# Check Commitizen
python -m commitizen Version
```

### Problèmes courants

```bash
# Environment Virtual non Activated
source venv/bin/activate  # Unix/Linux/macOS
# ou
venv\Scripts\activate     # Windows
```
