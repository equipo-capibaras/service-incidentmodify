from typing import cast
from unittest.mock import Mock, patch

from faker import Faker
from google.cloud.pubsub_v1 import PublisherClient  # type: ignore[import-untyped]
from unittest_parametrize import ParametrizedTestCase, parametrize

from blueprints.notification import send_notification
from models import Action, Client, Employee, InvitationStatus, Plan, Role, User
from repositories import ClientRepository, EmployeeRepository, IncidentRepository, UserRepository
from tests.util import create_random_history_entry, create_random_incident


class TestNotification(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()

    @parametrize(
        ('error',),
        [
            (None,),
            ('user',),
            ('employee',),
            ('client',),
            ('incident',),
        ],
    )
    @patch('blueprints.notification.PublisherClient')
    def test_notification(self, publisher_client_mock: Mock, error: str) -> None:
        client_id = cast(str, self.faker.uuid4())
        incident_id = cast(str, self.faker.uuid4())
        user_id = cast(str, self.faker.uuid4())
        agent_id = cast(str, self.faker.uuid4())

        topic = self.faker.pystr(min_chars=3, max_chars=10)
        project_id = self.faker.pystr(min_chars=3, max_chars=10)

        user = User(
            id=user_id,
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.email(),
        )

        employee = Employee(
            id=agent_id,
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.email(),
            role=Role.AGENT,
            invitation_status=InvitationStatus.ACCEPTED,
            invitation_date=self.faker.past_datetime(),
        )

        client = Client(
            id=client_id,
            name=self.faker.company(),
            plan=cast(Plan, self.faker.random_element(list(Plan))),
            email_incidents=self.faker.email(),
        )

        incident = create_random_incident(
            self.faker,
            overrides={
                'client_id': client_id,
                'reported_by': user_id,
                'created_by': user_id,
                'assigned_to': agent_id,
            },
        )

        incident_history = [
            create_random_history_entry(self.faker, seq=i, client_id=client_id, incident_id=incident_id) for i in range(3)
        ]
        incident_history[0].action = Action.CREATED

        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get).return_value = None if error == 'client' else client

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = None if error == 'incident' else incident
        cast(Mock, incident_repo_mock.get_history).return_value = (x for x in incident_history)

        user_repo_mock = Mock(UserRepository)
        cast(Mock, user_repo_mock.get).return_value = None if error == 'user' else user

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = None if error == 'employee' else employee

        mock_pubsub = Mock(PublisherClient)
        publisher_client_mock.side_effect = lambda: mock_pubsub

        if error is not None:
            with self.assertRaises(ValueError):
                send_notification(
                    client_id,
                    incident_id,
                    topic,
                    client_repo=client_repo_mock,
                    incident_repo=incident_repo_mock,
                    project_id=project_id,
                    employee_repo=employee_repo_mock,
                    user_repo=user_repo_mock,
                )

            cast(Mock, mock_pubsub.publish).assert_not_called()
        else:
            send_notification(
                client_id,
                incident_id,
                topic,
                client_repo=client_repo_mock,
                incident_repo=incident_repo_mock,
                project_id=project_id,
                employee_repo=employee_repo_mock,
                user_repo=user_repo_mock,
            )

            cast(Mock, mock_pubsub.publish).assert_called_once()
