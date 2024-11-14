from datetime import UTC, datetime

from models import Action, Channel, HistoryEntry, Incident

CLIENT_ID_GIGATEL = '9a652818-342e-4771-84cf-39c20a29264d'
AGENT_ID_GIGATEL_JULIAN = '0abad006-921c-4e09-b2a6-10713b71571f'
USER_ID_GIGATEL_MARIA = 'b713f559-cae5-4db3-992a-d3553fb25000'
USER_ID_GIGATEL_JUAN = 'e7bcf651-c7d7-4dfa-9633-14598673faff'

CLIENT_ID_UNIVERSO = 'acfa53b4-58f3-46e8-809b-19ef52b437ed'
AGENT_ID_UNIVERSO_JOAO = '7ecbab00-726e-4c21-b7ea-17fa2ace7b1d'
USER_ID_UNIVERSO_RAFAEL = '46f94cd1-8494-4e96-b308-80d7705868be'

incident1 = Incident(
    id='36e3344d-aa5b-4c5a-88ef-a7eb8abe27d8',
    client_id=CLIENT_ID_GIGATEL,
    name='Cobro incorrecto',
    channel=Channel.WEB,
    reported_by=USER_ID_GIGATEL_MARIA,
    created_by=AGENT_ID_GIGATEL_JULIAN,
    assigned_to=AGENT_ID_GIGATEL_JULIAN,
)

incident1_history = [
    HistoryEntry(
        incident_id=incident1.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 18, 14, 26, 22, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'He recibido mi factura de septiembre y aparece un cobro adicional por un servicio que no contraté. '
            'El servicio en cuestión se llama "Asistencia Técnica Premium", pero yo nunca solicité ni autoricé este servicio. '
            'Me di cuenta del cobro hoy, 10 de septiembre, al revisar el detalle de la factura. '
            'Solicito que se revise mi cuenta y se realice el ajuste correspondiente en el menor tiempo posible.'
        ),
    ),
    HistoryEntry(
        incident_id=incident1.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 18, 17, 31, 57, tzinfo=UTC),
        action=Action.CLOSED,
        description='Se hizó el ajuste en la tarjeta registrada para los pagos.',
    ),
]

incident2 = Incident(
    id='eccc588b-df31-4105-9940-86937059aff8',
    client_id=CLIENT_ID_GIGATEL,
    name='Internet no funciona',
    channel=Channel.MOBILE,
    reported_by=USER_ID_GIGATEL_MARIA,
    created_by=USER_ID_GIGATEL_MARIA,
    assigned_to=AGENT_ID_GIGATEL_JULIAN,
)

incident2_history = [
    HistoryEntry(
        incident_id=incident2.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 20, 14, 26, 22, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'No tengo acceso a Internet en mi hogar. El módem está encendido, pero no hay conexión. '
            'He reiniciado el equipo varias veces y verificado que el servicio esté activo en mi cuenta, '
            'pero el problema persiste. Solicito una revisión urgente del servicio.'
        ),
    ),
    HistoryEntry(
        incident_id=incident2.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 21, 8, 11, 41, tzinfo=UTC),
        action=Action.ESCALATED,
        description=(
            'Se ha llamado al cliente para verificar si pudo solucionar el problema con las recomendaciones '
            'planteadas por la IA, pero comenta seguir con el problema, por lo cuál se le enviará un técnico '
            'en un plazo de 2 días.'
        ),
    ),
]

incident3 = Incident(
    id='8b51a60c-07d3-4ed3-85b9-352ded0abec5',
    client_id=CLIENT_ID_GIGATEL,
    name='Fallo servicios',
    channel=Channel.EMAIL,
    reported_by=USER_ID_GIGATEL_MARIA,
    created_by=USER_ID_GIGATEL_MARIA,
    assigned_to=AGENT_ID_GIGATEL_JULIAN,
)

incident3_history = [
    HistoryEntry(
        incident_id=incident3.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 23, 19, 46, 40, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'Desde hace 3 días no tengo acceso a los servicios de televisión, Internet y telefonía. '
            'He revisado el estado de la conexión en el módem y en la caja de distribución, '
            'pero no he encontrado ninguna anomalía. Solicito una revisión urgente del servicio.'
        ),
    ),
]

