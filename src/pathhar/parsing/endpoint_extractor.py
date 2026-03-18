"""Group and deduplicate API endpoints by path pattern."""

from collections import defaultdict

from pathhar.models.har_summary import EndpointInfo
from pathhar.models.site_map import APIEndpoint


def group_endpoints(endpoints: list[EndpointInfo]) -> list[APIEndpoint]:
	"""Group raw endpoint entries into deduplicated API endpoints."""
	groups: dict[tuple[str, str], list[EndpointInfo]] = defaultdict(list)

	for ep in endpoints:
		key = (ep.method, ep.path_pattern)
		groups[key].append(ep)

	api_endpoints: list[APIEndpoint] = []
	for (method, pattern), entries in sorted(groups.items()):
		status_codes = sorted(set(e.status for e in entries))
		content_types = [e.content_type for e in entries if e.content_type]
		response_ct = content_types[0] if content_types else None

		# Use first entry with a request body as request content type sample
		req_ct = None
		for e in entries:
			if e.request_body:
				req_ct = "application/json"
				break

		api_endpoints.append(
			APIEndpoint(
				method=method,
				path_pattern=pattern,
				status_codes=status_codes,
				request_content_type=req_ct,
				response_content_type=response_ct,
				sample_url=entries[0].url,
			)
		)

	return api_endpoints
