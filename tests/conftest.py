"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_har_data() -> dict:
	"""Minimal HAR data for testing the parser."""
	return {
		"log": {
			"version": "1.2",
			"entries": [
				{
					"request": {
						"method": "GET",
						"url": "https://example.com/api/products/123",
						"headers": [],
						"bodySize": 0,
					},
					"response": {
						"status": 200,
						"content": {
							"size": 256,
							"mimeType": "application/json",
							"text": '{"id": 123, "name": "Widget", "price": 9.99}',
						},
					},
					"time": 45.2,
					"timings": {"wait": 30, "receive": 15},
				},
				{
					"request": {
						"method": "POST",
						"url": "https://example.com/api/cart",
						"headers": [],
						"postData": {
							"mimeType": "application/json",
							"text": '{"product_id": 123, "quantity": 1}',
						},
						"bodySize": 34,
					},
					"response": {
						"status": 201,
						"content": {
							"size": 128,
							"mimeType": "application/json",
							"text": '{"cart_id": "abc", "items": [{"product_id": 123}]}',
						},
					},
					"time": 120.5,
					"timings": {"wait": 100, "receive": 20},
				},
				{
					"request": {
						"method": "GET",
						"url": "https://example.com/static/style.css",
						"headers": [],
						"bodySize": 0,
					},
					"response": {
						"status": 200,
						"content": {"size": 5000, "mimeType": "text/css"},
					},
					"time": 10.0,
					"timings": {"wait": 5, "receive": 5},
				},
				{
					"request": {
						"method": "GET",
						"url": "https://example.com/images/logo.png",
						"headers": [],
						"bodySize": 0,
					},
					"response": {
						"status": 200,
						"content": {"size": 20000, "mimeType": "image/png"},
					},
					"time": 50.0,
					"timings": {"wait": 10, "receive": 40},
				},
				{
					"request": {
						"method": "GET",
						"url": "https://example.com/api/users/550e8400-e29b-41d4-a716-446655440000",
						"headers": [],
						"bodySize": 0,
					},
					"response": {
						"status": 200,
						"content": {
							"size": 64,
							"mimeType": "application/json",
							"text": '{"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Test User"}',
						},
					},
					"time": 33.0,
					"timings": {"wait": 25, "receive": 8},
				},
			],
		}
	}
