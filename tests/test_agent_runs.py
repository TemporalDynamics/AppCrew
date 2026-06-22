from pathlib import Path

from appcrew.core.agent_runs import AgentRuns


def test_create_run_indexes_current_subject(tmp_path: Path):
    runs = AgentRuns(state_dir=tmp_path)
    run = runs.create_run("subject_alpha", kind="mission")
    assert run["subject_id"] == "subject_alpha"
    assert run["status"] == "READY"
    assert runs.get_current_run("subject_alpha")["run_id"] == run["run_id"]


def test_update_run_changes_status(tmp_path: Path):
    runs = AgentRuns(state_dir=tmp_path)
    run = runs.create_run("subject_beta")
    updated = runs.update_run(run["run_id"], status="RUNNING", started_at="2026-01-01T00:00:00Z")
    assert updated["status"] == "RUNNING"
    assert updated["started_at"] == "2026-01-01T00:00:00Z"


def test_latest_run_wins_for_same_subject(tmp_path: Path):
    runs = AgentRuns(state_dir=tmp_path)
    first = runs.create_run("subject_gamma")
    second = runs.create_run("subject_gamma", kind="rerun")
    assert first["run_id"] != second["run_id"]
    assert runs.get_current_run("subject_gamma")["run_id"] == second["run_id"]

