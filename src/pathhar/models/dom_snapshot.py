"""DOM snapshot model."""

from pydantic import BaseModel, ConfigDict


class DOMSnapshot(BaseModel):
	model_config = ConfigDict(extra="forbid")

	url: str
	title: str | None = None
	timestamp: float
	html_summary: str | None = None
	element_count: int | None = None
