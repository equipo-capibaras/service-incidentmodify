import json
from collections.abc import Callable
from typing import Any

from flask import Blueprint, Response
from flask.views import MethodView


def class_route(blueprint: Blueprint, rule: str, **options: Any) -> Callable[[type[MethodView]], type[MethodView]]:  # noqa: ANN401
    def decorator(cls: type[MethodView]) -> type[MethodView]:
        blueprint.add_url_rule(rule, view_func=cls.as_view(cls.__name__), **options)
        return cls

    return decorator


def json_response(data: dict[str, Any] | list[dict[str, Any]], status: int) -> Response:
    return Response(json.dumps(data), status=status, mimetype='application/json')
