# Maintenance du projet

> 🚧 **Section en cours de rédaction**


## Stratégie de maintenance

- Les mises à jours sont effectués à chaque nouvelle fonctionnalité ou correction de bug. Il est conseillé de réaliser des petits commits fréquents pour faciliter le suivi des modifications et la restauration en cas de problème.
- En cas de fonctionnalité majeure, une branche dédiée est créée pour permettre un développement isolé avant la fusion dans la branche principale.
- Les commits doivent être clairs et descriptifs pour faciliter la compréhension des modifications apportées. Pour en savoir plus, consultez la section [Conventions de commit](contributing.md).

## Gestion des dépendances

- Les dépendances sont gérées via un fichier `requirements.txt`. Il est important de maintenir ce fichier à jour avec les versions compatibles des bibliothèques utilisées.
- Avant d'ajouter une nouvelle dépendance, vérifiez qu'elle est bien nécessaire et qu'elle n'entre pas en conflit avec les dépendances existantes.
- Utilisez un environnement virtuel pour isoler les dépendances du projet et éviter les conflits avec d'autres projets. Vous pouvez réaliser ceci en faisant :
  ```bash
  python -m venv env
  source env/bin/activate  # Sur Windows : env\Scripts\activate
  pip install -r requirements.txt
  ```

  Des IDE comme VSCode ou PyCharm peuvent automatiser la création et l'activation de l'environnement virtuel.

!!! info "Mise à jour des dépendances"
    Pour mettre à jour les dépendances, modifiez le fichier `requirements.txt` avec les nouvelles versions souhaitées, puis exécutez :
    ```bash
    pip install -r requirements.txt
    ```


## Sauvegarde et restauration

- Il est recommandé de faire des sauvegardes régulières du code source et des ressources du projet. Utilisez un système de contrôle de version comme Git pour suivre les modifications et faciliter la restauration en cas de besoin.
- En cas de problème majeur, utilisez les fonctionnalités de Git pour revenir à une version antérieure stable du projet.
- La configuration du jeu est stockée dans un fichier JSON (`galad_config.json`). Assurez-vous de sauvegarder ce fichier ou de le supprimer avant de faire des modifications majeures.
- Pour restaurer une version précédente du code, utilisez les commandes Git appropriées, telles que `git checkout <commit_id>` ou `git revert <commit_id>`.


## À venir

- Surveillance des performances
- Bonnes pratiques générales

---

*Cette documentation sera complétée prochainement.*


