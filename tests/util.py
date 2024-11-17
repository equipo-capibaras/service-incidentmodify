from datetime import UTC
from typing import cast

from faker import Faker

from models import Action, Channel, HistoryEntry, Incident


def create_random_incident(
    faker: Faker,
    *,
    client_id: str | None = None,
    reported_by: str | None = None,
    created_by: str | None = None,
    assigned_to: str | None = None,
) -> Incident:
    return Incident(
        id=cast(str, faker.uuid4()),
        client_id=client_id or cast(str, faker.uuid4()),
        name=faker.sentence(3),
        channel=cast(Channel, faker.random_element(list(Channel))),
        reported_by=reported_by or cast(str, faker.uuid4()),
        created_by=created_by or cast(str, faker.uuid4()),
        assigned_to=assigned_to or cast(str, faker.uuid4()),
    )


def create_random_history_entry(
    faker: Faker, *, seq: int | None, client_id: str | None = None, incident_id: str | None = None
) -> HistoryEntry:
    return HistoryEntry(
        incident_id=incident_id or cast(str, faker.uuid4()),
        client_id=client_id or cast(str, faker.uuid4()),
        date=faker.past_datetime(tzinfo=UTC),
        action=cast(Action, faker.random_element(list(Action))),
        description=faker.text(),
        seq=seq,
    )
