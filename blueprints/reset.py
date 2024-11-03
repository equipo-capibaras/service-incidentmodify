import copy

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, Response, request
from flask.views import MethodView

import demo
from containers import Container
from repositories import IncidentRepository

from .util import class_route, json_response

blp = Blueprint('Reset database', __name__)


@class_route(blp, '/api/v1/reset/incidentmodify')
class ResetDB(MethodView):
    init_every_request = False

    @inject
    def post(
        self,
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        incident_repo.delete_all()

        if request.args.get('demo', 'false') == 'true':
            for incident in demo.incidents:
                incident_repo.create(incident)

                for entry in demo.history[incident.id]:
                    incident_repo.append_history_entry(copy.copy(entry))

        return json_response({'status': 'Ok'}, 200)
