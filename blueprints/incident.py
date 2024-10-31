from dataclasses import dataclass, field
from flask import Blueprint, Response, request
from flask.views import MethodView
from marshmallow import ValidationError
import marshmallow.validate
import marshmallow_dataclass

from blueprints.util import class_route
from containers import Container
from models import Incident, Channel
from typing import Any

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
    }

# Incident validation schema
@dataclass
class RegistryIncidentBody:
    client_id: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=50)})
    name: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=60)})
    channel: str = field(metadata={'validate': marshmallow.validate.OneOf([Channel.WEB.value, Channel.EMAIL.value, Channel.MOBILE.value])})
    reported_by: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=50)})
    created_by: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=50)})
    description: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=1000)})
    assigned_to: str = field(metadata={'validate': marshmallow.validate.Length(min=1, max=50)})

@class_route(blp, '/api/v1/register/incident')
class RegistryIncident(MethodView):
    init_every_request = False

    # def get(self) -> Response:
    #     return Response('Blueprint Works!', status=200)