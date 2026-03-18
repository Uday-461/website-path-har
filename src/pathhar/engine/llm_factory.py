"""Create LLM instances for browser-use agents."""

from browser_use.llm.openrouter.chat import ChatOpenRouter

from pathhar.config import Config


def create_llm(config: Config) -> ChatOpenRouter:
	"""Create a ChatOpenRouter instance for LLM access via OpenRouter."""
	return ChatOpenRouter(
		model=config.llm_model,
		api_key=config.openrouter_api_key,
	)
