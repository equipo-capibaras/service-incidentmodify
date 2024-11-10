from models import Employee


class EmployeeRepository:
    def get(self, employee_id: str, client_id: str) -> Employee | None:
        raise NotImplementedError  # pragma: no cover
