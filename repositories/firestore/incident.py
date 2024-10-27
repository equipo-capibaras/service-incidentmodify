import contextlib
import logging
from dataclasses import asdict
from typing import cast

from google.api_core.exceptions import AlreadyExists
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import CollectionReference
from google.cloud.firestore_v1.base_aggregation import AggregationResult

from models import HistoryEntry, Incident
from repositories import IncidentRepository


class FirestoreIncidentRepository(IncidentRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create(self, incident: Incident) -> None:
        incident_dict = asdict(incident)
        del incident_dict['id']
        del incident_dict['client_id']

        client_ref = self.db.collection('clients').document(incident.client_id)
        with contextlib.suppress(AlreadyExists):
            client_ref.create({})

        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident.id)
        incident_ref.create(incident_dict)

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

        history_dict['seq'] = next_seq
        entry_ref.create(history_dict)
        incident_ref.update({'last_modified': entry.date})

    def delete_all(self) -> None:
        self.db.recursive_delete(self.db.collection('clients'))
