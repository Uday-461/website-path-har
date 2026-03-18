"""Journey definition and result models."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from pathhar.models.dom_snapshot import DOMSnapshot


class JourneyStep(BaseModel):
	model_config = ConfigDict(extra="forbid")

	description: str
	expected_url_pattern: str | None = None


class JourneyDefinition(BaseModel):
	model_config = ConfigDict(extra="forbid")

	name: str
	category: str | None = None
	entry_url: str
	steps: list[JourneyStep]
	requires_auth: bool = False


class JourneyResult(BaseModel):
	model_config = ConfigDict(extra="forbid")

	journey_id: str
	name: str
	success: bool
	steps_log: list[str] = []
	har_path: Path | None = None
	dom_snapshots: list[DOMSnapshot] = []
	error: str | None = None
