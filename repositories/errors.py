class RegistryIncidentError(Exception):
    def __init__(self, e: str) -> None:
        super().__init__(f'Error registering incident: {e}')
