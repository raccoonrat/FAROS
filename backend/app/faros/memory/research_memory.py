from typing import Any, Dict


class ResearchMemory:
    """A simple mutable memory view backed by the FAROS state store."""

    def __init__(self, state_store, run_id: str):
        self.state_store = state_store
        self.run_id = run_id
        self._data = state_store.get_memory(run_id)

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    def update(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.state_store.save_memory(self.run_id, self._data)

    def merge(self, payload: Dict[str, Any]) -> None:
        self._data.update(payload)
        self.state_store.save_memory(self.run_id, self._data)
