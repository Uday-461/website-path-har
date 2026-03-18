"""Aggregate journey results into a complete site map."""

from datetime import UTC, datetime

from pathhar.models.har_summary import HarSummary
from pathhar.models.journey import JourneyResult
from pathhar.models.site_map import APISurface, Route, SiteMap
from pathhar.parsing.endpoint_extractor import group_endpoints


def aggregate_results(
	url: str,
	routes: list[Route],
	journey_results: list[JourneyResult],
	har_summaries: list[HarSummary],
	scan_duration: float,
) -> SiteMap:
	"""Merge all scan results into a SiteMap."""
	# Collect all API endpoints from HAR summaries
	all_endpoints = []
	total_requests = 0
	for summary in har_summaries:
		all_endpoints.extend(summary.endpoints)
		total_requests += summary.total_entries

	api_endpoints = group_endpoints(all_endpoints)
	unique_paths = len(set(ep.path_pattern for ep in api_endpoints))

	api_surface = APISurface(
		endpoints=api_endpoints,
		total_requests=total_requests,
		unique_paths=unique_paths,
	)

	return SiteMap(
		url=url,
		scan_timestamp=datetime.now(UTC),
		scan_duration_seconds=scan_duration,
		routes=routes,
		journeys=journey_results,
		api_surface=api_surface,
	)
