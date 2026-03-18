"""HAR parsing result models."""

from pydantic import BaseModel, ConfigDict


class EndpointInfo(BaseModel):
	model_config = ConfigDict(extra="forbid")

	method: str
	url: str
	path_pattern: str
	status: int
	content_type: str | None = None
	request_size: int | None = None
	response_size: int | None = None
	duration_ms: float | None = None
	request_body: dict | None = None
	response_body: dict | None = None


class HarSummary(BaseModel):
	model_config = ConfigDict(extra="forbid")

	har_path: str
	total_entries: int
	api_entries: int
	static_entries: int
	endpoints: list[EndpointInfo] = []
	unique_path_patterns: list[str] = []
