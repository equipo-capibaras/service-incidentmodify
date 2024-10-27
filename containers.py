from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from gcp_microservice_utils import access_token_provider

from repositories.firestore import FirestoreIncidentRepository


class Container(DeclarativeContainer):
    wiring_config = WiringConfiguration(packages=['blueprints'])
    config = providers.Configuration()

    access_token = providers.Callable(access_token_provider)

    incident_repo = providers.ThreadSafeSingleton(FirestoreIncidentRepository, database=config.firestore.database)
