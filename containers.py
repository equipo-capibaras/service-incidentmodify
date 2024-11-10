from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from gcp_microservice_utils import access_token_provider

from repositories.firestore import FirestoreIncidentRepository
from repositories.rest import RestClientRepository, RestEmployeeRepository, RestUserRepository


class Container(DeclarativeContainer):
    wiring_config = WiringConfiguration(packages=['blueprints'])
    config = providers.Configuration()

    access_token = providers.Callable(access_token_provider)

    incident_repo = providers.ThreadSafeSingleton(FirestoreIncidentRepository, database=config.firestore.database)

    user_repo = providers.ThreadSafeSingleton(
        RestUserRepository,
        base_url=config.svc.user.url,
        token_provider=config.svc.user.token_provider,
    )

    employee_repo = providers.ThreadSafeSingleton(
        RestEmployeeRepository,
        base_url=config.svc.client.url,
        token_provider=config.svc.client.token_provider,
    )

    client_repo = providers.ThreadSafeSingleton(
        RestClientRepository,
        base_url=config.svc.client.url,
        token_provider=config.svc.client.token_provider,
    )
