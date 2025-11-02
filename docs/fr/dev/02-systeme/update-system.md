---
i18n:
  en: "Update System"
  fr: "Système de mises à jour"
---

# Système de mises à jour

## Vue d'ensemble

Le jeu intègre un système de vérification automatique des mises à jour qui interroge l'API GitHub pour détecter les nouvelles versions publiées.

## Architecture

### Modules

**`src/utils/update_checker.py`**

Module principal de vérification des mises à jour :

- `check_for_updates()` : Vérifie si une mise à jour est disponible (respecte le cache et la config)
- `check_for_updates_force()` : Force la vérification (ignore cache et mode dev)
- `get_current_version()` : Retourne la version actuelle du jeu
- `_should_check_updates()` : Détermine si une vérification doit être effectuée
- `_update_cache()` : Met à jour le fichier cache
- `_get_cached_update_info()` : Récupère les infos depuis le cache

**`src/ui/update_notification.py`**

Widget de notification visuelle :

- Affiche une notification discrète dans le coin supérieur droit
- Deux boutons : "Télécharger" (ouvre GitHub) et "Plus tard" (ferme)
- Gestion des événements souris (hover, clic)
- Rendu avec transparence et animations

### Intégration dans le menu principal

**`main.py`**

Le menu principal lance la vérification de manière asynchrone :

```python
def _check_for_updates_async(self):
    """Vérifie les mises à jour de manière asynchrone."""
    def check_updates():
        update_info = check_for_updates()
        if update_info:
            new_version, release_url = update_info
            current_version = get_project_version()
            self.update_notification = UpdateNotification(
                new_version, 
                current_version, 
                release_url
            )
    
    thread = threading.Thread(target=check_updates, daemon=True)
    thread.start()
```

## Fonctionnement

### 1. Vérification au démarrage

Lorsque le menu principal se lance :

1. Un thread daemon est créé pour ne pas bloquer l'interface
2. `check_for_updates()` est appelée
3. Le système vérifie si la vérification doit être effectuée :
   - Config `check_updates` doit être `true`
   - Mode dev doit être désactivé
   - Cache doit être périmé (>24h) ou inexistant

### 2. Requête GitHub API

Si la vérification est autorisée :

```python
GITHUB_API_URL = "https://api.github.com/repos/Fydyr/Galad-Islands/releases/latest"
response = requests.get(GITHUB_API_URL, timeout=5)
data = response.json()
latest_version = data.get("tag_name", "").lstrip("v")
release_url = data.get("html_url", "")
```

### 3. Comparaison de versions

Utilise le module `packaging` pour comparer sémantiquement :

```python
from packaging import version

if version.parse(latest_version) > version.parse(__version__):
    return (latest_version, release_url)
```

### 4. Mise en cache

Résultat sauvegardé dans `.update_cache.json` :

```json
{
  "last_check": "2025-11-02T18:04:52.652667",
  "update_available": false,
  "new_version": null,
  "release_url": null,
  "current_version": "0.10.0"
}
```

### 5. Affichage de la notification

Si une mise à jour est détectée, une `UpdateNotification` est créée et affichée dans le menu.

## Configuration

### Paramètres

**`galad_config.json`**

```json
{
  "check_updates": true,  // Active/désactive la vérification
  "dev_mode": false       // Si true, ignore les vérifications
}
```

### Constantes

**`src/utils/update_checker.py`**

```python
GITHUB_API_URL = "https://api.github.com/repos/Fydyr/Galad-Islands/releases/latest"
TIMEOUT = 5  # Timeout requête en secondes
CACHE_FILE = ".update_cache.json"
CACHE_DURATION_HOURS = 24  # Durée de validité du cache
```

## Gestion des erreurs

Le système est robuste et gère plusieurs cas d'erreur :

| Erreur | Comportement |
|--------|--------------|
| Timeout réseau | Utilise le cache si disponible |
| Erreur API GitHub | Log warning, retourne cache |
| Cache corrompu | Ignore et revérifie |
| Pas de connexion | Échoue silencieusement |
| Mode dev activé | Ignore la vérification |

**Exemple de gestion** :

```python
try:
    response = requests.get(GITHUB_API_URL, timeout=TIMEOUT)
    response.raise_for_status()
    # Traitement...
except requests.exceptions.Timeout:
    logger.warning("Délai d'attente dépassé")
    return _get_cached_update_info()
except requests.exceptions.RequestException as e:
    logger.warning(f"Erreur réseau: {e}")
    return _get_cached_update_info()
```

## Interface utilisateur

### Notification

**Apparence** :

