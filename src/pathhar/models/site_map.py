"""Site map and API surface models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from pathhar.models.journey import JourneyResult


class Route(BaseModel):
	model_config = ConfigDict(extra="forbid")

	url: str
	title: str | None = None
	description: str | None = None
	page_type: str | None = None
	linked_from: list[str] = []


class APIEndpoint(BaseModel):
	model_config = ConfigDict(extra="forbid")

	method: str
	path_pattern: str
	status_codes: list[int] = []
	request_content_type: str | None = None
	response_content_type: str | None = None
	request_schema: dict | None = None
	response_schema: dict | None = None
	sample_url: str | None = None


class APISurface(BaseModel):
	model_config = ConfigDict(extra="forbid")

	endpoints: list[APIEndpoint] = []
	total_requests: int = 0
	unique_paths: int = 0


class SiteMap(BaseModel):
	model_config = ConfigDict(extra="forbid")

	url: str
	scan_timestamp: datetime
	scan_duration_seconds: float
	routes: list[Route] = []
	journeys: list[JourneyResult] = []
	api_surface: APISurface = APISurface()
