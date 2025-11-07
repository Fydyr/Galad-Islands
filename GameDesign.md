# Game Design Document

---

## 1. Conceptualisation

### Idée du jeu

> Il s’agit d’un jeu de stratégie en temps réel où le but est de combattre votre adversaire tout en dominant les îles de Galad, c'est-à-dire détruire la base adverse tout en défendant la sienne.

### La vision

- **Public cible** : 12 ans et plus (adolescents, adultes)
- **Style** : Stratégie, réflexion, fantasy, rétro gaming
- **Univers** : Monde fantastique, batailles épiques

---

## 2. Gameplay et mécaniques

### Règles du jeu

- Combat contre une IA pour détruire la base adverse
- Ressources initiales égales, à collecter sur des îlots ou via des événements aléatoires (ex : coffres volants)
- Création de troupes contre ressources
- Jeu en temps réel, déplacement libre sur le plateau
- Contrôle des unités par IA par défaut, possibilité de reprendre le contrôle
- Différents types d’unités avec capacités spéciales
- Champ de vision propre à chaque unité
- Événements aléatoires (tempêtes, etc.) pouvant affecter les deux camps

### Contrôles & Interactions

- **Stratégie** : Achat de troupes, gestion des ressources
- **Contrôle** : 
    - Achat d’unités : clic gauche (si or suffisant)
    - Déplacement de la vue : maintien clic gauche
    - Déplacement des unités : ZQSD ou flèches directionnelles
    - Attaque : clic droit sur unité ennemie + bouton boulet de canon (clic gauche)
- **Modes de contrôle** : IA ou contrôle manuel d’un bateau

---

### Troupes

| Nom        | Type        | Coût | Vitesse | Dégâts | Radius | Rechargement | Armure | Capacité spéciale | Description |
|------------|-------------|------|---------|--------|--------|--------------|--------|-------------------|-------------|
| **Zasper** | Scout (léger) | 10 gold | 5/s | 10-15 | 5 cases | 1 s | 60 | Manœuvre d’évasion (invincibilité 3s) | Reconnaissance, frappes rapides, tir avant uniquement |
| **Barhamus** | Maraudeur (moyen) | 20 gold | 3.5/s | 20-30 (salve), 10-15 (boulet) | 7 cases | 2 s | 130 | Bouclier de mana (réduction 20-45%) | Polyvalent, tir avant et côtés |
| **Draupnir** | Léviathan (lourd) | 40 gold | 2/s | 40-60 (salve), 15-20 (boulet) | 10 cases | 4.5 s | 300 | Seconde salve | Armure épaisse, trois canons de chaque côté |
| **Druid** | Support | 30 gold | 4/s | 0 | 7 cases | 4 s | 100 | Lierre volant (immobilisation 5s), soin | Soigne alliés, bloque ennemis |
| **Architect** | Support | 30 gold | 4/s | 0 | 0 (sur île) | 0 | 100 | Rechargement automatique (radius 8 cases) | Construction de tours de défense/régénération |

---

#### Autres éléments

- **Mines volantes** : Dégâts 40, pièges aléatoires sur la carte
- **Tour de défense** : Dégâts 25, radius 8 cases, armure 70, rechargement 10s
- **Tour de soin** : PV soigné 15, radius 5 cases, armure 70, rechargement 10s

---

#### Événements

| Événement            | Type   | Chance | Effet/Dégâts | Radius | Durée | Description |
|----------------------|--------|--------|--------------|--------|-------|-------------|
| **Tempêtes**         | Malus  | 15%    | 30           | 4      | 20s   | Attaque toute unité dans le radius |
| **Vague de bandits** | Malus  | 25%    | 20           | 5      | -     | 1 à 6 bateaux bandits attaquent en traversant la carte |
| **Kraken**           | Malus  | 10%    | 70           | -      | -     | 2 à 6 tentacules détruisent tours et ressources |
| **Coffre volant**    | Bonus  | 20%    | 10-20 gold   | -      | 20s   | 2 à 5 coffres, bonus de ressources |

---

### Progression

- **Début** : Peu d’unités, collecte de ressources, choix stratégique initial
- **Milieu** : Multiplication des unités, événements aléatoires, premières confrontations
- **Fin** : Armées nombreuses, capacités spéciales, domination d’îlots stratégiques, destruction de la base adverse

> La progression se fait via un arbre pondéré (ressources, événements, actions adverses). Chaque partie reste imprévisible et unique, mais la stratégie prime sur le hasard.

---

## 3. Narration & univers

### Scénario & environnement

**Contexte**  
Les îles de Galad flottent dans le ciel, abritant le Cristal d’Aerion, source de pouvoir colossal. L’équilibre entre aventuriers et créatures mystiques est rompu par la soif de pouvoir.

**Déclenchement de la guerre**  
La découverte d’une nouvelle veine de Cristal d’Aerion provoque l’attaque de la Légion des Abysses contre la Flotte de l’Aube. Le conflit culmine autour des forteresses “Eryndor” (Flotte de l’Aube) et “Barakdur” (Légion des Abysses).

---

### Factions

#### La Flotte de l’Aube

- **Description** : Coalition d’aventuriers, explorateurs et mages humains
- **Objectif** : Progrès, expansion, sécurité des routes célestes
- **Devise** : "L’horizon nous appartient."
- **Symbole** : Soleil doré derrière un navire ailé

#### La Légion des Abysses

- **Description** : Armée de monstres ailés, vents obscurs
- **Objectif** : Chaos, domination du ciel, destruction de l’ordre
- **Devise** : "Les cieux sont notre tempête."
- **Symbole** : Crâne de dragon noir entouré de chaînes brisées

---

*Chaque partie est une bataille pour la domination des îles et du ciel, entre stratégie, gestion des ressources et adaptation aux événements imprévus.*
