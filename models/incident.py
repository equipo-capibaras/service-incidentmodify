from dataclasses import dataclass

from .channel import Channel


@dataclass
class Incident:
    id: str
    client_id: str
    name: str
    channel: Channel
    reported_by: str
    created_by: str
    assigned_to: str
    risk: str | None
