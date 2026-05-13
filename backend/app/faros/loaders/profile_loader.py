import json
from pathlib import Path
from typing import Dict, List

from app.faros.models.profile import Profile


class ProfileLoader:
    """Load FAROS execution profiles from disk."""

    def __init__(self, root: Path):
        self.root = root

    def list_profiles(self) -> List[Profile]:
        return [self.load(path.parent.name) for path in sorted(self.root.glob("*/profile.json"))]

    def load(self, profile_id: str) -> Profile:
        path = self.root / profile_id / "profile.json"
        if not path.is_file():
            raise FileNotFoundError(f"Profile '{profile_id}' not found")
        return Profile.model_validate(json.loads(path.read_text()))

    def describe(self) -> List[Dict[str, str]]:
        return [
            {
                "id": profile.id,
                "name": profile.name,
                "version": profile.version,
                "description": profile.description,
            }
            for profile in self.list_profiles()
        ]
