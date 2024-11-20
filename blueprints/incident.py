from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import marshmallow.validate
import marshmallow_dataclass
from dependency_injector.wiring import Provide
from flask import Blueprint, Response, request
from flask.views import MethodView
from marshmallow import ValidationError

from containers import Container
from models import Action, Channel, HistoryEntry, Incident, Risk
from repositories import IncidentRepository
from utils import (
    CLOSED_INCIDENT_ERROR,
    INCIDENT_NOT_FOUND,
    INVALID_UUID_ERROR,
    JSON_VALIDATION_ERROR,
    UNAUTHORIZED_INCIDENT_ERROR,
)

from .notification import send_notification
from .util import class_route, error_response, is_valid_uuid4, json_response, requires_token, validation_error_response

blp = Blueprint('Incident', __name__)


def incident_to_dict(incident: Incident) -> dict[str, Any]:
    return {
        'id': incident.id,
        'client_id': incident.client_id,
        'name': incident.name,
        'channel': incident.channel.name,
        'reported_by': incident.reported_by,
        'created_by': incident.created_by,
        'assigned_to': incident.assigned_to,
        'risk': incident.risk,
    }


def history_to_dict(entry: HistoryEntry) -> dict[str, Any]:
    return {
        'seq': entry.seq,
        'date': entry.date.isoformat().replace('+00:00', 'Z'),
        'action': entry.action,
        'description': entry.description,
    }


# Incident validation schema
@dataclass
class RegistryIncidentBody:
    client_id: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=50)})
    name: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=60)})
    channel: str = field(
        metadata={'validate': marshmallow.validate.OneOf([Channel.WEB.value, Channel.EMAIL.value, Channel.MOBILE.value])}
    )
    reported_by: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=50)})
    created_by: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=50)})
    description: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=1000)})
    assigned_to: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=50)})


@class_route(blp, '/api/v1/register/incident')
class RegistryIncident(MethodView):
    init_every_request = False

    def post(
        self,
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        # Validate request body
        schema = marshmallow_dataclass.class_schema(RegistryIncidentBody)()
        req_json = request.get_json(silent=True)

        if req_json is None:
            return error_response(JSON_VALIDATION_ERROR, 400)

        try:
            data: RegistryIncidentBody = schema.load(req_json)
        except ValidationError as e:
            return validation_error_response(e)

        # Create incident
        incident = Incident(
            id=str(uuid4()),
            client_id=data.client_id,
            name=data.name,
            channel=Channel(data.channel),
            reported_by=data.reported_by,
            created_by=data.created_by,
            assigned_to=data.assigned_to,
            risk=None,
        )

        # Append history entry
        history_entry = HistoryEntry(
            incident_id=incident.id,
            client_id=incident.client_id,
            date=datetime.now(UTC).replace(microsecond=0),
            action=Action.CREATED,
            description=data.description,
        )

        # Save incident and history entry
        incident_repo.create(incident)
        incident_repo.append_history_entry(history_entry)

        send_notification(incident.client_id, incident.id, 'incident-update')

        if 'urgente' in data.description.lower():
            send_notification(incident.client_id, incident.id, 'incident-alert')

        return json_response(incident_to_dict(incident), 201)


@dataclass
class IncidentUpdateBody:
    action: str = field(
        metadata={'validate': [marshmallow.validate.OneOf([Action.ESCALATED, Action.CLOSED, Action.AI_RESPONSE])]}
    )
    description: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=1000)})


