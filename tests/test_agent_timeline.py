from pathlib import Path

from appcrew.core.agent_timeline import AgentTimeline


def test_append_and_list_for_run(tmp_path: Path):
    timeline = AgentTimeline(state_dir=tmp_path)
    event = timeline.append(
        run_id="run_1",
        subject_id="subject_1",
        event_type="run_started",
        title="Run started",
        message="Mission started",
    )
    events = timeline.list_for_run("run_1")
    assert len(events) == 1
    assert events[0]["event_id"] == event["event_id"]


def test_list_for_subject_filters_subject(tmp_path: Path):
    timeline = AgentTimeline(state_dir=tmp_path)
    timeline.append(run_id="run_1", subject_id="subject_1", event_type="a", title="A", message="A")
    timeline.append(run_id="run_2", subject_id="subject_2", event_type="b", title="B", message="B")
    events = timeline.list_for_subject("subject_1")
    assert len(events) == 1
    assert events[0]["subject_id"] == "subject_1"


def test_timeline_persists_and_reloads(tmp_path: Path):
    timeline = AgentTimeline(state_dir=tmp_path)
    timeline.append(run_id="run_9", subject_id="subject_9", event_type="done", title="Done", message="Finished")
    reloaded = AgentTimeline(state_dir=tmp_path)
    events = reloaded.list_for_run("run_9")
    assert len(events) == 1
    assert events[0]["title"] == "Done"

