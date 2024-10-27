from models import HistoryEntry, Incident


class IncidentRepository:
    def create(self, incident: Incident) -> None:
        raise NotImplementedError  # pragma: no cover

    def append_history_entry(self, entry: HistoryEntry) -> None:
        raise NotImplementedError  # pragma: no cover

    def delete_all(self) -> None:
        raise NotImplementedError  # pragma: no cover
