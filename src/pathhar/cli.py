"""CLI entry point for pathhar."""

import asyncio
import json
import logging
import sys

import click

from pathhar.config import Config


def _emit_json(data: dict) -> None:
	"""Write compact JSON to stdout."""
	click.echo(json.dumps(data, default=str))


def _emit_error(msg: str) -> None:
	"""Write error envelope to stdout."""
	_emit_json({"status": "error", "error": msg})


def _build_config(
	headless: bool = True,
	output_dir: str | None = None,
	parallel: int | None = None,
	max_steps: int | None = None,
) -> Config:
	"""Build Config from env, applying CLI overrides."""
	config = Config()  # type: ignore[call-arg]
	config.headless = headless
	if output_dir is not None:
		from pathlib import Path

		config.output_dir = Path(output_dir)
	if parallel is not None:
		config.max_concurrent_journeys = parallel
	if max_steps is not None:
		config.max_discovery_steps = max_steps
	return config


@click.group()
@click.option("--human", is_flag=True, help="Human-readable output instead of JSON")
@click.pass_context
def cli(ctx: click.Context, human: bool) -> None:
	"""Website Path & HAR Mapper — AI-powered site exploration."""
	ctx.ensure_object(dict)
	ctx.obj["human"] = human


@cli.command()
@click.argument("url")
@click.option("--auth", default=None, help="Auth instruction for the LLM agent")
@click.option("--parallel", default=None, type=int, help="Max concurrent journeys (1-10)")
@click.option("--max-steps", default=None, type=int, help="Max discovery steps (5-200)")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--output-dir", default=None, help="Output directory path")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.pass_context
def scan(
	ctx: click.Context,
	url: str,
	auth: str | None,
	parallel: int | None,
	max_steps: int | None,
	headless: bool,
	output_dir: str | None,
	verbose: bool,
) -> None:
	"""Scan a website: discover routes, execute journeys, capture HARs."""
	human = ctx.obj["human"]

	logging.basicConfig(
		level=logging.DEBUG if verbose else logging.INFO,
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
		stream=sys.stderr,
	)

	try:
		config = _build_config(headless, output_dir, parallel, max_steps)
	except Exception as e:
		if human:
			click.echo(f"Configuration error: {e}", err=True)
			click.echo("Make sure OPENROUTER_API_KEY is set (in .env or environment)", err=True)
		else:
			_emit_error(str(e))
		sys.exit(1)

	from pathhar.orchestrator.service import scan as run_scan

	if human:
		click.echo(f"Scanning {url}...", err=True)
		click.echo(f"  LLM: {config.llm_model}", err=True)
		click.echo(f"  Parallel journeys: {config.max_concurrent_journeys}", err=True)
		click.echo(f"  Max discovery steps: {config.max_discovery_steps}", err=True)
		click.echo(f"  Headless: {config.headless}", err=True)
		click.echo(f"  Output: {config.output_dir}", err=True)

	try:
		site_map, run_dir = asyncio.run(run_scan(url, config, auth))
	except KeyboardInterrupt:
		click.echo("\nScan interrupted.", err=True)
		sys.exit(130)
	except Exception as e:
		if human:
			click.echo(f"\nScan failed: {e}", err=True)
			if verbose:
				import traceback

				traceback.print_exc(file=sys.stderr)
		else:
			_emit_error(str(e))
		sys.exit(1)

	if human:
		click.echo("\nScan complete!", err=True)
		click.echo(f"  Routes discovered: {len(site_map.routes)}", err=True)
		click.echo(f"  Journeys executed: {len(site_map.journeys)}", err=True)
		click.echo(f"  API endpoints: {len(site_map.api_surface.endpoints)}", err=True)
		click.echo(f"  Duration: {site_map.scan_duration_seconds:.1f}s", err=True)
		click.echo(f"  Output: {run_dir / 'sitemap.json'}", err=True)
	else:
		_emit_json(
			{
				"status": "ok",
				"run_dir": str(run_dir),
				"routes": len(site_map.routes),
				"journeys": len(site_map.journeys),
				"api_endpoints": len(site_map.api_surface.endpoints),
				"sitemap_path": str(run_dir / "sitemap.json"),
				"duration_seconds": round(site_map.scan_duration_seconds, 1),
			}
		)


