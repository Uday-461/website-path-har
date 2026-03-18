"""Discovery agent — explores a website to find routes and define journeys."""

import logging

from browser_use import Agent, BrowserProfile, BrowserSession

from pathhar.config import Config
from pathhar.engine.custom_tools import DiscoveryState, create_discovery_tools
from pathhar.engine.llm_factory import create_llm
from pathhar.models.journey import JourneyDefinition
from pathhar.models.site_map import Route

logger = logging.getLogger(__name__)

DISCOVERY_PROMPT = """\
You are a website exploration agent. Your goal is to thoroughly discover all pages, \
routes, and user journeys on the website at {url}.

Instructions:
1. Start at the given URL and systematically explore the site
2. Click on navigation links, menus, buttons, and footer links
3. For each distinct page you find, call `report_route` with the URL, title, and page type
4. After exploring, define user journeys using `report_journey`:
   - Each journey is a sequence of steps a user would take (e.g., "search for a product", "add to cart", "checkout")
   - Separate step descriptions with | (pipe character)
   - Include journeys for: navigation, search, forms, authentication, key workflows
5. Use `mark_explored` to track visited URLs and avoid revisiting
6. Use `is_explored` to check before navigating to a URL

Page types: home, listing, detail, search, form, auth, checkout, settings, about, error, other

Explore at least 10-15 pages if available. Define at least 3-5 journeys.
{auth_section}
When you have thoroughly explored the site, use the `done` action.
"""


async def run_discovery(
	url: str,
	config: Config,
	auth_instruction: str | None = None,
) -> tuple[list[Route], list[JourneyDefinition]]:
	"""Run the discovery agent to map routes and define journeys."""
	state = DiscoveryState()
	tools = create_discovery_tools(state)
	llm = create_llm(config)

	auth_section = ""
	if auth_instruction:
		auth_section = f"\nAuth: {auth_instruction}\n"

	task = DISCOVERY_PROMPT.format(url=url, auth_section=auth_section)

	profile = BrowserProfile(headless=config.headless)
	session = BrowserSession(browser_profile=profile)

	agent = Agent(
		task=task,
		llm=llm,
		browser_session=session,
		tools=tools,
		use_vision="auto",
		max_failures=3,
		max_actions_per_step=5,
	)

	try:
		logger.info("Starting discovery for %s", url)
		await agent.run()
		logger.info(
			"Discovery complete: %d routes, %d journeys",
			len(state.routes),
			len(state.journeys),
		)
	finally:
		await session.stop()

	return state.routes, state.journeys
