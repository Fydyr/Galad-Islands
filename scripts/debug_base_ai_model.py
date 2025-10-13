#!/usr/bin/env python3
"""Script de debug : affiche les Q-values prédites par le modèle self-play pour un état d'exemple."""
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

def find_model():
    for p in MODEL_CANDIDATES:
        if os.path.exists(p):
            return p
    # fallback: scan src/models for pkl
    mdir = os.path.join('src', 'models')
    if os.path.isdir(mdir):
        for f in os.listdir(mdir):
            if f.endswith('.pkl'):
                return os.path.join(mdir, f)
    return None


def main():
    path = find_model()
    if not path:
        print('Aucun modèle trouvé dans src/models/*.pkl')
        return

    print(f'Chargement du modèle : {path}')
    try:
        model = joblib.load(path)
    except Exception as e:
        print('Erreur lors du chargement du modèle :', e)
        return

    print('Type de modèle chargé :', type(model))

    # Exemple d'état (doit correspondre à l'ordre attendu par l'IA)
    state = {
        'gold': 100,
        'base_health_ratio': 1.0,
        'allied_units': 0,
        'enemy_units': 0,
        'enemy_base_known': 0,
        'towers_needed': 0,
        'enemy_base_health_ratio': 1.0,
    }

    features = [
        state['gold'],
        state['base_health_ratio'],
        state['allied_units'],
        state['enemy_units'],
        state['enemy_base_known'],
        state['towers_needed'],
        state['enemy_base_health_ratio'],
    ]

    q_values = []
    for action in range(7):
        input_vec = np.array([features + [action]])
        try:
            q = model.predict(input_vec)
            q_values.append(float(q[0]))
        except Exception as e:
            print(f'Erreur predict pour action {action}:', e)
            q_values.append(None)

    print('\nQ-values par action (index: nom):')
    names = ['Rien', 'Éclaireur', 'Architecte', 'Maraudeur', 'Léviathan', 'Druide', 'Kamikaze']
    for i, q in enumerate(q_values):
        print(f' {i:02d} ({names[i]}): {q}')

    # Afficher l'ordre d'actions triées par Q décroissant
    valid = [(i, q) for i, q in enumerate(q_values) if q is not None]
    valid_sorted = sorted(valid, key=lambda t: t[1], reverse=True)
    print('\nOrdre des actions par Q décroissant:')
    for i, q in valid_sorted:
        print(f' {i} ({names[i]}): {q}')


if __name__ == '__main__':
    main()
