from flask import Blueprint, Response, request
from flask.views import MethodView
from marshmallow import ValidationError

from containers import Container

blp = Blueprint('Incident', __name__)