"""Application configuration via environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
	model_config = {"env_file": ".env", "extra": "ignore"}

	openrouter_api_key: str = Field(description="OpenRouter API key")
	llm_model: str = Field(
		default="anthropic/claude-sonnet-4-20250514",
		description="OpenRouter model identifier",
	)
	max_concurrent_journeys: int = Field(
		default=3,
		ge=1,
		le=10,
		description="Max parallel journey executions",
	)
	headless: bool = Field(default=True, description="Run browsers in headless mode")
	output_dir: Path = Field(
		default=Path("./output"),
		description="Directory for scan output",
	)
