from pathlib import Path
from typing import List

from app.faros.loaders.blueprint_loader import BlueprintLoader
from app.faros.models.blueprint import Blueprint


class BlueprintRegistry:
    """In-memory registry backed by blueprint assets on disk."""

    def __init__(self, root: Path):
        self.loader = BlueprintLoader(root)

    def list(self) -> List[Blueprint]:
        return self.loader.list_blueprints()

    def get(self, blueprint_id: str) -> Blueprint:
        return self.loader.load(blueprint_id)


_registry: BlueprintRegistry | None = None


def get_blueprint_registry() -> BlueprintRegistry:
    global _registry
    if _registry is None:
        root = Path(__file__).resolve().parents[1] / "blueprints"
        _registry = BlueprintRegistry(root)
    return _registry
