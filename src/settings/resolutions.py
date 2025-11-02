import json
from pathlib import Path
from typing import List, Tuple
from src.functions.resource_path import get_resource_path


def _custom_resolutions_path() -> Path:
    """Resolve the path to galad_resolutions.json in both dev and compiled builds.

    Uses the same strategy as other resources:
    1) next to the executable (for releases)
    2) PyInstaller's temp folder (_MEIPASS) if bundled
    3) repository root in development
    """
    return Path(get_resource_path("galad_resolutions.json"))

# Default built-in resolutions (example list) — the game's existing resolutions
BUILTIN = [
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
]


def load_custom_resolutions() -> List[Tuple[int, int]]:
    """Load custom resolutions from galad_resolutions.json.

    Returns a list of (width, height) tuples. If file is absent or malformed,
    returns empty list.
    """
    res_file = _custom_resolutions_path()
    if not res_file.exists():
        return []
    try:
        data = json.loads(res_file.read_text())
        res = []
        for entry in data:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                try:
                    w = int(entry[0])
                    h = int(entry[1])
                    if w > 0 and h > 0:
                        res.append((w, h))
                except Exception:
                    continue
        return res
    except Exception:
        return []


def get_all_resolutions() -> List[Tuple[int, int]]:
    """Return combined list of builtin + custom resolutions (no duplicates).

    Builtin resolutions come first, then custom ones that aren't already present.
    """
    customs = load_custom_resolutions()
    combined = BUILTIN.copy()
    existing = set(combined)
    for (w, h) in customs:
        if (w, h) not in existing:
            combined.append((w, h))
            existing.add((w, h))
    return combined