- Position : Coin supérieur droit
- Taille : 350x120 pixels
- Style : Fond bleu semi-transparent avec bordure
- Effets : Hover sur les boutons

**Boutons** :

- **"Télécharger"** : Ouvre `release_url` dans le navigateur via `webbrowser.open()`
- **"Plus tard"** : Ferme la notification (propriété `dismissed = True`)

**Gestion des événements** :

```python
def handle_event(self, event: pygame.event.Event) -> bool:
    if event.type == pygame.MOUSEMOTION:
        self._update_hover_state(mouse_x, mouse_y)
        return True
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if download_rect.collidepoint(mouse_x, mouse_y):
            self._open_release_page()
            self.dismissed = True
            return True
        elif later_rect.collidepoint(mouse_x, mouse_y):
            self.dismissed = True
            return True
    return False
```

### Options (à implémenter)

Une option "Vérifier les mises à jour" sera ajoutée dans le menu Options avec :

- ☑️ Checkbox "Vérifier automatiquement au démarrage"
- 🔄 Bouton "Vérifier maintenant" (appelle `check_for_updates_force()`)
- ℹ️ Description du comportement (cache 24h, ignore en mode dev)

## Tests

### Test manuel

**Script de test** : `test_update_notification.py`

Force l'affichage d'une notification avec une version mockée :

```bash
python3 test_update_notification.py
```

### Test de vérification

```python
from src.utils.update_checker import check_for_updates

result = check_for_updates()
if result:
    version, url = result
    print(f"Mise à jour disponible: {version}")
    print(f"URL: {url}")
else:
    print("Aucune mise à jour disponible")
```

### Test forcé (ignore cache et dev mode)

```python
from src.utils.update_checker import check_for_updates_force

result = check_for_updates_force()
# Toujours effectue une vérification réseau
```

## Traductions

### Clés i18n

**Français (`assets/locales/french.py`)** :

```python
"update.available_title": "Mise à jour disponible",
"update.available_message": "Une nouvelle version ({version}) est disponible !\nVous utilisez actuellement la version {current_version}.",
"update.download_button": "Télécharger",
"update.later_button": "Plus tard",
"update.checking": "Vérification des mises à jour...",
"update.no_update": "Vous utilisez la dernière version !",
"update.check_failed": "Impossible de vérifier les mises à jour",
```

**Anglais (`assets/locales/english.py`)** :

```python
"update.available_title": "Update Available",
"update.available_message": "A new version ({version}) is available!\nYou are currently using version {current_version}.",
"update.download_button": "Download",
"update.later_button": "Later",
"update.checking": "Checking for updates...",
"update.no_update": "You are using the latest version!",
"update.check_failed": "Unable to check for updates",
```

## Bonnes pratiques

### Développement

- ✅ Toujours activer `dev_mode: true` pendant le développement
- ✅ Utiliser `check_for_updates_force()` pour tester
- ✅ Vérifier les logs avec niveau DEBUG
- ✅ Tester avec et sans connexion internet

### Production

- ✅ Le cache limite les requêtes GitHub (max 1/jour)
- ✅ La vérification est asynchrone (pas de blocage UI)
- ✅ Les erreurs sont silencieuses (pas de crash)
- ✅ L'utilisateur peut désactiver la fonctionnalité

### Rate Limiting GitHub

L'API GitHub autorise :

- **60 requêtes/heure** pour IP non authentifiée
- **5000 requêtes/heure** avec token OAuth

Notre système respecte ces limites avec :

- Cache 24h (max 1 requête/jour/utilisateur)
- Timeout 5 secondes
- Gestion d'erreur robuste

## Dépendances

```txt
requests>=2.31.0  # Requêtes HTTP vers GitHub API
packaging>=23.0   # Comparaison sémantique de versions
```

## Fichiers concernés

```text
src/
  utils/
    update_checker.py        # Logique de vérification
  ui/
    update_notification.py   # Widget de notification
  version.py                 # Version actuelle (__version__)
  settings/
    settings.py              # Configuration (check_updates)
main.py                      # Intégration menu principal
galad_config.json            # Config utilisateur
.update_cache.json           # Cache (généré)
requirements.txt             # Dépendances
```

## Évolutions futures

### Proposées

- [ ] Bouton "Vérifier maintenant" dans Options
- [ ] Notification de version beta/pre-release
- [ ] Téléchargement direct dans l'application
- [ ] Changelog affiché dans la notification
- [ ] Support du mode offline (pas d'erreur si pas de connexion)

### En discussion

- [ ] Auto-update (téléchargement et installation automatique)
- [ ] Channel de mises à jour (stable, beta, dev)
- [ ] Statistiques anonymes d'utilisation
