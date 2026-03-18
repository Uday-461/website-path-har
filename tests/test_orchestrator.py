"""Tests for orchestrator utilities."""

from pathhar.models.har_summary import EndpointInfo, HarSummary
from pathhar.models.journey import JourneyResult
from pathhar.models.site_map import Route
from pathhar.orchestrator.result_aggregator import aggregate_results
from pathhar.orchestrator.service import _validate_url


class TestValidateUrl:
	def test_adds_https(self):
		assert _validate_url("example.com") == "https://example.com"

	def test_preserves_https(self):
		assert _validate_url("https://example.com") == "https://example.com"

	def test_preserves_http(self):
		assert _validate_url("http://localhost:8080") == "http://localhost:8080"


class TestAggregateResults:
	def test_empty_results(self):
		site_map = aggregate_results(
			url="https://example.com",
			routes=[],
			journey_results=[],
			har_summaries=[],
			scan_duration=1.0,
		)
		assert site_map.url == "https://example.com"
		assert len(site_map.routes) == 0
		assert len(site_map.journeys) == 0
		assert site_map.api_surface.total_requests == 0

	def test_with_routes_and_summaries(self):
		routes = [
			Route(url="https://example.com/", title="Home"),
			Route(url="https://example.com/about", title="About"),
		]
		journey_results = [
			JourneyResult(
				journey_id="j_001",
				name="Browse products",
				success=True,
			)
		]
		har_summaries = [
			HarSummary(
				har_path="test.har",
				total_entries=10,
				api_entries=5,
				static_entries=5,
				endpoints=[
					EndpointInfo(
						method="GET",
						url="https://example.com/api/products/1",
						path_pattern="/api/products/{id}",
						status=200,
					),
					EndpointInfo(
						method="GET",
						url="https://example.com/api/products/2",
						path_pattern="/api/products/{id}",
						status=200,
					),
				],
				unique_path_patterns=["/api/products/{id}"],
			)
		]

		site_map = aggregate_results(
			url="https://example.com",
			routes=routes,
			journey_results=journey_results,
			har_summaries=har_summaries,
			scan_duration=30.0,
		)

		assert len(site_map.routes) == 2
		assert len(site_map.journeys) == 1
		assert site_map.api_surface.total_requests == 10
		# Two GET /api/products/{id} entries should be grouped into one endpoint
		assert len(site_map.api_surface.endpoints) == 1
		assert site_map.api_surface.endpoints[0].path_pattern == "/api/products/{id}"
		assert site_map.api_surface.endpoints[0].status_codes == [200]
