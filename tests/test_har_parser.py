"""Tests for HAR parsing and endpoint extraction."""

import json

from pathhar.parsing.endpoint_extractor import group_endpoints
from pathhar.parsing.har_parser import (
	extract_path_pattern,
	is_static_request,
	parse_har,
)
from pathhar.parsing.schema_inferrer import infer_schema


class TestIsStaticRequest:
	def test_css_file(self):
		assert is_static_request("https://example.com/style.css", None)

	def test_js_file(self):
		assert is_static_request("https://example.com/app.js", None)

	def test_image_by_extension(self):
		assert is_static_request("https://example.com/logo.png", None)

	def test_image_by_content_type(self):
		assert is_static_request("https://example.com/image", "image/png")

	def test_api_endpoint(self):
		assert not is_static_request("https://example.com/api/data", "application/json")

	def test_html_page(self):
		assert not is_static_request("https://example.com/page", "text/html")


class TestExtractPathPattern:
	def test_numeric_id(self):
		assert extract_path_pattern("https://example.com/api/products/123") == "/api/products/{id}"

	def test_uuid(self):
		assert (
			extract_path_pattern("https://example.com/api/users/550e8400-e29b-41d4-a716-446655440000")
			== "/api/users/{uuid}"
		)

	def test_mongo_id(self):
		assert extract_path_pattern("https://example.com/api/items/507f1f77bcf86cd799439011") == "/api/items/{id}"

	def test_no_id(self):
		assert extract_path_pattern("https://example.com/api/products") == "/api/products"

	def test_root(self):
		assert extract_path_pattern("https://example.com/") == "/"


class TestParseHar:
	def test_parse_sample(self, sample_har_data, tmp_path):
		har_file = tmp_path / "test.har"
		har_file.write_text(json.dumps(sample_har_data))

		summary = parse_har(har_file)

		assert summary.total_entries == 5
		assert summary.api_entries == 3  # 2 static filtered out
		assert summary.static_entries == 2

	def test_endpoint_details(self, sample_har_data, tmp_path):
		har_file = tmp_path / "test.har"
		har_file.write_text(json.dumps(sample_har_data))

		summary = parse_har(har_file)

		get_product = next(ep for ep in summary.endpoints if ep.path_pattern == "/api/products/{id}")
		assert get_product.method == "GET"
		assert get_product.status == 200
		assert get_product.response_body is not None
		assert get_product.response_body["name"] == "Widget"

	def test_path_patterns(self, sample_har_data, tmp_path):
		har_file = tmp_path / "test.har"
		har_file.write_text(json.dumps(sample_har_data))

		summary = parse_har(har_file)

		assert "/api/products/{id}" in summary.unique_path_patterns
		assert "/api/cart" in summary.unique_path_patterns
		assert "/api/users/{uuid}" in summary.unique_path_patterns


class TestGroupEndpoints:
	def test_deduplication(self, sample_har_data, tmp_path):
		har_file = tmp_path / "test.har"
		har_file.write_text(json.dumps(sample_har_data))

		summary = parse_har(har_file)
		api_endpoints = group_endpoints(summary.endpoints)

		# Should have 3 unique method+pattern combos
		assert len(api_endpoints) == 3
		patterns = {(ep.method, ep.path_pattern) for ep in api_endpoints}
		assert ("GET", "/api/products/{id}") in patterns
		assert ("POST", "/api/cart") in patterns
		assert ("GET", "/api/users/{uuid}") in patterns


class TestInferSchema:
	def test_string(self):
		assert infer_schema("hello") == {"type": "string"}

	def test_integer(self):
		assert infer_schema(42) == {"type": "integer"}

	def test_float(self):
		assert infer_schema(3.14) == {"type": "number"}

	def test_boolean(self):
		assert infer_schema(True) == {"type": "boolean"}

	def test_null(self):
		assert infer_schema(None) == {"type": "null"}

	def test_list(self):
		schema = infer_schema([1, 2, 3])
		assert schema["type"] == "array"
		assert schema["items"]["type"] == "integer"

	def test_empty_list(self):
		schema = infer_schema([])
		assert schema["type"] == "array"

	def test_dict(self):
		schema = infer_schema({"name": "test", "count": 5})
		assert schema["type"] == "object"
		assert schema["properties"]["name"]["type"] == "string"
		assert schema["properties"]["count"]["type"] == "integer"