@cli.command()
@click.argument("url")
@click.argument("steps")
@click.option("--auth", default=None, help="Auth instruction for the LLM agent")
@click.option("--max-steps", default=None, type=int, help="Max agent steps (5-200)")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--output-dir", default=None, help="Output directory path")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.pass_context
def journey(
	ctx: click.Context,
	url: str,
	steps: str,
	auth: str | None,
	max_steps: int | None,
	headless: bool,
	output_dir: str | None,
	verbose: bool,
) -> None:
	"""Run a targeted journey (no discovery phase).

	STEPS is a pipe-separated string, e.g. "click Login | fill email test@x.com | click Submit"
	"""
	human = ctx.obj["human"]

	logging.basicConfig(
		level=logging.DEBUG if verbose else logging.INFO,
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
		stream=sys.stderr,
	)

	try:
		config = _build_config(headless, output_dir, max_steps=max_steps)
	except Exception as e:
		if human:
			click.echo(f"Configuration error: {e}", err=True)
		else:
			_emit_error(str(e))
		sys.exit(1)

	step_list = [s.strip() for s in steps.split("|") if s.strip()]
	if not step_list:
		msg = "No steps provided. Use pipe-separated steps, e.g. 'click Login | fill email'"
		if human:
			click.echo(msg, err=True)
		else:
			_emit_error(msg)
		sys.exit(1)

	from pathhar.orchestrator.service import run_single_journey

	if human:
		click.echo(f"Running journey on {url}...", err=True)
		for i, s in enumerate(step_list, 1):
			click.echo(f"  Step {i}: {s}", err=True)

	try:
		site_map, run_dir = asyncio.run(run_single_journey(url, step_list, config, auth))
	except KeyboardInterrupt:
		click.echo("\nJourney interrupted.", err=True)
		sys.exit(130)
	except Exception as e:
		if human:
			click.echo(f"\nJourney failed: {e}", err=True)
			if verbose:
				import traceback

				traceback.print_exc(file=sys.stderr)
		else:
			_emit_error(str(e))
		sys.exit(1)

	result = site_map.journeys[0]

	if human:
		click.echo(f"\nJourney complete! (success={result.success})", err=True)
		click.echo(f"  Steps logged: {len(result.steps_log)}", err=True)
		click.echo(f"  API endpoints: {len(site_map.api_surface.endpoints)}", err=True)
		click.echo(f"  Duration: {site_map.scan_duration_seconds:.1f}s", err=True)
		click.echo(f"  Output: {run_dir / 'sitemap.json'}", err=True)
	else:
		_emit_json(
			{
				"status": "ok",
				"journey_id": result.journey_id,
				"success": result.success,
				"steps_log": result.steps_log,
				"api_endpoints": len(site_map.api_surface.endpoints),
				"har_path": str(result.har_path) if result.har_path else None,
				"sitemap_path": str(run_dir / "sitemap.json"),
				"duration_seconds": round(site_map.scan_duration_seconds, 1),
			}
		)


