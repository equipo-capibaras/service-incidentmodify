import contextlib
import logging
from collections.abc import Generator
from dataclasses import asdict
from enum import Enum
from typing import Any, cast

import dacite
from google.api_core.exceptions import AlreadyExists
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import CollectionReference, DocumentReference, DocumentSnapshot
from google.cloud.firestore_v1.base_aggregation import AggregationResult

from models import HistoryEntry, Incident
from repositories import IncidentRepository


class FirestoreIncidentRepository(IncidentRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def doc_to_incident(self, doc: DocumentSnapshot) -> Incident:
        client_id = cast(DocumentReference, cast(CollectionReference, cast(DocumentReference, doc.reference).parent).parent).id
        return dacite.from_dict(
            data_class=Incident,
            data={
                **cast(dict[str, Any], doc.to_dict()),
                'id': doc.id,
                'client_id': client_id,
            },
            config=dacite.Config(cast=[Enum]),
        )

    def doc_to_history_entry(self, doc: DocumentSnapshot) -> HistoryEntry:
        incident_ref = cast(DocumentReference, cast(CollectionReference, cast(DocumentReference, doc.reference).parent).parent)
        client_ref = cast(DocumentReference, cast(CollectionReference, incident_ref.parent).parent)
        return dacite.from_dict(
            data_class=HistoryEntry,
            data={
                **cast(dict[str, Any], doc.to_dict()),
                'incident_id': incident_ref.id,
                'client_id': client_ref.id,
            },
            config=dacite.Config(cast=[Enum]),
        )

    def create(self, incident: Incident) -> None:
        incident_dict = asdict(incident)
        del incident_dict['id']
        del incident_dict['client_id']

        client_ref = self.db.collection('clients').document(incident.client_id)
        with contextlib.suppress(AlreadyExists):
            client_ref.create({})

        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident.id)
        incident_ref.create(incident_dict)

    def get(self, client_id: str, incident_id: str) -> Incident | None:
        client_ref = self.db.collection('clients').document(client_id)
        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident_id)
        doc = incident_ref.get()

        if not doc.exists:
            return None

        return self.doc_to_incident(doc)

    def append_history_entry(self, entry: HistoryEntry) -> None:
        history_dict = asdict(entry)
        del history_dict['client_id']
        del history_dict['incident_id']
        del history_dict['seq']

        if entry.seq is not None:
            raise ValueError('seq must be None when appending history entry')

        client_ref = self.db.collection('clients').document(entry.client_id)
        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(entry.incident_id)
        history_ref = cast(CollectionReference, incident_ref.collection('history'))
        next_seq = int(cast(AggregationResult, history_ref.count().get()[0][0]).value)  # type: ignore[no-untyped-call]
        entry_ref = history_ref.document(str(next_seq))

        entry.seq = next_seq
        history_dict['seq'] = next_seq
        entry_ref.create(history_dict)
        incident_ref.update({'last_modified': entry.date})

    def get_history(self, client_id: str, incident_id: str) -> Generator[HistoryEntry, None, None]:
        client_ref = self.db.collection('clients').document(client_id)
        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident_id)
        history_ref = cast(CollectionReference, incident_ref.collection('history'))
        query = history_ref.order_by('seq', direction='ASCENDING')

        docs = query.stream()

        for doc in docs:
            yield self.doc_to_history_entry(doc)

    def delete_all(self) -> None:
        self.db.recursive_delete(self.db.collection('clients'))

    def update(self, incident: Incident) -> None:
        incident_dict = asdict(incident)
        del incident_dict['id']
        del incident_dict['client_id']

        client_ref = self.db.collection('clients').document(incident.client_id)
        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident.id)

        doc = incident_ref.get()
        if not doc.exists:
            raise ValueError(f'Incident with ID {incident.id} not found for client {incident.client_id}.')

        incident_ref.update(incident_dict)
