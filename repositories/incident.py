from collections.abc import Generator

from models import HistoryEntry, Incident


class IncidentRepository:
    def create(self, incident: Incident) -> None:
        raise NotImplementedError  # pragma: no cover

    def get(self, client_id: str, incident_id: str) -> Incident | None:
        raise NotImplementedError  # pragma: no cover

    def append_history_entry(self, entry: HistoryEntry) -> None:
        raise NotImplementedError  # pragma: no cover

    def get_history(self, client_id: str, incident_id: str) -> Generator[HistoryEntry, None, None]:
        raise NotImplementedError  # pragma: no cover

    def delete_all(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def update(self, incident: Incident) -> None:
        raise NotImplementedError  # pragma: no cover
