"""Infer JSON schemas from request/response bodies."""

from typing import Any


def infer_schema(obj: Any) -> dict[str, Any]:
	"""Infer a simple JSON schema from a Python object."""
	if obj is None:
		return {"type": "null"}
	if isinstance(obj, bool):
		return {"type": "boolean"}
	if isinstance(obj, int):
		return {"type": "integer"}
	if isinstance(obj, float):
		return {"type": "number"}
	if isinstance(obj, str):
		return {"type": "string"}
	if isinstance(obj, list):
		if not obj:
			return {"type": "array", "items": {}}
		item_schema = infer_schema(obj[0])
		return {"type": "array", "items": item_schema}
	if isinstance(obj, dict):
		properties = {}
		for key, value in obj.items():
			properties[key] = infer_schema(value)
		return {"type": "object", "properties": properties}
	return {"type": "string"}
