import os

from flask import Flask
from gcp_microservice_utils import GcpAuthToken, setup_apigateway, setup_cloud_logging, setup_cloud_trace

from blueprints import BlueprintBackup, BlueprintHealth, BlueprintIncident, BlueprintReset
from containers import Container


class FlaskMicroservice(Flask):
    container: Container


def create_app() -> FlaskMicroservice:
    if os.getenv('ENABLE_CLOUD_LOGGING') == '1':
        setup_cloud_logging()  # pragma: no cover

    app = FlaskMicroservice(__name__)
    app.container = Container()

    app.container.config.firestore.database.from_env('FIRESTORE_DATABASE', '(default)')

    if 'K_SERVICE' in os.environ:  # pragma: no cover
        import google.auth

        _, project_id = google.auth.default()  # type: ignore[no-untyped-call]
        app.container.config.project_id.from_value(project_id)

    if os.getenv('ENABLE_CLOUD_TRACE') == '1':
        setup_cloud_trace(app)  # pragma: no cover

    setup_apigateway(app)

    if 'USER_SVC_URL' in os.environ:  # pragma: no cover
        app.container.config.svc.user.url.from_env('USER_SVC_URL')

        if 'USER_SVC_TOKEN' in os.environ:
            app.container.config.svc.user.token_provider.from_value(
                type('TokenProvider', (object,), {'get_token': lambda: os.environ['USER_SVC_TOKEN']})
            )
        elif 'USE_CLOUD_TOKEN_PROVIDER' in os.environ:
            app.container.config.svc.user.token_provider.from_value(GcpAuthToken(os.environ['USER_SVC_URL']))

    if 'CLIENT_SVC_URL' in os.environ:  # pragma: no cover
        app.container.config.svc.client.url.from_env('CLIENT_SVC_URL')

        if 'CLIENT_SVC_TOKEN' in os.environ:
            app.container.config.svc.client.token_provider.from_value(
                type('TokenProvider', (object,), {'get_token': lambda: os.environ['CLIENT_SVC_TOKEN']})
            )
        elif 'USE_CLOUD_TOKEN_PROVIDER' in os.environ:
            app.container.config.svc.client.token_provider.from_value(GcpAuthToken(os.environ['CLIENT_SVC_URL']))

    app.register_blueprint(BlueprintBackup)
    app.register_blueprint(BlueprintHealth)
    app.register_blueprint(BlueprintReset)
    app.register_blueprint(BlueprintIncident)

    return app
