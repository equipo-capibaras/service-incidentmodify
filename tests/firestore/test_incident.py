import contextlib
import os
from dataclasses import asdict
from datetime import UTC
from typing import cast
from unittest import skipUnless

import requests
from faker import Faker
from google.api_core.exceptions import AlreadyExists
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import CollectionReference
from unittest_parametrize import ParametrizedTestCase

from models import Action, Channel, HistoryEntry, Incident
from repositories.firestore import FirestoreIncidentRepository

FIRESTORE_DATABASE = '(default)'


@skipUnless('FIRESTORE_EMULATOR_HOST' in os.environ, 'Firestore emulator not available')
class TestClient(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()

        # Reset Firestore emulator before each test
        requests.delete(
            f'http://{os.environ["FIRESTORE_EMULATOR_HOST"]}/emulator/v1/projects/google-cloud-firestore-emulator/databases/{FIRESTORE_DATABASE}/documents',
            timeout=5,
        )

        self.repo = FirestoreIncidentRepository(FIRESTORE_DATABASE)
        self.client = FirestoreClient(database=FIRESTORE_DATABASE)

    def create_random_incident(self, *, client_id: str | None = None) -> Incident:
        return Incident(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id or cast(str, self.faker.uuid4()),
            name=self.faker.sentence(3),
            channel=self.faker.random_element(list(Channel)),
            reported_by=cast(str, self.faker.uuid4()),
            created_by=cast(str, self.faker.uuid4()),
            assigned_to=cast(str, self.faker.uuid4()),
        )

    def create_random_history_entry(self, *, client_id: str | None = None, incident_id: str | None = None) -> HistoryEntry:
        return HistoryEntry(
            incident_id=incident_id or cast(str, self.faker.uuid4()),
            client_id=client_id or cast(str, self.faker.uuid4()),
            date=self.faker.past_datetime(tzinfo=UTC),
            action=self.faker.random_element(list(Action)),
            description=self.faker.text(),
        )

    def add_random_incidents(self, n: int) -> list[Incident]:
        incidents: list[Incident] = []

        # Add n incidents to Firestore
        for _ in range(n):
            incident = self.create_random_incident()

            incidents.append(incident)
            incident_dict = asdict(incident)
            del incident_dict['id']
            del incident_dict['client_id']

            client_ref = self.client.collection('clients').document(incident.client_id)
            with contextlib.suppress(AlreadyExists):
                client_ref.create({})

            incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident.id)
            incident_ref.create(incident_dict)

        return incidents

    def test_create(self) -> None:
        incident = self.create_random_incident()

        self.repo.create(incident)

        client_ref = self.client.collection('clients').document(incident.client_id)
        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident.id)
        doc = incident_ref.get()

        self.assertTrue(doc.exists)
        incident_dict = asdict(incident)
        del incident_dict['id']
        del incident_dict['client_id']
        self.assertEqual(doc.to_dict(), incident_dict)

    def test_append_history_entries(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        incident_id = cast(str, self.faker.uuid4())
        entries = [self.create_random_history_entry(client_id=client_id, incident_id=incident_id) for _ in range(5)]

        for entry in entries:
            self.repo.append_history_entry(entry)

        for idx, entry in enumerate(entries):
            client_ref = self.client.collection('clients').document(entry.client_id)
            incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(entry.incident_id)
            history_ref = cast(CollectionReference, incident_ref.collection('history'))
            doc = history_ref.document(str(idx)).get()

            self.assertTrue(doc.exists)
            entry_dict = asdict(entry)
            del entry_dict['client_id']
            del entry_dict['incident_id']
            del entry_dict['seq']
            entry_db = doc.to_dict()
            self.assertEqual(entry_db, entry_dict)

    def test_append_history_valueerror(self) -> None:
        entry = self.create_random_history_entry()
        entry.seq = 1

        with self.assertRaises(ValueError):
            self.repo.append_history_entry(entry)

    def test_delete_all(self) -> None:
        incidents = self.add_random_incidents(5)

        self.repo.delete_all()

        for incident in incidents:
            client_ref = self.client.collection('clients').document(incident.client_id)
            incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident.id)
            doc = incident_ref.get()

            self.assertFalse(doc.exists)
