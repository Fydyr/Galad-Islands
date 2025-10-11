---
i18n:
  en: "Maintenance"
  fr: "🛠️ Maintenance du projet"
---

# 🛠️ Maintenance du projet

Cette page décrit les bonnes pratiques et procédures pour assurer la pérennité et la qualité du projet **Galad Islands**.

---

## 🚦 Stratégie de maintenance

- **Mises à jour fréquentes** : chaque nouvelle fonctionnalité ou correction de bug doit donner lieu à un commit. Privilégiez de petits commits fréquents pour faciliter le suivi et la restauration.
- **Branches dédiées** : pour toute fonctionnalité majeure, créez une branche dédiée avant de fusionner dans la branche principale.
- **Commits clairs** : les messages de commit doivent être explicites et suivre la [convention de commit](../07-annexes/contributing.md#conventions-de-commit).

---

## 📦 Gestion des dépendances

- Les dépendances sont gérées via le fichier `requirements.txt`. Maintenez-le à jour avec les versions compatibles.
- Avant d’ajouter une nouvelle dépendance, vérifiez sa nécessité et l’absence de conflit avec les dépendances existantes.
- **Utilisez un environnement virtuel** pour isoler les dépendances du projet :

    ```bash
    python -m venv env
    source env/bin/activate  # Sur Windows : env\Scripts\activate
    pip install -r requirements.txt
    ```

    > 💡 Les IDE comme VSCode ou PyCharm peuvent automatiser la création et l’activation de l’environnement virtuel.

!!! info "Mise à jour des dépendances"
    Pour mettre à jour les dépendances, modifiez le fichier [requirements.txt](http://_vscodecontentref_/0) puis exécutez :
    ```bash
    pip install -r requirements.txt
    ```

---

## 💾 Sauvegarde et restauration

- **Sauvegardes régulières** : utilisez Git pour versionner le code source et les ressources.
- **Restauration** : en cas de problème, revenez à une version stable avec :
    ```bash
    git checkout <commit_id>
    # ou pour annuler un commit
    git revert <commit_id>
    ```
- **Configuration** : le fichier [galad_config.json](http://_vscodecontentref_/1) contient la configuration du jeu. Sauvegardez-le ou supprimez-le avant des modifications majeures.

---

## ✅ Bonnes pratiques de maintenance

- **Communiquez** avec l’équipe pour coordonner la maintenance et éviter les conflits.
- **Automatisez** les tâches répétitives avec des scripts ou outils adaptés.
- **Intégration continue** : utilisez des outils de CI pour automatiser tests et déploiements.
- **Documentation à jour** : assurez-vous que la documentation reflète toujours l’état du projet.

---

## 📊 Profilage des performances avec cProfile

Le projet inclut un outil de profilage intégré utilisant `cProfile` pour analyser les performances du jeu en temps réel.

### 🚀 Utilisation du profiler

Pour profiler une session de jeu complète :

```bash
python profile_game.py
```

Le profiler :
- **Enregistre** toutes les performances pendant votre partie
- **Analyse** les fonctions les plus lentes automatiquement
- **Génère** un rapport détaillé des 30 fonctions les plus gourmandes
- **Sauvegarde** les résultats complets dans `profile_results.prof`

### 📈 Interprétation des résultats

Le rapport affiche :
- **`cumulative`** : Temps total passé dans la fonction et ses sous-fonctions
- **`percall`** : Temps moyen par appel de fonction
- **`ncalls`** : Nombre d'appels à la fonction

!!! tip "Conseils d'optimisation"
    - Concentrez-vous sur les fonctions avec le plus haut temps `cumulative`
    - Vérifiez les appels fréquents (haut `ncalls`)
    - Optimisez les boucles et calculs mathématiques intensifs

### 🔧 Analyse avancée

Pour une analyse interactive des résultats sauvegardés :

```bash
python -m pstats profile_results.prof
```

Commandes utiles dans l'interpréteur pstats :
- `sort cumulative` : Trier par temps cumulé
- `sort tottime` : Trier par temps propre à la fonction
- `stats 20` : Afficher les 20 premières fonctions

!!! info "Bonnes pratiques de profilage"
    - Profilez des sessions de jeu réalistes (2-5 minutes)
    - Comparez les résultats avant/après optimisation
    - Utilisez le profilage pour identifier les goulots d'étranglement

---

> Pour toute question ou suggestion, n’hésitez pas à ouvrir une issue ou une pull request sur le dépôt GitHub.