@class_route(blp, '/api/v1/incidents/<incident_id>/update')
class IncidentDetail(MethodView):
    init_every_request = False

    @requires_token
    def post(  # noqa: PLR0911
        self,
        incident_id: str,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        auth_schema = marshmallow_dataclass.class_schema(IncidentUpdateBody)()
        req_json = request.get_json(silent=True)
        if req_json is None:
            return error_response(JSON_VALIDATION_ERROR, 400)

        try:
            data: IncidentUpdateBody = auth_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        if not is_valid_uuid4(incident_id):
            return error_response(INVALID_UUID_ERROR.format(field='incident_id'), 400)

        incident = incident_repo.get(client_id=token['cid'], incident_id=incident_id)
        if incident is None:
            return error_response(INCIDENT_NOT_FOUND, 404)

        if incident.assigned_to != token['sub']:
            return error_response(UNAUTHORIZED_INCIDENT_ERROR, 403)

        history = list(incident_repo.get_history(client_id=token['cid'], incident_id=incident.id))

        if history[-1].action == Action.CLOSED:
            return error_response(CLOSED_INCIDENT_ERROR, 409)

        history_entry = HistoryEntry(
            incident_id=incident.id,
            client_id=incident.client_id,
            date=datetime.now(UTC).replace(microsecond=0),
            action=Action(data.action),
            description=data.description,
        )
        incident_repo.append_history_entry(history_entry)

        send_notification(incident.client_id, incident.id, 'incident-update')

        return json_response(history_to_dict(history_entry), 201)


# Internal only
@class_route(blp, '/api/v1/clients/<client_id>/employees/<assigned_to>/incidents/<incident_id>/update')
class IncidentUpdate(MethodView):
    init_every_request = False

    def post(  # noqa: PLR0911
        self,
        client_id: str,
        incident_id: str,
        assigned_to: str,
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        auth_schema = marshmallow_dataclass.class_schema(IncidentUpdateBody)()
        req_json = request.get_json(silent=True)
        if req_json is None:
            return error_response(JSON_VALIDATION_ERROR, 400)

        try:
            data: IncidentUpdateBody = auth_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        if not is_valid_uuid4(incident_id):
            return error_response(INVALID_UUID_ERROR.format(field='incident_id'), 400)

        incident = incident_repo.get(client_id=client_id, incident_id=incident_id)
        if incident is None:
            return error_response(INCIDENT_NOT_FOUND, 404)

        if incident.assigned_to != assigned_to:
            return error_response(UNAUTHORIZED_INCIDENT_ERROR, 403)

        history = list(incident_repo.get_history(client_id=client_id, incident_id=incident.id))

        if history[-1].action == Action.CLOSED:
            return error_response(CLOSED_INCIDENT_ERROR, 409)

        history_entry = HistoryEntry(
            incident_id=incident.id,
            client_id=incident.client_id,
            date=datetime.now(UTC).replace(microsecond=0),
            action=Action(data.action),
            description=data.description,
        )
        incident_repo.append_history_entry(history_entry)

        send_notification(incident.client_id, incident.id, 'incident-update')

        return json_response(history_to_dict(history_entry), 201)


@dataclass
class IncidentRiskUpdateBody:
    risk: str = field(metadata={'validate': marshmallow.validate.OneOf([Risk.HIGH, Risk.LOW, Risk.MEDIUM])})


@class_route(blp, '/api/v1/clients/<client_id>/incidents/<incident_id>/update-risk')
class IncidentUpdateRisk(MethodView):
    init_every_request = False

    def put(
        self,
        client_id: str,
        incident_id: str,
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        auth_schema = marshmallow_dataclass.class_schema(IncidentRiskUpdateBody)()
        req_json = request.get_json(silent=True)
        if req_json is None:
            return error_response(JSON_VALIDATION_ERROR, 400)

        try:
            data: IncidentRiskUpdateBody = auth_schema.load(req_json)
        except ValidationError as err:
            return validation_error_response(err)

        if not is_valid_uuid4(incident_id):
            return error_response(INVALID_UUID_ERROR.format(field='incident_id'), 400)

        incident = incident_repo.get(client_id=client_id, incident_id=incident_id)
        if incident is None:
            return error_response(INCIDENT_NOT_FOUND, 404)

        history = list(incident_repo.get_history(client_id=client_id, incident_id=incident.id))

        if history[-1].action == Action.CLOSED:
            return error_response(CLOSED_INCIDENT_ERROR, 409)

        prev_risk = incident.risk
        incident.risk = data.risk
        incident_repo.update(incident)

        if prev_risk != data.risk:
            send_notification(incident.client_id, incident.id, 'incident-risk-updated')

        return json_response(incident_to_dict(incident), 200)
