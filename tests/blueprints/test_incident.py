import base64
import json
from typing import Any, cast
from unittest.mock import Mock, patch

from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Action, Channel, Risk
from repositories import IncidentRepository
from tests.util import create_random_history_entry, create_random_incident
from utils import CLOSED_INCIDENT_ERROR, INCIDENT_NOT_FOUND, INVALID_UUID_ERROR, JSON_VALIDATION_ERROR


class TestIncidentUpdate(ParametrizedTestCase):
    INCIDENT_INTERNAL_UPDATE_URL = '/api/v1/clients/{client_id}/employees/{assigned_to}/incidents/{incident_id}/update'
    REGISTER_INCIDENT_URL = '/api/v1/register/incident'
    INCIDENT_UPDATE_URL = '/api/v1/incidents/{incident_id}/update'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def gen_token(self, *, client_id: str) -> dict[str, Any]:
        return {
            'sub': cast(str, self.faker.uuid4()),
            'cid': client_id,
            'role': 'agent',
            'aud': 'agent',
        }

    def call_register_incident(self, body: dict[str, Any] | str) -> TestResponse:
        return self.client.post(
            self.REGISTER_INCIDENT_URL,
            data=body if isinstance(body, str) else json.dumps(body),
            content_type='application/json',
        )

    def call_internal_update_api(
        self, token: dict[str, Any], client_id: str, assigned_to: str, incident_id: str, body: dict[str, Any] | str
    ) -> TestResponse:
        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        try:
            data = json.dumps(body)
        except TypeError:
            data = json.dumps({'error': 'invalid body'})
        return self.client.post(
            self.INCIDENT_INTERNAL_UPDATE_URL.format(client_id=client_id, assigned_to=assigned_to, incident_id=incident_id),
            headers={'X-Apigateway-Api-Userinfo': token_encoded},
            data=data,
            content_type='application/json',
        )

    def call_update_api(self, token: dict[str, str] | None, incident_id: str, body: dict[str, Any] | str) -> TestResponse:
        if token is None:
            return self.client.post(
                self.INCIDENT_UPDATE_URL.format(incident_id=incident_id),
                data=json.dumps(body),
                content_type='application/json',
            )

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(
            self.INCIDENT_UPDATE_URL.format(incident_id=incident_id),
            headers={'X-Apigateway-Api-Userinfo': token_encoded},
            data=body if isinstance(body, str) else json.dumps(body),
            content_type='application/json',
        )

    @parametrize(
        'channel',
        [
            (Channel.WEB.value,),
            (Channel.EMAIL.value,),
            (Channel.MOBILE.value,),
        ],
    )
    @patch('blueprints.incident.send_notification')
    def test_register_incident_success(self, _send_notification: Mock, channel: str) -> None:
        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.create).return_value = None
        cast(Mock, incident_repo_mock.append_history_entry).return_value = None

        payload = {
            'client_id': str(self.faker.uuid4()),
            'name': 'Test Incident',
            'channel': channel,
            'reported_by': str(self.faker.uuid4()),
            'created_by': str(self.faker.uuid4()),
            'description': 'Esto es una incidencia de prueba',
            'assigned_to': str(self.faker.uuid4()),
        }

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_register_incident(payload)

        self.assertEqual(resp.status_code, 201)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['client_id'], payload['client_id'])
        self.assertEqual(resp_data['name'], payload['name'])
        self.assertEqual(resp_data['channel'].lower(), payload['channel'].lower())
        self.assertEqual(resp_data['reported_by'], payload['reported_by'])

    def test_register_incident_invalid_channel(self) -> None:
        payload = {
            'client_id': str(self.faker.uuid4()),
            'name': 'Test Incident',
            'channel': 'invalid_channel',
            'reported_by': str(self.faker.uuid4()),
            'created_by': str(self.faker.uuid4()),
            'description': 'Esto es una incidencia de prueba',
            'assigned_to': str(self.faker.uuid4()),
        }

        resp = self.call_register_incident(payload)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertIn('Invalid value for channel', resp_data['message'])

    @parametrize(
        'missing_field',
        [
            ('client_id',),
            ('name',),
            ('channel',),
            ('reported_by',),
            ('created_by',),
            ('description',),
            ('assigned_to',),
        ],
    )
    def test_register_incident_missing_field(self, missing_field: str) -> None:
        payload = {
            'client_id': str(self.faker.uuid4()),
            'name': 'Test Incident',
            'channel': Channel.WEB.value,
            'reported_by': str(self.faker.uuid4()),
            'created_by': str(self.faker.uuid4()),
            'description': 'Esto es una incidencia de prueba',
            'assigned_to': str(self.faker.uuid4()),
        }

        del payload[missing_field]

        resp = self.call_register_incident(payload)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertIn(f'Invalid value for {missing_field}: Missing data for required field.', resp_data['message'])

    def test_register_invalid_json(self) -> None:
        resp = self.call_register_incident(self.faker.word())

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 400, 'message': 'Request body must be a JSON object.'})

    def test_update_no_token(self) -> None:
        resp = self.call_update_api(None, str(self.faker.uuid4()), {})

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': 'Token is missing'})

    @parametrize(
        'missing_field',
        [
            ('sub',),
            ('cid',),
            ('role',),
            ('aud',),
        ],
    )
    def test_update_token_missing_fields(self, missing_field: str) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        del token[missing_field]
        resp = self.call_update_api(token, str(self.faker.uuid4()), {})

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': f'{missing_field} is missing in token'})

    def test_update_token_invalid_json(self) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        resp = self.call_update_api(token, str(self.faker.uuid4()), self.faker.word())

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 400, 'message': JSON_VALIDATION_ERROR})

    @parametrize(
        'field',
        [
            ('action',),
            ('description',),
            ('incident_id',),
        ],
    )
    def test_update_invalid_data(self, field: str) -> None:
        incident_id = str(self.faker.uuid4())
        data = {
            'action': self.faker.random_element([Action.ESCALATED, Action.CLOSED]),
            'description': self.faker.sentence(),
        }

        if field == 'incident_id':
            incident_id = self.faker.word()
        else:
            del data[field]

        token = self.gen_token(client_id=str(self.faker.uuid4()))
        resp = self.call_update_api(token, incident_id, data)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        if field == 'incident_id':
            self.assertEqual(resp_data, {'code': 400, 'message': INVALID_UUID_ERROR.format(field='incident_id')})
        else:
            self.assertEqual(
                resp_data, {'code': 400, 'message': f'Invalid value for {field}: Missing data for required field.'}
            )

    def test_update_incident_not_found(self) -> None:
        incident_id = str(self.faker.uuid4())
        data = {
            'action': self.faker.random_element([Action.ESCALATED, Action.CLOSED]),
            'description': self.faker.sentence(),
        }

        token = self.gen_token(client_id=str(self.faker.uuid4()))

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = None

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_update_api(token, incident_id, data)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 404, 'message': 'Incident not found.'})

    def test_update_incident_not_allowed(self) -> None:
        incident = create_random_incident(self.faker)
        data = {
            'action': self.faker.random_element([Action.ESCALATED, Action.CLOSED]),
            'description': self.faker.sentence(),
        }

        token = self.gen_token(client_id=str(self.faker.uuid4()))

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = incident

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_update_api(token, incident.id, data)

        self.assertEqual(resp.status_code, 403)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 403, 'message': 'You are not allowed to access this incident.'})

    def test_update_incident_closed(self) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        incident = create_random_incident(self.faker, overrides={'assigned_to': token['sub']})
        data = {
            'action': self.faker.random_element([Action.ESCALATED, Action.CLOSED]),
            'description': self.faker.sentence(),
        }

        incident_history = [
            create_random_history_entry(self.faker, seq=i, client_id=incident.client_id, incident_id=incident.id)
            for i in range(3)
        ]
        incident_history[-1].action = Action.CLOSED

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = incident
        cast(Mock, incident_repo_mock.get_history).return_value = incident_history

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_update_api(token, incident.id, data)

        self.assertEqual(resp.status_code, 409)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 409, 'message': 'Incident is already closed.'})

    @patch('blueprints.incident.send_notification')
    def test_update_incident(self, _send_notification: Mock) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        incident = create_random_incident(self.faker, overrides={'assigned_to': token['sub']})
        data = {
            'action': self.faker.random_element([Action.ESCALATED, Action.CLOSED]),
            'description': self.faker.sentence(),
        }

        incident_history = [
            create_random_history_entry(self.faker, seq=0, client_id=incident.client_id, incident_id=incident.id)
        ]
        incident_history[0].action = Action.CREATED

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = incident
        cast(Mock, incident_repo_mock.get_history).return_value = incident_history

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_update_api(token, incident.id, data)

        self.assertEqual(resp.status_code, 201)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['action'], data['action'])
        self.assertEqual(resp_data['description'], data['description'])

    def test_internal_invalid_json_body(self) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        client_id = str(self.faker.uuid4())
        assigned_to = str(self.faker.uuid4())
        incident_id = str(self.faker.uuid4())

        invalid_body = {'invalid': object()}

        response = self.call_internal_update_api(token, client_id, assigned_to, incident_id, invalid_body)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            (
                'Invalid value for action: Missing data for required field. Invalid value for description: Missing data for '
                'required field. Invalid value for error: Unknown field.'
            ),
            response.get_data(as_text=True),
        )

    def test_internal_invalid_incident_id(self) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        client_id = str(self.faker.uuid4())
        assigned_to = str(self.faker.uuid4())
        invalid_incident_id = 'invalid-uuid'

        body = {'action': Action.ESCALATED.value, 'description': 'Test description'}
        response = self.call_internal_update_api(token, client_id, assigned_to, invalid_incident_id, body)

        self.assertEqual(response.status_code, 400)
        self.assertIn(INVALID_UUID_ERROR.format(field='incident_id'), response.get_data(as_text=True))

    def test_internal_incident_not_found(self) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        client_id = str(self.faker.uuid4())
        assigned_to = str(self.faker.uuid4())
        incident_id = str(self.faker.uuid4())

        incident_repo_mock = Mock(IncidentRepository)
        incident_repo_mock.get.return_value = None

        with self.app.container.incident_repo.override(incident_repo_mock):
            response = self.call_internal_update_api(
                token, client_id, assigned_to, incident_id, {'action': 'closed', 'description': 'Test'}
            )

        self.assertEqual(response.status_code, 404)
        self.assertIn('Incident not found.', response.get_data(as_text=True))

    def test_internal_not_assigned_to_user(self) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        incident = create_random_incident(self.faker)
        body = {'action': Action.CLOSED.value, 'description': 'Closing incident'}

        incident_repo_mock = Mock(IncidentRepository)
        incident_repo_mock.get.return_value = incident

        with self.app.container.incident_repo.override(incident_repo_mock):
            response = self.call_internal_update_api(token, incident.client_id, str(self.faker.uuid4()), incident.id, body)

        self.assertEqual(response.status_code, 403)
        self.assertIn('You are not allowed to access this incident.', response.get_data(as_text=True))

    def test_internal_incident_already_closed(self) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        incident = create_random_incident(self.faker)
        history = [create_random_history_entry(self.faker, seq=0)]
        history[0].action = Action.CLOSED

        incident_repo_mock = Mock(IncidentRepository)
        incident_repo_mock.get.return_value = incident
        incident_repo_mock.get_history.return_value = history

        with self.app.container.incident_repo.override(incident_repo_mock):
            response = self.call_internal_update_api(
                token, incident.client_id, incident.assigned_to, incident.id, {'action': 'closed', 'description': 'Test'}
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn(CLOSED_INCIDENT_ERROR, response.get_data(as_text=True))

    @patch('blueprints.incident.send_notification')
    def test_internal_update_success(self, _send_notification: Mock) -> None:
        token = self.gen_token(client_id=str(self.faker.uuid4()))
        incident = create_random_incident(self.faker)
        history_entry = create_random_history_entry(self.faker, seq=0)
        history_entry.action = Action.CREATED
        update_body = {'action': Action.ESCALATED.value, 'description': 'Escalating incident'}

        incident_repo_mock = Mock(IncidentRepository)
        incident_repo_mock.get.return_value = incident
        incident_repo_mock.get_history.return_value = [history_entry]

        with self.app.container.incident_repo.override(incident_repo_mock):
            response = self.call_internal_update_api(token, incident.client_id, incident.assigned_to, incident.id, update_body)

        self.assertEqual(response.status_code, 201)
        resp_data = json.loads(response.get_data())
        self.assertEqual(resp_data['action'], update_body['action'])
        self.assertEqual(resp_data['description'], update_body['description'])

    def test_update_risk_invalid_json(self) -> None:
        client_id = str(self.faker.uuid4())
        incident_id = str(self.faker.uuid4())

        resp = self.client.put(
            f'/api/v1/clients/{client_id}/incidents/{incident_id}/update-risk',
            data=self.faker.word(),  # Not a valid JSON
            content_type='application/json',
        )

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 400, 'message': JSON_VALIDATION_ERROR})

    def test_update_risk_incident_not_found(self) -> None:
        client_id = str(self.faker.uuid4())
        incident_id = str(self.faker.uuid4())
        data = {'risk': Risk.LOW.value}

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = None

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.client.put(
                f'/api/v1/clients/{client_id}/incidents/{incident_id}/update-risk',
                data=json.dumps(data),
                content_type='application/json',
            )

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 404, 'message': INCIDENT_NOT_FOUND})

    def test_update_risk_closed_incident(self) -> None:
        client_id = str(self.faker.uuid4())
        incident = create_random_incident(self.faker, overrides={'client_id': client_id})
        data = {'risk': Risk.MEDIUM.value}

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = incident
        cast(Mock, incident_repo_mock.get_history).return_value = [
            create_random_history_entry(self.faker, seq=0, action=Action.CLOSED)
        ]

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.client.put(
                f'/api/v1/clients/{client_id}/incidents/{incident.id}/update-risk',
                data=json.dumps(data),
                content_type='application/json',
            )

        self.assertEqual(resp.status_code, 409)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 409, 'message': CLOSED_INCIDENT_ERROR})

    def test_update_risk_invalid_incident_id(self) -> None:
        client_id = str(self.faker.uuid4())
        invalid_incident_id = 'not-a-valid-uuid'
        data = {'risk': Risk.LOW.value}

        resp = self.client.put(
            f'/api/v1/clients/{client_id}/incidents/{invalid_incident_id}/update-risk',
            data=json.dumps(data),
            content_type='application/json',
        )

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 400, 'message': INVALID_UUID_ERROR.format(field='incident_id')})

    @parametrize(
        'initial_risk, updated_risk, expected_status_code, should_notify',
        [
            (Risk.LOW.value, Risk.HIGH.value, 200, True),
            (Risk.HIGH.value, Risk.HIGH.value, 200, False),
        ],
    )
    @patch('blueprints.incident.send_notification')
    def test_update_risk(
        self,
        _send_notification: Mock,
        initial_risk: str,
        updated_risk: str,
        expected_status_code: int,
        should_notify: bool,  # noqa: FBT001
    ) -> None:
        client_id = str(self.faker.uuid4())
        incident = create_random_incident(self.faker, overrides={'client_id': client_id, 'risk': initial_risk})
        data = {'risk': updated_risk}

        incident_repo_mock = Mock(spec=IncidentRepository)
        incident_repo_mock.get.return_value = incident
        incident_repo_mock.get_history.return_value = [create_random_history_entry(self.faker, seq=0, action=Action.CREATED)]
        incident_repo_mock.update.return_value = None

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.client.put(
                f'/api/v1/clients/{client_id}/incidents/{incident.id}/update-risk',
                data=json.dumps(data),
                content_type='application/json',
            )

        self.assertEqual(resp.status_code, expected_status_code)

        if should_notify:
            _send_notification.assert_called_once_with(client_id, incident.id, 'incident-risk-updated')
        else:
            _send_notification.assert_not_called()

    def test_update_risk_validation_error(self) -> None:
        client_id = str(self.faker.uuid4())
        incident_id = str(self.faker.uuid4())

        invalid_body = {
            'risk': 'INVALID_RISK_VALUE',
            'extra_field': 'unexpected',
        }

        response = self.client.put(
            f'/api/v1/clients/{client_id}/incidents/{incident_id}/update-risk',
            data=json.dumps(invalid_body),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn('Invalid value for risk', response_data['message'])
        self.assertIn('Unknown field', response_data['message'])
