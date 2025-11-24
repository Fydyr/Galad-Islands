"""Legacy placeholder retained for compatibility. The prediction system is disabled."""

from __future__ import annotations


class PredictionService:  # pragma: no cover - guarded legacy shim
    """Dummy shim to avoid import errors when legacy scripts still reference it."""

    def __init__(self, *_args, **_kwargs) -> None:  # noqa: D401
        pass

    def __getattr__(self, name):
        raise RuntimeError(
            "PredictionService has been removed. The AI now relies solely on local vision."
            f" Attempted to access method '{name}'."
        )
