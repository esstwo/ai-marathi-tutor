"""Connector registry — maps connector names to callable functions.

Skills reference connectors by name (e.g. "get_child_profile"). This registry
collects all connector functions so the agentic loop can resolve and call them.
"""

from typing import Callable

# Global registry: connector_name → function
_registry: dict[str, Callable] = {}


def register(name: str, fn: Callable):
    """Register a connector function by name."""
    _registry[name] = fn


def get(name: str) -> Callable | None:
    """Look up a connector function by name."""
    return _registry.get(name)


def get_all() -> dict[str, Callable]:
    """Return all registered connectors."""
    return dict(_registry)


def get_for_skill(connector_names: list[str]) -> dict[str, Callable]:
    """Return only the connectors a skill needs."""
    return {name: _registry[name] for name in connector_names if name in _registry}


def _auto_register():
    """Auto-register all connector functions from connector modules."""
    from backend.connectors.supabase import children, auth, lessons, conversations, progress
    from backend.connectors.tts import google_tts

    # Each module's public functions become connectors
    modules = [children, auth, lessons, conversations, progress, google_tts]
    for module in modules:
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if callable(obj):
                register(name, obj)


_auto_register()
