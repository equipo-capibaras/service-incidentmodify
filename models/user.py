from dataclasses import dataclass


@dataclass
class User:
    id: str
    client_id: str
    name: str
    email: str
