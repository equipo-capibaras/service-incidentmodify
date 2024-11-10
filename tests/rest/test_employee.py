from typing import cast
from unittest.mock import Mock

import responses
from faker import Faker
from requests import HTTPError
from unittest_parametrize import ParametrizedTestCase, parametrize

from models import Employee, InvitationStatus, Role
from repositories.rest import RestEmployeeRepository, TokenProvider


class TestEmployee(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.base_url = self.faker.url().rstrip('/')
        self.repo = RestEmployeeRepository(self.base_url, None)

    def test_authenticated_get_without_token_provider(self) -> None:
        repo = RestEmployeeRepository(self.base_url, None)

        with responses.RequestsMock() as rsps:
            rsps.get(self.base_url)
            repo.authenticated_get(self.base_url)
            self.assertNotIn('Authorization', rsps.calls[0].request.headers)

    def test_authenticated_get_with_token_provider(self) -> None:
        token = self.faker.pystr()
        token_provider = Mock(TokenProvider)
        cast(Mock, token_provider.get_token).return_value = token

        repo = RestEmployeeRepository(self.base_url, token_provider)

        with responses.RequestsMock() as rsps:
            rsps.get(self.base_url)
            repo.authenticated_get(self.base_url)
            self.assertEqual(rsps.calls[0].request.headers['Authorization'], f'Bearer {token}')

    def test_get_existing(self) -> None:
        client_id = cast(str, self.faker.uuid4())

        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.email(),
            role=self.faker.random_element([Role.ADMIN, Role.AGENT, Role.ANALYST]),
            invitation_status=self.faker.random_element(list(InvitationStatus)),
            invitation_date=self.faker.past_datetime(),
        )

        with responses.RequestsMock() as rsps:
            rsps.get(
                f'{self.base_url}/api/v1/employees/{client_id}/{employee.id}',
                json={
                    'id': employee.id,
                    'clientId': client_id,
                    'name': employee.name,
                    'email': employee.email,
                    'role': employee.role.value,
                    'invitationStatus': employee.invitation_status.value,
                    'invitationDate': employee.invitation_date.isoformat(),
                },
            )

            employee_repo = self.repo.get(employee.id, client_id)

        self.assertEqual(employee_repo, employee)

    def test_get_not_found(self) -> None:
        employee_id = cast(str, self.faker.uuid4())
        client_id = cast(str, self.faker.uuid4())

        with responses.RequestsMock() as rsps:
            rsps.get(f'{self.base_url}/api/v1/employees/{client_id}/{employee_id}', status=404)

            employee_repo = self.repo.get(employee_id, client_id)

        self.assertIsNone(employee_repo)

    @parametrize(
        'status',
        [
            (500,),
            (201,),
        ],
    )
    def test_get_error(self, status: int) -> None:
        employee_id = cast(str, self.faker.uuid4())
        client_id = cast(str, self.faker.uuid4())

        with responses.RequestsMock() as rsps:
            rsps.get(f'{self.base_url}/api/v1/employees/{client_id}/{employee_id}', status=status)

            with self.assertRaises(HTTPError):
                self.repo.get(employee_id, client_id)
