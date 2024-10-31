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

from blueprints.util import class_route, error_response, json_response, validation_error_response
from containers import Container
from models import Action, Channel, HistoryEntry, Incident
from repositories import IncidentRepository, RegistryIncidentError

blp = Blueprint('Incident', __name__)

JSON_VALIDATION_ERROR = 'Request body must be a JSON object.'
INVALID_UUID_ERROR = 'Invalid UUID format for {field}.'


def incident_to_dict(incident: Incident) -> dict[str, Any]:
    return {
        'id': incident.id,
        'client_id': incident.client_id,
        'name': incident.name,
        'channel': incident.channel.name,
        'reported_by': incident.reported_by,
        'created_by': incident.created_by,
        'assigned_to': incident.assigned_to,
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
        try:
            incident_repo.create(incident)
            incident_repo.append_history_entry(history_entry)
        except RegistryIncidentError:
            return error_response('Error saving the incident', 500)

        return json_response(incident_to_dict(incident), 201)
