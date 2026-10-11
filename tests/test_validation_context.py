"""Regression checks for local versus remote evidence provenance."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "validate_portfolio", Path(__file__).resolve().parents[1] / "scripts" / "validate_portfolio.py"
)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def test_local_execution_does_not_claim_workflow_success(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    context = validator.execution_context()
    assert context["location"] == "local"
    assert "run_url" not in context
    assert context["workflow_conclusion"] == "NOT_APPLICABLE"


def test_remote_execution_identifies_current_run_without_claiming_success(monkeypatch):
    for name, value in {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": "example/portfolio",
        "GITHUB_RUN_ID": "123",
        "GITHUB_SHA": "abc123",
        "GITHUB_RUN_ATTEMPT": "2",
    }.items():
        monkeypatch.setenv(name, value)
    context = validator.execution_context()
    assert context["location"] == "github_actions"
    assert context["run_url"] == "https://github.com/example/portfolio/actions/runs/123"
    assert context["head_sha"] == "abc123"
    assert context["run_attempt"] == "2"
    assert context["workflow_conclusion"] == "NOT_CHECKED_BY_THIS_SCRIPT"
