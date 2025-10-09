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

> Pour toute question ou suggestion, n’hésitez pas à ouvrir une issue ou une pull request sur le dépôt GitHub.