incident4 = Incident(
    id='8a7a7fd0-5e36-4f27-b37e-745d4042279f',
    client_id=CLIENT_ID_GIGATEL,
    name='Fuga de agua del segundo piso',
    channel=Channel.WEB,
    reported_by=USER_ID_GIGATEL_JUAN,
    created_by=AGENT_ID_GIGATEL_JULIAN,
    assigned_to=AGENT_ID_GIGATEL_JULIAN,
)

incident4_history = [
    HistoryEntry(
        incident_id=incident4.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 19, 14, 26, 22, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'En el baño del segundo piso hay una tubería que está echando agua como una fuente. '
            'El agua ya se está saliendo al pasillo.'
        ),
    ),
    HistoryEntry(
        incident_id=incident4.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 19, 17, 31, 57, tzinfo=UTC),
        action=Action.CLOSED,
        description='Un fontanero ha acudido al lugar y ha reparado la tubería rota.',
    ),
]

incident5 = Incident(
    id='c749589b-ce03-4e47-9c95-8def0f600276',
    client_id=CLIENT_ID_GIGATEL,
    name='Sin conexión a Internet',
    channel=Channel.MOBILE,
    reported_by=USER_ID_GIGATEL_JUAN,
    created_by=USER_ID_GIGATEL_JUAN,
    assigned_to=AGENT_ID_GIGATEL_JULIAN,
)

incident5_history = [
    HistoryEntry(
        incident_id=incident5.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 20, 17, 26, 22, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'No tengo acceso a Internet en mi hogar. El módem está encendido, pero no hay conexión. '
            'He reiniciado el equipo varias veces y verificado que el servicio esté activo en mi cuenta, '
            'pero el problema persiste. Solicito una revisión urgente del servicio.'
        ),
    ),
    HistoryEntry(
        incident_id=incident5.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 21, 21, 11, 41, tzinfo=UTC),
        action=Action.ESCALATED,
        description=(
            'Se ha llamado al cliente para verificar si pudo solucionar el problema con las recomendaciones '
            'planteadas por la IA, pero comenta seguir con el problema, por lo cuál se le enviará un técnico '
            'en un plazo de 2 días.'
        ),
    ),
]

incident6 = Incident(
    id='e14faa4b-8f93-4c6e-9d9a-bd2bf8fbe12e',
    client_id=CLIENT_ID_GIGATEL,
    name='Servicio de televisión interrumpido',
    channel=Channel.EMAIL,
    reported_by=USER_ID_GIGATEL_JUAN,
    created_by=USER_ID_GIGATEL_JUAN,
    assigned_to=AGENT_ID_GIGATEL_JULIAN,
)

incident6_history = [
    HistoryEntry(
        incident_id=incident6.id,
        client_id=CLIENT_ID_GIGATEL,
        date=datetime(2024, 10, 23, 22, 46, 40, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'Desde hace 3 días no tengo acceso a los servicios de televisión, Internet y telefonía. '
            'He revisado el estado de la conexión en el módem y en la caja de distribución, '
            'pero no he encontrado ninguna anomalía. Solicito una revisión urgente del servicio.'
        ),
    ),
]

incident7 = Incident(
    id='41573516-fddd-4896-a0ce-16125f8dea1e',
    client_id=CLIENT_ID_UNIVERSO,
    name='Cobro incorrecto',
    channel=Channel.WEB,
    reported_by=USER_ID_UNIVERSO_RAFAEL,
    created_by=AGENT_ID_UNIVERSO_JOAO,
    assigned_to=AGENT_ID_UNIVERSO_JOAO,
)

