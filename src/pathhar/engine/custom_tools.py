"""Custom browser-use tools for discovery and journey execution."""

import logging
import time

from browser_use import BrowserSession, Tools

from pathhar.models.dom_snapshot import DOMSnapshot
from pathhar.models.journey import JourneyDefinition, JourneyStep
from pathhar.models.site_map import Route

logger = logging.getLogger(__name__)


class DiscoveryState:
	"""Mutable state shared with discovery agent tools."""

	def __init__(self) -> None:
		self.routes: list[Route] = []
		self.journeys: list[JourneyDefinition] = []
		self.explored_urls: set[str] = set()


class JourneyState:
	"""Mutable state shared with journey agent tools."""

	def __init__(self) -> None:
		self.dom_snapshots: list[DOMSnapshot] = []
		self.steps_log: list[str] = []


def create_discovery_tools(state: DiscoveryState) -> Tools:
	"""Create custom tools for the discovery agent."""
	tools = Tools()

	@tools.registry.action("Report a discovered route/page on the website")
	async def report_route(
		url: str,
		title: str = "",
		description: str = "",
		page_type: str = "",
	) -> str:
		route = Route(
			url=url,
			title=title or None,
			description=description or None,
			page_type=page_type or None,
		)
		state.routes.append(route)
		state.explored_urls.add(url)
		logger.info("Discovered route: %s (%s)", url, title)
		return f"Route recorded: {url}"

	@tools.registry.action("Define a user journey to execute later. Steps should describe what to do.")
	async def report_journey(
		name: str,
		entry_url: str,
		step_descriptions: str,
		category: str = "",
		requires_auth: bool = False,
	) -> str:
		steps = [JourneyStep(description=s.strip()) for s in step_descriptions.split("|") if s.strip()]
		journey = JourneyDefinition(
			name=name,
			entry_url=entry_url,
			steps=steps,
			category=category or None,
			requires_auth=requires_auth,
		)
		state.journeys.append(journey)
		logger.info("Defined journey: %s (%d steps)", name, len(steps))
		return f"Journey '{name}' recorded with {len(steps)} steps"

	@tools.registry.action("Check if a URL has already been explored")
	async def is_explored(url: str) -> str:
		if url in state.explored_urls:
			return f"Yes, {url} has already been explored"
		return f"No, {url} has not been explored yet"

	@tools.registry.action("Mark a URL as explored to avoid revisiting")
	async def mark_explored(url: str) -> str:
		state.explored_urls.add(url)
		return f"Marked {url} as explored"

	return tools


def create_journey_tools(state: JourneyState) -> Tools:
	"""Create custom tools for journey execution agents."""
	tools = Tools()

	@tools.registry.action("Capture a DOM snapshot of the current page for analysis")
	async def capture_dom_snapshot(
		browser_session: BrowserSession,
	) -> str:
		try:
			browser_state = await browser_session.get_browser_state_summary()
			dom_text = browser_state.dom_state.llm_representation()
			element_count = len(browser_state.dom_state.selector_map) if browser_state.dom_state.selector_map else 0
			snapshot = DOMSnapshot(
				url=browser_state.url,
				title=browser_state.title,
				timestamp=time.time(),
				html_summary=dom_text[:2000] if dom_text else None,
				element_count=element_count,
			)
			state.dom_snapshots.append(snapshot)
			state.steps_log.append(f"DOM snapshot captured at {browser_state.url}")
			return f"Snapshot captured: {browser_state.url} ({element_count} elements)"
		except Exception as e:
			logger.warning("Failed to capture DOM snapshot: %s", e)
			return f"Failed to capture snapshot: {e}"

	@tools.registry.action("Log a journey step that was completed")
	async def log_step(description: str) -> str:
		state.steps_log.append(description)
		return f"Step logged: {description}"

	return tools
