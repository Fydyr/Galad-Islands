#!/usr/bin/env python3
"""Inspecte un DecisionTreeRegressor self-play et affiche ses métadonnées.
Affiche : profondeur, nombre de feuilles, importances des features, et indices de features utilisées.
"""
import os
import joblib
import numpy as np

MODEL_CANDIDATES = [
    "src/models/base_ai_selfplay_final.pkl",
    "src/models/base_ai_selfplay_iter_3.pkl",
    "src/models/base_ai_selfplay_iter_2.pkl",
    "src/models/base_ai_selfplay_iter_1.pkl",
    "src/models/base_ai_model.pkl",
]

FEATURE_NAMES = [
    'gold',
    'base_health_ratio',
    'allied_units',
    'enemy_units',
    'enemy_base_known',
    'towers_needed',
    'enemy_base_health_ratio',
    'action_index'
]


def find_model():
    for p in MODEL_CANDIDATES:
        if os.path.exists(p):
            return p
    mdir = os.path.join('src', 'models')
    if os.path.isdir(mdir):
        for f in os.listdir(mdir):
            if f.endswith('.pkl'):
                return os.path.join(mdir, f)
    return None


def main():
    path = find_model()
    if not path:
        print('Aucun modèle trouvé.')
        return

    print(f'Chargement du modèle : {path}')
    model = joblib.load(path)
    print('Type de modèle chargé :', type(model))

    try:
        depth = model.get_depth()
        n_leaves = model.get_n_leaves()
        print(f'Dépendance arbre: profondeur={depth}, feuilles={n_leaves}')
    except Exception:
        print('Le modèle ne semble pas être un DecisionTree ou n'"'"'a pas ces attributs.')

    try:
        importances = model.feature_importances_
        print('\nImportances des features :')
        for i, imp in enumerate(importances):
            name = FEATURE_NAMES[i] if i < len(FEATURE_NAMES) else f'feature_{i}'
            print(f' {i}: {name}: {imp:.6f}')

        # Inspecter les indices des features utilisées dans le tree
        tree = model.tree_
        used_features = set(tree.feature[tree.feature >= 0])
        print('\nIndices de features utilisées (non-leaf):', sorted(list(used_features)))
        print('Noms des features utilisées:')
        for idx in sorted(list(used_features)):
            print(' ', idx, FEATURE_NAMES[idx] if idx < len(FEATURE_NAMES) else f'feature_{idx}')

    except Exception as e:
        print("Erreur lors de l'inspection des features:", e)

    # Test prédictions pour un état de base et variations
    base_state = [100, 1.0, 0, 0, 0, 0, 1.0]
    print('\nPrédictions pour l\'état de base (gold=100,..) par action:')
    for action in range(7):
        x = np.array([base_state + [action]])
        try:
            q = model.predict(x)[0]
            print(f' action {action}: {q}')
        except Exception as e:
            print(' predict error action', action, e)

    # Vérifier si toutes les Q sont identiques (approx)
    qs = [model.predict(np.array([base_state + [a]]))[0] for a in range(7)]
    if max(qs) - min(qs) < 1e-9:
        print('\nConstat: toutes les Q-values sont identiques pour cet état (diff < 1e-9).')
        print('Proposition: lors de la phase d\'inférence, si toutes les Q sont égales, appliquer un tie-breaker heuristique (préférer action abordable non nulle).')

if __name__ == '__main__':
    main()
