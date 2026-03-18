"""Tests for the LLM-based assertion engine."""

from unittest.mock import AsyncMock, patch

import pytest

from pathhar.config import Config
from pathhar.engine.asserter import check_assertion
from pathhar.models.dom_snapshot import DOMSnapshot


@pytest.fixture
def snapshot():
	return DOMSnapshot(
		url="http://localhost:3000",
		title="Home",
		timestamp=1000.0,
		html_summary="<h1>Welcome</h1><nav>Home | About | Contact</nav>",
		element_count=10,
	)


@pytest.fixture
def config(monkeypatch):
	monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
	return Config()  # type: ignore[call-arg]


class TestCheckAssertion:
	@pytest.mark.asyncio
	async def test_yes_response(self, snapshot, config):
		mock_response = AsyncMock()
		mock_response.content = "YES\nThe page contains a navigation bar with Home | About | Contact"

		with patch("pathhar.engine.asserter.create_llm") as mock_llm:
			mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
			passed, evidence = await check_assertion(snapshot, "page has a navigation bar", config)

		assert passed is True
		assert evidence is not None
		assert "navigation" in evidence.lower()

	@pytest.mark.asyncio
	async def test_no_response(self, snapshot, config):
		mock_response = AsyncMock()
		mock_response.content = "NO\nThe page does not contain any checkout-related content"

		with patch("pathhar.engine.asserter.create_llm") as mock_llm:
			mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
			passed, evidence = await check_assertion(snapshot, "page shows checkout complete", config)

		assert passed is False
		assert evidence is not None

	@pytest.mark.asyncio
	async def test_yes_no_evidence(self, snapshot, config):
		mock_response = AsyncMock()
		mock_response.content = "YES"

		with patch("pathhar.engine.asserter.create_llm") as mock_llm:
			mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
			passed, evidence = await check_assertion(snapshot, "page exists", config)

		assert passed is True
		assert evidence is None

	@pytest.mark.asyncio
	async def test_empty_snapshot(self, config):
		empty_snapshot = DOMSnapshot(
			url="http://localhost:3000",
			timestamp=1000.0,
		)

		mock_response = AsyncMock()
		mock_response.content = "NO\nThe page is empty"

		with patch("pathhar.engine.asserter.create_llm") as mock_llm:
			mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
			passed, evidence = await check_assertion(empty_snapshot, "page has content", config)

		assert passed is False
