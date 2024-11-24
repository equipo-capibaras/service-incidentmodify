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

from models import Channel, HistoryEntry, Incident
from repositories.firestore import FirestoreIncidentRepository
from tests.util import create_random_history_entry, create_random_incident

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

    def add_random_incidents(
        self, n: int, client_id: str | None = None, reported_by: str | None = None, assigned_to: str | None = None
    ) -> list[Incident]:
        incidents: list[Incident] = []

        # Add n incidents to Firestore
        for _ in range(n):
            incident = create_random_incident(
                self.faker, overrides={'client_id': client_id, 'reported_by': reported_by, 'assigned_to': assigned_to}
            )

            incidents.append(incident)
            incident_dict = asdict(incident)
            del incident_dict['id']
            del incident_dict['client_id']

            client_ref = self.client.collection('clients').document(incident.client_id)
            with contextlib.suppress(AlreadyExists):
                client_ref.create({})

            incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident.id)
            incident.last_modified = self.faker.past_datetime(tzinfo=UTC)  # type: ignore[attr-defined]
            incident_dict['last_modified'] = incident.last_modified  # type: ignore[attr-defined]
            incident_ref.create(incident_dict)

        return incidents

    def add_random_history_entries(
        self, n: int, client_id: str | None = None, incident_id: str | None = None
    ) -> list[HistoryEntry]:
        entries: list[HistoryEntry] = []

        # Add n history entries to Firestore
        for i in range(n):
            history_entry = create_random_history_entry(self.faker, seq=i, client_id=client_id, incident_id=incident_id)
            entries.append(history_entry)
            history_entry_dict = asdict(history_entry)
            del history_entry_dict['incident_id']
            del history_entry_dict['client_id']

            client_ref = self.client.collection('clients').document(history_entry.client_id)
            incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(history_entry.incident_id)
            history_ref = cast(CollectionReference, incident_ref.collection('history')).document(str(i))
            history_ref.create(history_entry_dict)
            incident_ref.update({'last_modified': history_entry.date})

        return entries

    def test_create(self) -> None:
        incident = create_random_incident(self.faker)

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
        incident = self.add_random_incidents(1)[0]
        entries = [
            create_random_history_entry(self.faker, seq=None, client_id=incident.client_id, incident_id=incident.id)
            for _ in range(5)
        ]

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
            entry_dict['seq'] = idx
            entry_db = doc.to_dict()
            self.assertEqual(entry_db, entry_dict)

    def test_append_history_valueerror(self) -> None:
        entry = create_random_history_entry(self.faker, seq=None)
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

    def test_get_history(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        reporter_id = cast(str, self.faker.uuid4())

        incident = self.add_random_incidents(1, client_id=client_id, reported_by=reporter_id)[0]
        entries = self.add_random_history_entries(3, client_id=client_id, incident_id=incident.id)

        result = list(self.repo.get_history(client_id=client_id, incident_id=incident.id))

        self.assertEqual(result, entries)

    def test_get_existing(self) -> None:
        client_id = cast(str, self.faker.uuid4())

        incident = self.add_random_incidents(1, client_id=client_id)[0]

        result = self.repo.get(client_id=client_id, incident_id=incident.id)

        self.assertEqual(result, incident)

    def test_get_not_found(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        incident_id = cast(str, self.faker.uuid4())

        result = self.repo.get(client_id=client_id, incident_id=incident_id)

        self.assertIsNone(result)

    def test_update_existing_incident(self) -> None:
        incident = self.add_random_incidents(1)[0]

        updated_incident = incident
        updated_incident.name = 'Updated Incident Name'
        updated_incident.channel = Channel.EMAIL

        self.repo.update(updated_incident)

        client_ref = self.client.collection('clients').document(updated_incident.client_id)
        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(updated_incident.id)
        doc = incident_ref.get()

        self.assertTrue(doc.exists)

    def test_update_non_existing_incident(self) -> None:
        incident = create_random_incident(self.faker)

        with self.assertRaises(ValueError) as context:
            self.repo.update(incident)

        self.assertEqual(str(context.exception), f'Incident with ID {incident.id} not found for client {incident.client_id}.')