incident7_history = [
    HistoryEntry(
        incident_id=incident7.id,
        client_id=CLIENT_ID_UNIVERSO,
        date=datetime(2024, 10, 18, 14, 26, 22, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'He recibido mi factura de septiembre y aparece un cobro adicional por un servicio que no contraté. '
            'El servicio en cuestión se llama "Asistencia Técnica Premium", pero yo nunca solicité ni autoricé este servicio. '
            'Me di cuenta del cobro hoy, 10 de septiembre, al revisar el detalle de la factura. '
            'Solicito que se revise mi cuenta y se realice el ajuste correspondiente en el menor tiempo posible.'
        ),
    ),
    HistoryEntry(
        incident_id=incident7.id,
        client_id=CLIENT_ID_UNIVERSO,
        date=datetime(2024, 10, 18, 14, 26, 22, tzinfo=UTC),
        action=Action.AI_RESPONSE,
        description=(
            'Si estás viendo un cargo duplicado en tu factura, primero revisa el historial de pagos para confirmar. A veces, '
            'los cargos duplicados se corrigen automáticamente en 24 horas. Si el cargo sigue apareciendo, puedes iniciar un '
            'reclamo a través del portal de pagos para solicitar el reembolso. Un agente revisará tu solicitud y te '
            'notificará el estado del reembolso por correo electrónico.'
        ),
    ),
    HistoryEntry(
        incident_id=incident7.id,
        client_id=CLIENT_ID_UNIVERSO,
        date=datetime(2024, 10, 18, 15, 11, 41, tzinfo=UTC),
        action=Action.ESCALATED,
        description=(
            'Se ha llamado al cliente para verificar si pudo solucionar el problema con las recomendaciones '
            'planteadas por la IA, pero comenta seguir con el problema.'
        ),
    ),
    HistoryEntry(
        incident_id=incident7.id,
        client_id=CLIENT_ID_UNIVERSO,
        date=datetime(2024, 10, 18, 17, 31, 57, tzinfo=UTC),
        action=Action.CLOSED,
        description='Se hizó el ajuste en la tarjeta registrada para los pagos.',
    ),
]

incident8 = Incident(
    id='443d1b06-7f81-4366-b0b3-2004d6a680f1',
    client_id=CLIENT_ID_UNIVERSO,
    name='Cargo indebido',
    channel=Channel.WEB,
    reported_by=USER_ID_UNIVERSO_RAFAEL,
    created_by=AGENT_ID_UNIVERSO_JOAO,
    assigned_to=AGENT_ID_UNIVERSO_JOAO,
)

incident8_history = [
    HistoryEntry(
        incident_id=incident8.id,
        client_id=CLIENT_ID_UNIVERSO,
        date=datetime(2024, 10, 27, 14, 26, 22, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'He recibido mi factura de septiembre y aparece un cobro adicional por un servicio que no contraté. '
            'El servicio en cuestión se llama "Asistencia Técnica Premium", pero yo nunca solicité ni autoricé este servicio. '
            'Me di cuenta del cobro hoy, 10 de septiembre, al revisar el detalle de la factura. '
            'Solicito que se revise mi cuenta y se realice el ajuste correspondiente en el menor tiempo posible.'
        ),
    ),
    HistoryEntry(
        incident_id=incident8.id,
        client_id=CLIENT_ID_UNIVERSO,
        date=datetime(2024, 10, 27, 14, 27, 14, tzinfo=UTC),
        action=Action.AI_RESPONSE,
        description=(
            'Si estás viendo un cargo duplicado en tu factura, primero revisa el historial de pagos para confirmar. A veces, '
            'los cargos duplicados se corrigen automáticamente en 24 horas. Si el cargo sigue apareciendo, puedes iniciar un '
            'reclamo a través del portal de pagos para solicitar el reembolso. Un agente revisará tu solicitud y te '
            'notificará el estado del reembolso por correo electrónico.'
        ),
    ),
]

incidents = [incident1, incident2, incident3, incident4, incident5, incident6, incident7, incident8]
history = {
    incident1.id: incident1_history,
    incident2.id: incident2_history,
    incident3.id: incident3_history,
    incident4.id: incident4_history,
    incident5.id: incident5_history,
    incident6.id: incident6_history,
    incident7.id: incident7_history,
    incident8.id: incident8_history,
}
