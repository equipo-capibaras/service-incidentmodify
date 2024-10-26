from dataclasses import dataclass
from datetime import datetime

from .action import Action


@dataclass
class HistoryEntry:
    incident_id: str
    client_id: str
    date: datetime
    action: Action
    description: str
    seq: int | None = None  # Only set when reading from DB
