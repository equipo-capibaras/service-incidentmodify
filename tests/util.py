from datetime import UTC
from typing import cast

from faker import Faker

from models import Action, Channel, HistoryEntry, Incident, Risk


def create_random_incident(
    faker: Faker,
    *,
    overrides: dict[str, str | None] | None = None,
) -> Incident:
    overrides = overrides or {}
    risk_value = overrides.get('risk')
    return Incident(
        id=cast(str, faker.uuid4()),
        client_id=overrides.get('client_id') or cast(str, faker.uuid4()),
        name=faker.sentence(3),
        channel=cast(Channel, faker.random_element(list(Channel))),
        reported_by=overrides.get('reported_by') or cast(str, faker.uuid4()),
        created_by=overrides.get('created_by') or cast(str, faker.uuid4()),
        assigned_to=overrides.get('assigned_to') or cast(str, faker.uuid4()),
        risk=Risk(risk_value) if risk_value is not None else cast(Risk, faker.random_element(list(Risk))),
    )


def create_random_history_entry(
    faker: Faker,
    *,
    seq: int | None,
    client_id: str | None = None,
    incident_id: str | None = None,
    action: Action | None = None,
) -> HistoryEntry:
    return HistoryEntry(
        incident_id=incident_id or cast(str, faker.uuid4()),
        client_id=client_id or cast(str, faker.uuid4()),
        date=faker.past_datetime(tzinfo=UTC),
        action=action or cast(Action, faker.random_element(list(Action))),
        description=faker.text(),
        seq=seq,
    )
