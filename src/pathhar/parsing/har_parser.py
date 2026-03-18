"""Parse HAR files and extract API endpoint information."""

import json
import logging
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from pathhar.models.har_summary import EndpointInfo, HarSummary

logger = logging.getLogger(__name__)

STATIC_EXTENSIONS = frozenset(
	{
		".css",
		".js",
		".png",
		".jpg",
		".jpeg",
		".gif",
		".svg",
		".ico",
		".woff",
		".woff2",
		".ttf",
		".eot",
		".map",
		".webp",
		".avif",
	}
)

STATIC_CONTENT_TYPES = frozenset(
	{
		"text/css",
		"text/javascript",
		"application/javascript",
		"image/png",
		"image/jpeg",
		"image/gif",
		"image/svg+xml",
		"image/webp",
		"font/woff",
		"font/woff2",
	}
)


def is_static_request(url: str, content_type: str | None) -> bool:
	"""Check if a request is for a static asset."""
	parsed = urlparse(url)
	path = parsed.path.lower()
	if any(path.endswith(ext) for ext in STATIC_EXTENSIONS):
		return True
	if content_type:
		base_type = content_type.split(";")[0].strip().lower()
		if base_type in STATIC_CONTENT_TYPES:
			return True
	return False


def extract_path_pattern(url: str) -> str:
	"""Convert a URL to a path pattern, replacing IDs with placeholders.

	/api/products/123 -> /api/products/{id}
	/api/users/abc-def-ghi -> /api/users/{id}
	"""
	parsed = urlparse(url)
	segments = parsed.path.strip("/").split("/")
	pattern_segments = []
	for segment in segments:
		if re.match(r"^\d+$", segment):
			pattern_segments.append("{id}")
		elif re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", segment, re.IGNORECASE):
			pattern_segments.append("{uuid}")
		elif re.match(r"^[0-9a-f]{24}$", segment, re.IGNORECASE):
			pattern_segments.append("{id}")
		else:
			pattern_segments.append(segment)
	return "/" + "/".join(pattern_segments) if pattern_segments else "/"


def _try_parse_json(text: str | None) -> dict | None:
	"""Attempt to parse a string as JSON, return None on failure."""
	if not text:
		return None
	try:
		parsed = json.loads(text)
		if isinstance(parsed, dict):
			return parsed
	except (json.JSONDecodeError, TypeError):
		pass
	return None


def parse_har(har_path: str | Path) -> HarSummary:
	"""Parse a HAR file and extract endpoint summaries."""
	har_path = Path(har_path)
	with open(har_path) as f:
		har_data = json.load(f)

	entries = har_data.get("log", {}).get("entries", [])
	api_endpoints: list[EndpointInfo] = []
	static_count = 0

	for entry in entries:
		request = entry.get("request", {})
		response = entry.get("response", {})

		url = request.get("url", "")
		method = request.get("method", "GET")
		status = response.get("status", 0)

		response_content_type = response.get("content", {}).get("mimeType", "")

		if is_static_request(url, response_content_type):
			static_count += 1
			continue

		# Extract timing
		duration_ms = entry.get("time")

		# Extract body content
		request_body_text = request.get("postData", {}).get("text")
		response_body_text = response.get("content", {}).get("text")

		# Extract sizes
		request_size = request.get("bodySize")
		response_size = response.get("content", {}).get("size")

		endpoint = EndpointInfo(
			method=method,
			url=url,
			path_pattern=extract_path_pattern(url),
			status=status,
			content_type=response_content_type or None,
			request_size=request_size if request_size and request_size > 0 else None,
			response_size=response_size if response_size and response_size > 0 else None,
			duration_ms=duration_ms,
			request_body=_try_parse_json(request_body_text),
			response_body=_try_parse_json(response_body_text),
		)
		api_endpoints.append(endpoint)

	unique_patterns = sorted(set(ep.path_pattern for ep in api_endpoints))

	return HarSummary(
		har_path=str(har_path),
		total_entries=len(entries),
		api_entries=len(api_endpoints),
		static_entries=static_count,
		endpoints=api_endpoints,
		unique_path_patterns=unique_patterns,
	)


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage: python -m pathhar.parsing.har_parser <path_to_har>")
		sys.exit(1)

	logging.basicConfig(level=logging.INFO)
	summary = parse_har(sys.argv[1])
	print(json.dumps(summary.model_dump(), indent=2, default=str))
