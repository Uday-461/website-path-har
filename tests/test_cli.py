"""Tests for CLI JSON output, --human flag, error envelope, and exit codes."""

import json

from click.testing import CliRunner

from pathhar.cli import cli


class TestParseHarCommand:
	"""Test parse-har with JSON and human output modes."""

	def test_json_output_envelope(self, tmp_path, sample_har_data):
		"""Default mode emits JSON with status envelope."""
		har_file = tmp_path / "test.har"
		har_file.write_text(json.dumps(sample_har_data))

		runner = CliRunner()
		result = runner.invoke(cli, ["parse-har", str(har_file)])
		assert result.exit_code == 0

		data = json.loads(result.output)
		assert data["status"] == "ok"
		assert data["har_path"] == str(har_file)
		assert isinstance(data["api_entries"], int)
		assert data["api_entries"] == 3  # 3 API entries in sample (excludes CSS, PNG)
		assert isinstance(data["unique_path_patterns"], list)
		assert isinstance(data["endpoints"], list)

	def test_human_output(self, tmp_path, sample_har_data):
		"""--human flag emits indented JSON dump (legacy behavior)."""
		har_file = tmp_path / "test.har"
		har_file.write_text(json.dumps(sample_har_data))

		runner = CliRunner()
		result = runner.invoke(cli, ["--human", "parse-har", str(har_file)])
		assert result.exit_code == 0

		# Human mode outputs indented JSON (no status envelope)
		data = json.loads(result.output)
		assert "har_path" in data
		assert "status" not in data

	def test_missing_file_error(self):
		"""Non-existent file gives error."""
		runner = CliRunner()
		result = runner.invoke(cli, ["parse-har", "/nonexistent/file.har"])
		assert result.exit_code != 0

	def test_invalid_har_json(self, tmp_path):
		"""Malformed HAR file emits JSON error envelope."""
		har_file = tmp_path / "bad.har"
		har_file.write_text("not json")

		runner = CliRunner()
		result = runner.invoke(cli, ["parse-har", str(har_file)])
		assert result.exit_code == 1
		data = json.loads(result.output)
		assert data["status"] == "error"

	def test_invalid_har_human(self, tmp_path):
		"""Malformed HAR file with --human emits readable error."""
		har_file = tmp_path / "bad.har"
		har_file.write_text("not json")

		runner = CliRunner()
		result = runner.invoke(cli, ["--human", "parse-har", str(har_file)])
		assert result.exit_code == 1


class TestJourneyCommandValidation:
	"""Test journey input validation."""

	def test_empty_steps_json(self, monkeypatch):
		"""Empty steps string emits error envelope."""
		monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

		runner = CliRunner()
		result = runner.invoke(cli, ["journey", "http://example.com", "  |  | "])
		assert result.exit_code == 1
		data = json.loads(result.output)
		assert data["status"] == "error"
		assert "steps" in data["error"].lower()

	def test_empty_steps_human(self, monkeypatch):
		"""Empty steps with --human emits readable error."""
		monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

		runner = CliRunner()
		result = runner.invoke(cli, ["--human", "journey", "http://example.com", "  |  | "])
		assert result.exit_code == 1


class TestAssertCommandValidation:
	"""Test assert input validation."""

	def test_empty_journey_steps(self, monkeypatch):
		"""Empty journey steps emits error."""
		monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

		runner = CliRunner()
		result = runner.invoke(
			cli, ["assert", "http://example.com", "--journey", " | | ", "--expect", "page has title"]
		)
		assert result.exit_code == 1
		data = json.loads(result.output)
		assert data["status"] == "error"

	def test_missing_expect_flag(self):
		"""--expect is required for assert."""
		runner = CliRunner()
		result = runner.invoke(cli, ["assert", "http://example.com", "--journey", "click Login"])
		assert result.exit_code != 0

	def test_missing_journey_flag(self):
		"""--journey is required for assert."""
		runner = CliRunner()
		result = runner.invoke(cli, ["assert", "http://example.com", "--expect", "page has title"])
		assert result.exit_code != 0


class TestAssertExitCodes:
	"""Test assert command exit code contract."""

	def test_help_mentions_assertion(self):
		"""Assert help text mentions assertion."""
		runner = CliRunner()
		result = runner.invoke(cli, ["assert", "--help"])
		assert result.exit_code == 0
		assert "assertion" in result.output.lower()


class TestHumanFlagGroup:
	"""Test --human flag at group level."""

	def test_help_shows_human_flag(self):
		runner = CliRunner()
		result = runner.invoke(cli, ["--help"])
		assert result.exit_code == 0
		assert "--human" in result.output

	def test_subcommands_exist(self):
		runner = CliRunner()
		result = runner.invoke(cli, ["--help"])
		assert "scan" in result.output
		assert "journey" in result.output
		assert "assert" in result.output
		assert "parse-har" in result.output
