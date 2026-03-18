"""CLI entry point for pathhar."""

import asyncio
import logging
import sys

import click

from pathhar.config import Config


@click.group()
def cli() -> None:
	"""Website Path & HAR Mapper — AI-powered site exploration."""
	pass


@cli.command()
@click.argument("url")
@click.option("--auth", default=None, help="Auth instruction for the LLM agent")
@click.option("--parallel", default=None, type=int, help="Max concurrent journeys (1-10)")
@click.option("--max-steps", default=None, type=int, help="Max discovery steps (5-200)")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--output-dir", default=None, help="Output directory path")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def scan(
	url: str,
	auth: str | None,
	parallel: int | None,
	max_steps: int | None,
	headless: bool,
	output_dir: str | None,
	verbose: bool,
) -> None:
	"""Scan a website: discover routes, execute journeys, capture HARs."""
	logging.basicConfig(
		level=logging.DEBUG if verbose else logging.INFO,
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
	)

	try:
		config = Config()  # type: ignore[call-arg]
	except Exception as e:
		click.echo(f"Configuration error: {e}", err=True)
		click.echo("Make sure OPENROUTER_API_KEY is set (in .env or environment)", err=True)
		sys.exit(1)

	if parallel is not None:
		config.max_concurrent_journeys = parallel
	if max_steps is not None:
		config.max_discovery_steps = max_steps
	config.headless = headless
	if output_dir is not None:
		from pathlib import Path

		config.output_dir = Path(output_dir)

	from pathhar.orchestrator.service import scan as run_scan

	click.echo(f"Scanning {url}...")
	click.echo(f"  LLM: {config.llm_model}")
	click.echo(f"  Parallel journeys: {config.max_concurrent_journeys}")
	click.echo(f"  Max discovery steps: {config.max_discovery_steps}")
	click.echo(f"  Headless: {config.headless}")
	click.echo(f"  Output: {config.output_dir}")
	click.echo()

	try:
		site_map = asyncio.run(run_scan(url, config, auth))
		click.echo()
		click.echo("Scan complete!")
		click.echo(f"  Routes discovered: {len(site_map.routes)}")
		click.echo(f"  Journeys executed: {len(site_map.journeys)}")
		click.echo(f"  API endpoints: {len(site_map.api_surface.endpoints)}")
		click.echo(f"  Duration: {site_map.scan_duration_seconds:.1f}s")
	except KeyboardInterrupt:
		click.echo("\nScan interrupted.", err=True)
		sys.exit(130)
	except Exception as e:
		click.echo(f"Scan failed: {e}", err=True)
		if verbose:
			import traceback

			traceback.print_exc()
		sys.exit(1)


@cli.command(name="parse-har")
@click.argument("har_path", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def parse_har(har_path: str, verbose: bool) -> None:
	"""Parse a HAR file and display API endpoint summary."""
	import json

	logging.basicConfig(
		level=logging.DEBUG if verbose else logging.INFO,
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
	)

	from pathhar.parsing.har_parser import parse_har as do_parse

	summary = do_parse(har_path)
	click.echo(json.dumps(summary.model_dump(), indent=2, default=str))


if __name__ == "__main__":
	cli()
