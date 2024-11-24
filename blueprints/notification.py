import json
from typing import Any, cast

from dependency_injector.wiring import Provide
from google.cloud.pubsub_v1 import PublisherClient  # type: ignore[import-untyped]
from google.cloud.pubsub_v1.publisher.futures import Future  # type: ignore[import-untyped]
from lingua import Language, LanguageDetectorBuilder

from containers import Container
from models import Client, HistoryEntry, Incident, User
from repositories import ClientRepository, EmployeeRepository, IncidentRepository, UserRepository


def client_to_dict(client: Client) -> dict[str, Any]:
    return {
        'id': client.id,
        'name': client.name,
        'emailIncidents': client.email_incidents,
        'plan': client.plan.value,
    }


def history_to_dict(entry: HistoryEntry) -> dict[str, Any]:
    return {
        'seq': entry.seq,
        'date': entry.date.isoformat().replace('+00:00', 'Z'),
        'action': entry.action,
        'description': entry.description,
    }


def incident_to_dict(
    incident: Incident,
    history: list[HistoryEntry],
    user_repo: UserRepository,
    employee_repo: EmployeeRepository,
) -> dict[str, Any]:
    user_reported_by = user_repo.get(incident.reported_by, incident.client_id)

    if user_reported_by is None:
        raise ValueError(f'User {incident.reported_by} not found')

    user_created_by = user_repo.get(incident.created_by, incident.client_id) or employee_repo.get(
        incident.created_by, incident.client_id
    )

    if user_created_by is None:
        raise ValueError(f'User/Employee {incident.created_by} not found')

    employee_assigned_to = employee_repo.get(incident.assigned_to, incident.client_id)

    if employee_assigned_to is None:
        raise ValueError(f'Employee {incident.assigned_to} not found')

    return {
        'id': incident.id,
        'name': incident.name,
        'channel': incident.channel,
        'reportedBy': {
            'id': user_reported_by.id,
            'name': user_reported_by.name,
            'email': user_reported_by.email,
            'role': 'user',
        },
        'createdBy': {
            'id': user_created_by.id,
            'name': user_created_by.name,
            'email': user_created_by.email,
            'role': 'user' if isinstance(user_created_by, User) else user_created_by.role,
        },
        'assignedTo': {
            'id': employee_assigned_to.id,
            'name': employee_assigned_to.name,
            'email': employee_assigned_to.email,
            'role': employee_assigned_to.role,
        },
        'history': [history_to_dict(x) for x in history],
        'risk': incident.risk,
    }


def send_notification(  # noqa: PLR0913
    client_id: str,
    incident_id: str,
    topic: str,
    client_repo: ClientRepository = Provide[Container.client_repo],
    incident_repo: IncidentRepository = Provide[Container.incident_repo],
    user_repo: UserRepository = Provide[Container.user_repo],
    employee_repo: EmployeeRepository = Provide[Container.employee_repo],
    project_id: str = Provide[Container.config.project_id],
) -> None:
    client = client_repo.get(client_id=client_id)
    if client is None:
        raise ValueError('Client not found.')

    incident = incident_repo.get(client_id=client_id, incident_id=incident_id)
    if incident is None:
        raise ValueError('Incident not found.')

    history = incident_repo.get_history(client_id=client_id, incident_id=incident_id)

    data = incident_to_dict(incident, list(history), user_repo, employee_repo)

    data['client'] = client_to_dict(client)

    detector = LanguageDetectorBuilder.from_languages(Language.SPANISH, Language.PORTUGUESE).build()
    language = detector.detect_language_of(incident.name + '\n' + data['history'][0]['description'])

    data['language'] = 'pt' if language == Language.PORTUGUESE else 'es'

    publisher = PublisherClient()
    future = cast(
        Future,
        publisher.publish(
            f'projects/{project_id}/topics/{topic}',
            json.dumps(data).encode('utf-8'),
            **{'Content-Type': 'application/json'},
        ),
    )
    future.result()
