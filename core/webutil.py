"""Flask helpers shared by all blueprints.

Keeps the wire format of the previous FastAPI version so the built
frontend needs no changes: errors are JSON bodies shaped
{"detail": ...}, request bodies are validated with the same pydantic
schemas, and responses are serialized from pydantic models.
"""
import json
from datetime import date, datetime
from enum import Enum

from flask import Response, jsonify, request
from pydantic import BaseModel, TypeAdapter, ValidationError


class HTTPException(Exception):
    """API error carrying (status_code, detail)."""

    def __init__(self, status_code: int, detail=""):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def parse(model):
    """Validate the request JSON body against a pydantic model or a
    type expression such as list[ClaimIn]. Raises HTTPException(422)
    with pydantic's error list on invalid input."""
    data = request.get_json(silent=True)
    if data is None:
        raise HTTPException(422, "A JSON body is required")
    try:
        if isinstance(model, type) and issubclass(model, BaseModel):
            return model.model_validate(data)
        return TypeAdapter(model).validate_python(data)
    except ValidationError as exc:
        raise HTTPException(422, json.loads(exc.json()))


def jsonable(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [jsonable(v) for v in obj]
    return obj


def respond(obj=None, status: int = 200):
    if obj is None and status == 204:
        return Response(status=204)
    return jsonify(jsonable(obj)), status


def register_errors(app):
    @app.errorhandler(HTTPException)
    def _api_error(exc: HTTPException):
        return jsonify({"detail": jsonable(exc.detail)}), exc.status_code
