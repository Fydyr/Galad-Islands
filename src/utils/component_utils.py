import esper
import logging
from typing import Any, List, Optional, Type

logger = logging.getLogger(__name__)


def get_component(entity: int, component_type: Type[Any], alt_names: Optional[List[str]] = None) -> Optional[Any]:
    """
    Try to fetch `component_type` for `entity` using esper.component_for_entity
    or fall back to scanning the entity's components by class name.

    - alt_names: optional list of alternate class names to match (e.g. for different import paths)
    """
    try:
        return esper.component_for_entity(entity, component_type)
    except Exception:
        try:
            manifest = esper._entities.get(entity, {})
            candidates = [component_type.__name__]
            if alt_names:
                candidates.extend(alt_names)
            for comp in manifest.values():
                if comp is None:
                    continue
                if comp.__class__.__name__ in candidates:
                    return comp
        except Exception as e:
            logger.debug("get_component fallback scan failed for entity %s: %s", entity, e)
    return None


def list_entity_components(entity: int) -> List[str]:
    """
    Debug helper: returns a list of strings describing components attached
    to the given entity (class name and module where available)
    """
    try:
        manifest = esper._entities.get(entity, {})
        out = []
        for comp in manifest.values():
            if comp is None:
                out.append("None")
                continue
            try:
                m = comp.__class__.__module__
            except Exception:
                m = "unknown"
            out.append(f"{comp.__class__.__name__} ({m})")
        return out
    except Exception:
        return []
