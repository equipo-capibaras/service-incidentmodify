from typing import cast
from unittest.mock import Mock

import responses
from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize

from models import Client, Plan
from repositories.rest import RestClientRepository, TokenProvider


class TestClient(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.base_url = self.faker.url().rstrip('/')
        self.repo = RestClientRepository(self.base_url, None)

    def test_authenticated_get_without_token_provider(self) -> None:
        repo = RestClientRepository(self.base_url, None)

        with responses.RequestsMock() as rsps:
            rsps.get(self.base_url)
            repo.authenticated_get(self.base_url)
            self.assertNotIn('Authorization', rsps.calls[0].request.headers)

    def test_authenticated_get_with_token_provider(self) -> None:
        token = self.faker.pystr()
        token_provider = Mock(TokenProvider)
        cast(Mock, token_provider.get_token).return_value = token

        repo = RestClientRepository(self.base_url, token_provider)

        with responses.RequestsMock() as rsps:
            rsps.get(self.base_url)
            repo.authenticated_get(self.base_url)
            self.assertEqual(rsps.calls[0].request.headers['Authorization'], f'Bearer {token}')

    def test_get_success(self) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=cast(Plan, self.faker.random_element(list(Plan))),
            email_incidents=self.faker.email(),
        )

        with responses.RequestsMock() as rsps:
            rsps.get(
                f'{self.base_url}/api/v1/clients/{client.id}?include_plan=true',
                json={
                    'id': client.id,
                    'name': client.name,
                    'plan': client.plan.value,
                    'emailIncidents': client.email_incidents,
                },
                status=200,
            )

            client_repo = self.repo.get(client.id)

        self.assertEqual(client_repo, client)

    def test_get_not_found(self) -> None:
        client_id = cast(str, self.faker.uuid4())

        with responses.RequestsMock() as rsps:
            rsps.get(
                f'{self.base_url}/api/v1/clients/{client_id}?include_plan=true',
                json={
                    'message': 'Client not found',
                    'code': 404,
                },
                status=404,
            )

            client_repo = self.repo.get(client_id)

        self.assertIsNone(client_repo)

    @parametrize(
        'status',
        [
            (500,),
            (400,),
        ],
    )
    def test_get_error(self, status: int) -> None:
        client_id = cast(str, self.faker.uuid4())

        with responses.RequestsMock() as rsps:
            rsps.get(f'{self.base_url}/api/v1/clients/{client_id}?include_plan=true', status=status)

            client_repo = self.repo.get(client_id)
            self.assertIsNone(client_repo)
