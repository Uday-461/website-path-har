"""Discovery agent — explores a website to find routes and define journeys."""

import logging
from urllib.parse import urlparse

from browser_use import Agent, BrowserProfile, BrowserSession

from pathhar.config import Config
from pathhar.engine.custom_tools import DiscoveryState, create_discovery_tools
from pathhar.engine.llm_factory import create_llm
from pathhar.models.journey import JourneyDefinition
from pathhar.models.site_map import Route

logger = logging.getLogger(__name__)

DISCOVERY_PROMPT = """\
You are a website exploration agent. Your goal is to discover all pages, routes, and \
user journeys on the website at {url}.

IMPORTANT CONSTRAINTS:
- Stay ONLY on the domain: {domain}
- Do NOT follow links to external domains (e.g. social media, third-party sites)
- If a link takes you off {domain}, go back immediately

Instructions:
1. Start at {url} and systematically explore the site
2. For each distinct page you find on {domain}, call `report_route` with the URL, title, and page type
3. Click navigation links, menus, buttons, and footer links — but only if they stay on {domain}
4. Use `mark_explored` after visiting each URL to avoid revisiting
5. You MUST call `report_journey` at least once before finishing — define the key user journeys:
   - Describe 3-5 realistic user workflows (e.g. "search → product → cart → checkout")
   - Separate each step with | (pipe character)
   - Base journeys on what you actually observed on the site

Page types: home, listing, detail, search, form, auth, checkout, settings, about, error, other
{auth_section}
When done exploring, call `report_journey` for each journey, then call `done`.
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

	domain = urlparse(url).netloc

	auth_section = ""
	if auth_instruction:
		auth_section = f"\nAuth: {auth_instruction}\n"

	task = DISCOVERY_PROMPT.format(url=url, domain=domain, auth_section=auth_section)

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
		await agent.run(max_steps=config.max_discovery_steps)
		logger.info(
			"Discovery complete: %d routes, %d journeys",
			len(state.routes),
			len(state.journeys),
		)
	finally:
		await session.stop()

	return state.routes, state.journeys
