import json
from pathlib import Path
from typing import Dict, List

from app.faros.models.blueprint import Blueprint


class BlueprintLoader:
    """Load blueprint assets from disk."""

    def __init__(self, root: Path):
        self.root = root

    def list_blueprints(self) -> List[Blueprint]:
        return [self.load(path.parent.name) for path in sorted(self.root.glob("*/blueprint.json"))]

    def load(self, blueprint_id: str) -> Blueprint:
        path = self.root / blueprint_id / "blueprint.json"
        if not path.is_file():
            raise FileNotFoundError(f"Blueprint '{blueprint_id}' not found")
        return Blueprint.model_validate(json.loads(path.read_text()))

    def describe(self) -> List[Dict[str, str]]:
        return [
            {
                "id": blueprint.id,
                "name": blueprint.name,
                "version": blueprint.version,
                "domain": blueprint.domain,
                "description": blueprint.description,
            }
            for blueprint in self.list_blueprints()
        ]
