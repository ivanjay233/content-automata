"""Tests for CLI commands and config validation."""

import pytest
from click.testing import CliRunner

from content_automata.cli import cli


class TestCLIBasic:
    """Test basic CLI commands."""

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "content-automata" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_init(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert "Ready!" in result.output or "Initialization" in result.output

    def test_status(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Pipeline Status" in result.output or "Package" in result.output


class TestCLIRun:
    """Test 'cauto run' command."""

    def test_run_without_topic_exits(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run"])
        assert result.exit_code != 0

    def test_run_with_topic(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--topic", "Test Topic"])
        assert result.exit_code == 0
        assert "Pipeline Complete" in result.output or "Complete" in result.output

    def test_run_with_url(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--url", "https://example.com/article"])
        assert result.exit_code == 0

    def test_run_with_json_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--topic", "JSON Test", "--json"])
        assert result.exit_code == 0
        assert '"topic"' in result.output or '"state"' in result.output

    def test_run_with_dry_run(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--topic", "Dry Run Test", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry Run" in result.output or "Actions" in result.output or "estimated_cost" in result.output.lower()


class TestCLIListShow:
    """Test 'cauto list' and 'cauto show' commands."""

    def test_list_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0

    def test_list_with_json(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--json"])
        assert result.exit_code == 0

    def test_show_latest(self):
        runner = CliRunner()
        # First run something
        runner.invoke(cli, ["run", "--topic", "Show Test"])
        result = runner.invoke(cli, ["show", "--latest"])
        assert result.exit_code == 0


class TestCLITemplate:
    """Test 'cauto template' command."""

    def test_template_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "list"])
        assert result.exit_code == 0
        assert "Blog Post" in result.output or "Templates" in result.output

    def test_template_show_blog(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "show", "blog"])
        assert result.exit_code == 0
        assert "Blog Post" in result.output

    def test_template_show_nonexistent(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "show", "nonexistent"])
        assert "'nonexistent' not found" in result.output or "not found" in result.output


class TestCLIValidate:
    """Test 'cauto validate' command."""

    def test_validate_no_config(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0

    def test_validate_with_config(self):
        import tempfile
        import yaml
        runner = CliRunner()
        with runner.isolated_filesystem():
            cfg = {"research": {"provider": "tavily"}, "image_generation": {"provider": "openai"}}
            with open("test_config.yaml", "w") as f:
                yaml.dump(cfg, f)
            result = runner.invoke(cli, ["validate", "--config", "test_config.yaml"])
            assert result.exit_code == 0
            assert "valid" in result.output.lower()


class TestCLIHistory:
    """Test 'cauto history' command."""

    def test_history(self):
        runner = CliRunner()
        # Run something first
        runner.invoke(cli, ["run", "--topic", "History Test"])
        result = runner.invoke(cli, ["history"])
        assert result.exit_code == 0

    def test_history_with_json(self):
        runner = CliRunner()
        runner.invoke(cli, ["run", "--topic", "History JSON"])
        result = runner.invoke(cli, ["history", "--json"])
        assert result.exit_code == 0
