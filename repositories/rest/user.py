from typing import Any, cast

import dacite
import requests

from models import User
from repositories import UserRepository

from .base import RestBaseRepository
from .util import TokenProvider


class RestUserRepository(UserRepository, RestBaseRepository):
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        RestBaseRepository.__init__(self, base_url, token_provider)

    def get(self, user_id: str, client_id: str) -> User | None:
        resp = self.authenticated_get(f'{self.base_url}/api/v1/users/{client_id}/{user_id}')

        if resp.status_code == requests.codes.ok:
            json = cast(dict[str, Any], resp.json())
            # Convert from json naming convention to Python naming convention
            json['client_id'] = json.pop('clientId')
            return dacite.from_dict(data_class=User, data=json)

        if resp.status_code == requests.codes.not_found:
            return None

        self.unexpected_error(resp)  # noqa: RET503
