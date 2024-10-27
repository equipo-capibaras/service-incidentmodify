from typing import cast
from unittest.mock import Mock

from unittest_parametrize import ParametrizedTestCase, parametrize

import demo
from app import create_app
from repositories import IncidentRepository


class TestReset(ParametrizedTestCase):
    API_ENDPOINT = '/api/v1/reset/incidentmodify'

    def setUp(self) -> None:
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.app.container.unwire()

    @parametrize(
        'arg,expected',
        [
            (None, False),
            ('true', True),
            ('false', False),
            ('foo', False),
        ],
    )
    def test_reset(self, arg: str | None, expected: bool) -> None:  # noqa: FBT001
        incident_repo_mock = Mock(IncidentRepository)
        call_order = []

        cast(Mock, incident_repo_mock.delete_all).side_effect = lambda: call_order.append('delete_all')
        cast(Mock, incident_repo_mock.create).side_effect = lambda _x: call_order.append('create')
        cast(Mock, incident_repo_mock.append_history_entry).side_effect = lambda _x: call_order.append('append_history_entry')

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.client.post(self.API_ENDPOINT + (f'?demo={arg}' if arg is not None else ''))

        cast(Mock, incident_repo_mock.delete_all).assert_called_once()

        if expected:
            expected_call_order = ['delete_all']

            for incident in demo.incidents:
                expected_call_order.append('create')
                expected_call_order += ['append_history_entry'] * len(demo.history[incident.id])

            self.assertEqual(call_order, expected_call_order)

        self.assertEqual(resp.status_code, 200)
