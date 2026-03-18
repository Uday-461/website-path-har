"""LLM-based DOM assertion engine."""

import logging

from pathhar.config import Config
from pathhar.engine.llm_factory import create_llm
from pathhar.models.dom_snapshot import DOMSnapshot

logger = logging.getLogger(__name__)

ASSERTION_PROMPT = """\
Given this page state:
{html_summary}

Does the page satisfy: '{assertion}'?
Answer YES or NO on the first line, then quote the supporting evidence."""


async def check_assertion(
	dom_snapshot: DOMSnapshot,
	assertion: str,
	config: Config,
) -> tuple[bool, str | None]:
	"""Check an assertion against a DOM snapshot using the LLM.

	Returns (passed, evidence).
	"""
	llm = create_llm(config)

	prompt = ASSERTION_PROMPT.format(
		html_summary=dom_snapshot.html_summary or "(empty page)",
		assertion=assertion,
	)

	response = await llm.ainvoke(prompt)
	text = response.content if hasattr(response, "content") else str(response)
	text = text.strip()

	lines = text.split("\n", 1)
	first_line = lines[0].strip().upper()
	passed = first_line.startswith("YES")
	evidence = lines[1].strip() if len(lines) > 1 else None

	logger.info("Assertion '%s' → %s", assertion, "PASSED" if passed else "FAILED")
	return passed, evidence
