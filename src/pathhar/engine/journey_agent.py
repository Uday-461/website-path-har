"""Journey agent — executes a user journey with HAR recording and DOM snapshots."""

import logging
from pathlib import Path

from browser_use import Agent, BrowserProfile, BrowserSession

from pathhar.config import Config
from pathhar.engine.custom_tools import JourneyState, create_journey_tools
from pathhar.engine.llm_factory import create_llm
from pathhar.models.journey import JourneyDefinition, JourneyResult

logger = logging.getLogger(__name__)

JOURNEY_PROMPT = """\
You are a website testing agent. Execute the following user journey precisely.

Journey: {name}
Starting URL: {entry_url}

Steps to perform:
{steps_text}

Instructions:
1. Navigate to the starting URL
2. Execute each step in order
3. After each significant page change, call `capture_dom_snapshot` to record the page state
4. Call `log_step` after completing each step
5. If a step fails, try reasonable alternatives before giving up
{auth_section}
When all steps are complete (or you cannot proceed), use the `done` action.
"""


async def run_journey(
	journey: JourneyDefinition,
	journey_id: str,
	har_dir: Path,
	config: Config,
	auth_instruction: str | None = None,
) -> JourneyResult:
	"""Execute a single journey with HAR recording."""
	state = JourneyState()
	tools = create_journey_tools(state)
	llm = create_llm(config)

	har_path = har_dir / f"{journey_id}.har"

	steps_text = "\n".join(f"{i + 1}. {step.description}" for i, step in enumerate(journey.steps))

	auth_section = ""
	if auth_instruction and journey.requires_auth:
		auth_section = f"\nAuth: {auth_instruction}\n"

	task = JOURNEY_PROMPT.format(
		name=journey.name,
		entry_url=journey.entry_url,
		steps_text=steps_text,
		auth_section=auth_section,
	)

	profile = BrowserProfile(
		headless=config.headless,
		record_har_path=str(har_path),
	)
	session = BrowserSession(browser_profile=profile)

	try:
		agent = Agent(
			task=task,
			llm=llm,
			browser_session=session,
			tools=tools,
			use_vision="auto",
			max_failures=3,
			max_actions_per_step=5,
		)

		logger.info("Starting journey: %s", journey.name)
		result = await agent.run()
		success = not result.has_errors() if hasattr(result, "has_errors") else True
		logger.info("Journey '%s' complete (success=%s)", journey.name, success)

		return JourneyResult(
			journey_id=journey_id,
			name=journey.name,
			success=success,
			steps_log=state.steps_log,
			har_path=har_path if har_path.exists() else None,
			dom_snapshots=state.dom_snapshots,
		)
	except Exception as e:
		logger.error("Journey '%s' failed: %s", journey.name, e)
		return JourneyResult(
			journey_id=journey_id,
			name=journey.name,
			success=False,
			steps_log=state.steps_log,
			har_path=har_path if har_path.exists() else None,
			dom_snapshots=state.dom_snapshots,
			error=str(e),
		)
	finally:
		await session.stop()
