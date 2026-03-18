"""Main orchestrator — coordinates discovery, journey execution, and aggregation."""

import logging
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from pathhar.config import Config
from pathhar.engine.journey_agent import run_journey
from pathhar.models.har_summary import HarSummary
from pathhar.models.journey import JourneyDefinition, JourneyResult, JourneyStep
from pathhar.models.site_map import SiteMap
from pathhar.orchestrator.parallel import run_parallel
from pathhar.orchestrator.result_aggregator import aggregate_results
from pathhar.output.writer import write_site_map
from pathhar.parsing.har_parser import parse_har

logger = logging.getLogger(__name__)


def _validate_url(url: str) -> str:
	"""Ensure URL has a valid scheme."""
	if not url.startswith(("http://", "https://")):
		url = "https://" + url
	return url


def _create_run_dir(url: str, config: Config) -> tuple[Path, Path]:
	"""Create per-run output directories. Returns (run_dir, har_dir)."""
	domain = urlparse(url).netloc
	timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
	run_dir = config.output_dir / f"{domain}_{timestamp}"
	har_dir = run_dir / "har"
	har_dir.mkdir(parents=True, exist_ok=True)
	return run_dir, har_dir


async def scan(
	url: str,
	config: Config,
	auth_instruction: str | None = None,
) -> tuple[SiteMap, Path]:
	"""Run a complete site scan.

	1. Validate URL
	2. Run discovery agent
	3. Execute journeys (parallel)
	4. Parse HARs
	5. Aggregate and write output

	Returns (site_map, run_dir).
	"""
	from pathhar.engine.discovery_agent import run_discovery

	start_time = time.time()
	url = _validate_url(url)

	run_dir, har_dir = _create_run_dir(url, config)

	# Phase 1: Discovery
	logger.info("=== Phase 1: Discovery ===")
	routes, journeys = await run_discovery(url, config, auth_instruction)

	if not journeys:
		logger.warning("No journeys discovered — site map will only contain routes")

	# Phase 2: Journey execution
	logger.info("=== Phase 2: Journey Execution (%d journeys) ===", len(journeys))
	journey_coros = [
		run_journey(
			journey=j,
			journey_id=f"journey_{i:03d}",
			har_dir=har_dir,
			config=config,
			auth_instruction=auth_instruction,
		)
		for i, j in enumerate(journeys)
	]

	if config.max_concurrent_journeys == 1:
		# Sequential execution
		journey_results: list[JourneyResult] = []
		for coro in journey_coros:
			result = await coro
			journey_results.append(result)
	else:
		journey_results = await run_parallel(journey_coros, max_concurrent=config.max_concurrent_journeys)

	# Phase 3: Parse HARs
	logger.info("=== Phase 3: HAR Parsing ===")
	har_summaries: list[HarSummary] = []
	for result in journey_results:
		if result.har_path and result.har_path.exists():
			try:
				summary = parse_har(result.har_path)
				har_summaries.append(summary)
				logger.info(
					"Parsed %s: %d API entries, %d unique paths",
					result.har_path.name,
					summary.api_entries,
					len(summary.unique_path_patterns),
				)
			except Exception as e:
				logger.warning("Failed to parse %s: %s", result.har_path, e)

	# Phase 4: Aggregate
	logger.info("=== Phase 4: Aggregation ===")
	scan_duration = time.time() - start_time
	site_map = aggregate_results(
		url=url,
		routes=routes,
		journey_results=journey_results,
		har_summaries=har_summaries,
		scan_duration=scan_duration,
	)

	# Write output
	output_path = write_site_map(site_map, run_dir)
	logger.info("Scan complete in %.1fs. Output: %s", scan_duration, output_path)

	return site_map, run_dir


async def run_single_journey(
	url: str,
	steps: list[str],
	config: Config,
	auth_instruction: str | None = None,
) -> tuple[SiteMap, Path]:
	"""Run a single journey (no discovery phase).

	Returns (site_map, run_dir).
	"""
	start_time = time.time()
	url = _validate_url(url)

	run_dir, har_dir = _create_run_dir(url, config)

	journey_def = JourneyDefinition(
		name="CLI journey",
		entry_url=url,
		steps=[JourneyStep(description=s) for s in steps],
		requires_auth=auth_instruction is not None,
	)

	journey_id = "journey_000"
	result = await run_journey(
		journey=journey_def,
		journey_id=journey_id,
		har_dir=har_dir,
		config=config,
		auth_instruction=auth_instruction,
	)

	# Parse HAR
	har_summaries: list[HarSummary] = []
	if result.har_path and result.har_path.exists():
		try:
			summary = parse_har(result.har_path)
			har_summaries.append(summary)
		except Exception as e:
			logger.warning("Failed to parse %s: %s", result.har_path, e)

	# Aggregate
	scan_duration = time.time() - start_time
	site_map = aggregate_results(
		url=url,
		routes=[],
		journey_results=[result],
		har_summaries=har_summaries,
		scan_duration=scan_duration,
	)

	write_site_map(site_map, run_dir)

	return site_map, run_dir