@cli.command(name="assert")
@click.argument("url")
@click.option("--journey", "steps", required=True, help="Pipe-separated journey steps")
@click.option("--expect", required=True, help="Assertion to check, e.g. \"page contains 'X'\"")
@click.option("--auth", default=None, help="Auth instruction for the LLM agent")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--output-dir", default=None, help="Output directory path")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.pass_context
def assert_cmd(
	ctx: click.Context,
	url: str,
	steps: str,
	expect: str,
	auth: str | None,
	headless: bool,
	output_dir: str | None,
	verbose: bool,
) -> None:
	"""Run a journey then assert a condition on the final page state.

	Exit code 0 = assertion passed, 2 = assertion failed, 1 = runtime error.
	"""
	human = ctx.obj["human"]

	logging.basicConfig(
		level=logging.DEBUG if verbose else logging.INFO,
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
		stream=sys.stderr,
	)

	try:
		config = _build_config(headless, output_dir)
	except Exception as e:
		if human:
			click.echo(f"Configuration error: {e}", err=True)
		else:
			_emit_error(str(e))
		sys.exit(1)

	step_list = [s.strip() for s in steps.split("|") if s.strip()]
	if not step_list:
		msg = "No journey steps provided."
		if human:
			click.echo(msg, err=True)
		else:
			_emit_error(msg)
		sys.exit(1)

	from pathhar.engine.asserter import check_assertion
	from pathhar.orchestrator.service import run_single_journey

	if human:
		click.echo(f"Running assertion on {url}...", err=True)
		click.echo(f"  Expect: {expect}", err=True)

	try:
		site_map, run_dir = asyncio.run(run_single_journey(url, step_list, config, auth))
	except KeyboardInterrupt:
		click.echo("\nInterrupted.", err=True)
		sys.exit(130)
	except Exception as e:
		if human:
			click.echo(f"\nJourney failed: {e}", err=True)
			if verbose:
				import traceback

				traceback.print_exc(file=sys.stderr)
		else:
			_emit_error(str(e))
		sys.exit(1)

	result = site_map.journeys[0]

	# Get last DOM snapshot for assertion
	if not result.dom_snapshots:
		msg = "No DOM snapshots captured — cannot evaluate assertion"
		if human:
			click.echo(msg, err=True)
		else:
			_emit_error(msg)
		sys.exit(1)

	last_snapshot = result.dom_snapshots[-1]

	try:
		passed, evidence = asyncio.run(check_assertion(last_snapshot, expect, config))
	except Exception as e:
		if human:
			click.echo(f"Assertion check failed: {e}", err=True)
		else:
			_emit_error(f"Assertion check failed: {e}")
		sys.exit(1)

	if human:
		status_text = "PASSED" if passed else "FAILED"
		click.echo(f"\nAssertion {status_text}: {expect}", err=True)
		if evidence:
			click.echo(f"  Evidence: {evidence}", err=True)
		click.echo(f"  Duration: {site_map.scan_duration_seconds:.1f}s", err=True)
	else:
		_emit_json(
			{
				"status": "ok",
				"passed": passed,
				"assertion": expect,
				"evidence": evidence,
				"journey_id": result.journey_id,
				"duration_seconds": round(site_map.scan_duration_seconds, 1),
			}
		)

	if not passed:
		sys.exit(2)


@cli.command(name="parse-har")
@click.argument("har_path", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.pass_context
def parse_har(ctx: click.Context, har_path: str, verbose: bool) -> None:
	"""Parse a HAR file and display API endpoint summary."""
	human = ctx.obj["human"]

	logging.basicConfig(
		level=logging.DEBUG if verbose else logging.INFO,
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
		stream=sys.stderr,
	)

	from pathhar.parsing.har_parser import parse_har as do_parse

	try:
		summary = do_parse(har_path)
	except Exception as e:
		if human:
			click.echo(f"Failed to parse HAR: {e}", err=True)
		else:
			_emit_error(str(e))
		sys.exit(1)

	if human:
		click.echo(json.dumps(summary.model_dump(), indent=2, default=str))
	else:
		data = summary.model_dump(mode="json")
		_emit_json(
			{
				"status": "ok",
				"har_path": har_path,
				"api_entries": summary.api_entries,
				"unique_path_patterns": summary.unique_path_patterns,
				"endpoints": data["endpoints"],
			}
		)


if __name__ == "__main__":
	cli()
