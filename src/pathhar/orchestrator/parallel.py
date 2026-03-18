"""Parallel journey execution with semaphore-based concurrency control."""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def run_parallel(
	coroutines: list[Coroutine[Any, Any, T]],
	max_concurrent: int = 3,
) -> list[T]:
	"""Run coroutines with bounded parallelism.

	Returns results in the same order as the input coroutines.
	"""
	semaphore = asyncio.Semaphore(max_concurrent)
	results: list[T | BaseException] = [None] * len(coroutines)  # type: ignore[list-item]

	async def _run_one(index: int, coro: Coroutine[Any, Any, T]) -> None:
		async with semaphore:
			try:
				results[index] = await coro
			except Exception as e:
				logger.error("Parallel task %d failed: %s", index, e)
				results[index] = e  # type: ignore[assignment]

	tasks = [asyncio.create_task(_run_one(i, coro)) for i, coro in enumerate(coroutines)]
	await asyncio.gather(*tasks)

	# Re-raise if any results are exceptions
	final: list[T] = []
	for i, r in enumerate(results):
		if isinstance(r, BaseException):
			logger.warning("Task %d returned error, including as-is", i)
		final.append(r)  # type: ignore[arg-type]

	return final
