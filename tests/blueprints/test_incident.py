import json
from typing import Any, cast
from unittest.mock import Mock

from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Channel
from repositories import IncidentRepository, RegistryIncidentError


class TestIncident(ParametrizedTestCase):
    REGISTER_INCIDENT_URL = '/api/v1/register/incident'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def call_register_incident(self, body: dict[str, Any]) -> TestResponse:
        return self.client.post(
            self.REGISTER_INCIDENT_URL,
            data=json.dumps(body),
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
    def test_register_incident_success(self, channel: str) -> None:
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

    def test_register_incident_repository_error(self) -> None:
        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.create).side_effect = RegistryIncidentError('Error saving the incident')

        payload = {
            'client_id': str(self.faker.uuid4()),
            'name': 'Test Incident',
            'channel': Channel.WEB.value,
            'reported_by': str(self.faker.uuid4()),
            'created_by': str(self.faker.uuid4()),
            'description': 'Esto es una incidencia de prueba',
            'assigned_to': str(self.faker.uuid4()),
        }

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_register_incident(payload)

        self.assertEqual(resp.status_code, 500)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Error saving the incident')
