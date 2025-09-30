# Guide de démarrage

## 📋 Prérequis système

### Configuration minimale
- **Système d'exploitation** : Windows 10, macOS 10.14, ou Linux Ubuntu 18.04+
- **Python** : Version 3.8 ou supérieure
- **RAM** : 4 GB minimum
- **Espace disque** : 500 MB d'espace libre
- **Résolution** : 1024x768 minimum (1920x1080 recommandée)

### Dépendances Python
- pygame >= 2.0.0
- Les autres dépendances sont listées dans `requirements.txt`

## 🔧 Installation

### 1. Cloner le projet
```bash
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv

# Sur Windows
venv\Scripts\activate

# Sur macOS/Linux
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Lancer le jeu
```bash
python main.py
```

## 🎮 Premier lancement

### Menu principal
Au lancement, vous arrivez sur le menu principal avec les options :

- **Jouer** : Commencer une nouvelle partie
- **Options** : Configurer les paramètres
- **Aide** : Consulter l'aide intégrée
- **Crédits** : Voir l'équipe de développement
- **Quitter** : Fermer le jeu

### Configuration initiale

!!! tip "Conseil"
    Avant votre première partie, visitez le menu **Options** pour :
    
    - Ajuster la résolution d'écran
    - Configurer le volume sonore
    - Choisir votre langue (français/anglais)
    - Tester les contrôles

## 🏁 Votre première partie

### 1. Comprendre l'interface
- **Vue carte** : Vue d'ensemble de l'archipel
- **Caméra libre** : Déplacez-vous avec les flèches
- **Zoom** : Molette de souris pour zoomer/dézoomer
- **Barre d'action** : En bas de l'écran

### 2. Contrôles de base
| Touche | Action |
|--------|--------|
| ⬅️➡️⬆️⬇️ | Déplacer la caméra |
| `1-9` | Sélectionner une unité |
| `B` | Ouvrir la boutique |
| `Échap` | Menu/Retour |

### 3. Premiers objectifs
1. **Explorez** la carte avec les flèches directionnelles
2. **Repérez** les îles, mines, et coffres d'or
3. **Sélectionnez** vos unités avec les touches numériques
4. **Collectez** de l'or en vous déplaçant dessus
5. **Achetez** de nouvelles unités dans la boutique (`B`)

### 4. Combat de base
- Sélectionnez une unité avec `1-9`
- Approchez-vous des ennemis
- Les unités attaquent automatiquement
- Utilisez `R` pour les capacités spéciales

## 🎯 Conseils pour débuter

!!! success "Stratégie débutant"
    **Phase d'exploration (5 premières minutes)**
    
    1. Explorez toute la carte
    2. Localisez les sources d'or
    3. Identifiez les positions ennemies
    4. Planifiez votre stratégie

!!! warning "Erreurs courantes"
    **À éviter :**
    
    - Attaquer sans reconnaissance
    - Négliger l'économie
    - Oublier les capacités spéciales
    - Disperser ses forces

## 🆘 Résolution de problèmes

### Le jeu ne se lance pas
1. Vérifiez que Python 3.8+ est installé
2. Assurez-vous que l'environnement virtuel est activé
3. Réinstallez les dépendances : `pip install -r requirements.txt`

### Problèmes d'affichage
1. Ajustez la résolution dans **Options**
2. Testez le mode fenêtré vs plein écran
3. Vérifiez les pilotes graphiques

### Performance lente
1. Fermez les autres applications
2. Réduisez la résolution
3. Vérifiez la configuration système minimale

### Audio ne fonctionne pas
1. Vérifiez le volume système
2. Testez les paramètres audio dans **Options**
3. Redémarrez le jeu

---

*Maintenant que le jeu est installé, découvrez les [contrôles détaillés](controls.md) !*