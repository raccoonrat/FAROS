from pathlib import Path
from typing import List

from app.faros.loaders.profile_loader import ProfileLoader
from app.faros.models.profile import Profile


class ProfileRegistry:
    """In-memory registry backed by profile assets on disk."""

    def __init__(self, root: Path):
        self.loader = ProfileLoader(root)

    def list(self) -> List[Profile]:
        return self.loader.list_profiles()

    def get(self, profile_id: str) -> Profile:
        return self.loader.load(profile_id)


_registry: ProfileRegistry | None = None


def get_profile_registry() -> ProfileRegistry:
    global _registry
    if _registry is None:
        root = Path(__file__).resolve().parents[1] / "profiles"
        _registry = ProfileRegistry(root)
    return _registry
