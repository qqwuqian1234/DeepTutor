"""Teaching-turn reliability: truncation, cancel retry, and answer-first."""

from __future__ import annotations

import pytest

from deeptutor.agents.visualize.utils import build_fallback_html, validate_visualization
from deeptutor.core.stream import StreamEvent, StreamEventType
from deeptutor.services.session.sqlite_store import SQLiteSessionStore
from deeptutor.services.session.turn_runtime import (
    TurnRuntimeManager,
    _format_answer_first_prompt,
    _normalize_answer_first,
    _request_snapshot_metadata,
    persisted_answer_problem,
)


_COMPLETE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body><p>Acid</p><script>void 0;</script></body></html>
"""


def test_html_validation_rejects_a_document_cut_off_mid_tag() -> None:
    truncated = "<!DOCTYPE html><html><body><p>H2SO5"
    ok, error = validate_visualization(truncated, "html")
    assert ok is False
    assert "cut off" in error


def test_html_validation_accepts_a_closed_document() -> None:
    ok, error = validate_visualization(_COMPLETE_HTML, "html")
    assert ok is True, error
    fallback_ok, fallback_error = validate_visualization(
        build_fallback_html(title="Acid", summary="A static note."),
        "html",
    )
    assert fallback_ok is True, fallback_error


def test_truncated_html_answer_is_not_a_successful_completion() -> None:
    content = "```html\n<!DOCTYPE html>\n<html><body><p>sulfur\n```"
    problem = persisted_answer_problem(content, [], language="zh")
    assert "截断" in problem or "代码块" in problem


def test_mid_sentence_token_limit_is_not_a_successful_completion() -> None:
    events = [
        {
            "type": "progress",
            "metadata": {"call_kind": "llm_final_response", "finish_reason": "length"},
        }
    ]
    problem = persisted_answer_problem(
        "硫酸的酸性来自",
        events,
        language="zh",
    )
    assert problem
    assert persisted_answer_problem("硫酸是强酸。", events, language="zh") == ""


def test_empty_completed_answer_is_rejected_and_a_file_answer_is_kept() -> None:
    assert persisted_answer_problem("", [], language="en")
    assert persisted_answer_problem("", [], attachments=[{"url": "/files/a.png"}]) == ""


def test_terminal_error_still_wins_over_a_done_completed_status() -> None:
    from deeptutor.services.session.turn_runtime import _resolve_turn_outcome

    status, error = _resolve_turn_outcome(
        [
            {
                "type": "error",
                "content": "The visualization HTML was cut off before the document finished.",
                "metadata": {
                    "turn_terminal": True,
                    "status": "failed",
                    "error_code": "incomplete_output",
                    "retryable": True,
                },
            }
        ],
        StreamEvent(type=StreamEventType.DONE, source="visualize", metadata={"status": "completed"}),
    )
    assert status == "failed"
    assert "cut off" in error


def test_answer_first_attempt_is_normalized_and_snapshotted() -> None:
    assert _normalize_answer_first({"attempt": "  "}) is None
    normalized = _normalize_answer_first({"attempt": "它会分解"})
    assert normalized == {"attempt": "它会分解"}
    assert "对照" in _format_answer_first_prompt("它会分解", language="zh")
    metadata = _request_snapshot_metadata(
        payload={"answer_first": normalized, "language": "zh"},
        content="H2SO5是强酸吗",
        capability="chat",
        config={},
        attachments=[],
        notebook_references=[],
        history_references=[],
        partner_group_references=[],
        question_notebook_references=[],
        book_references=[],
        persona="",
        memory_references=[],
        llm_selection=None,
    )
    assert metadata["request_snapshot"]["answerFirstAttempt"] == "它会分解"


@pytest.mark.asyncio
async def test_answer_first_attempt_is_logged_without_a_wrong_grade(tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "answers.db")
    session = await store.ensure_session(None)
    runtime = TurnRuntimeManager(store)
    await runtime._record_answer_first_attempt(
        session_id=session["id"],
        turn_id="turn-1",
        question="H2SO5是强酸吗",
        attempt="我认为它是强酸，因为含有氢。",
    )
    attempts = await store.list_assessment_attempts(session["id"])
    assert len(attempts) == 1
    assert attempts[0]["result"] == "ungraded"
    assert attempts[0]["question_type"] == "answer_first"
    assert attempts[0]["user_answer"].startswith("我认为")


@pytest.mark.asyncio
async def test_start_turn_keeps_answer_first_out_of_capability_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    store = SQLiteSessionStore(tmp_path / "turns.db")
    runtime = TurnRuntimeManager(store)
    seen: dict = {}

    async def capture(execution) -> None:
        seen["answer_first"] = execution.payload.get("answer_first")
        seen["config"] = execution.payload.get("config")
        await store.transition_turn(execution.turn_id, "completed")

    monkeypatch.setattr(runtime, "_run_turn", capture)
    _session, turn = await runtime.start_turn(
        {
            "content": "H2SO5是强酸吗",
            "language": "zh",
            "config": {"answer_first": {"attempt": "会分解成硫酸"}},
        }
    )
    await runtime._executions[turn["id"]].task
    assert seen["answer_first"] == {"attempt": "会分解成硫酸"}
    assert "answer_first" not in seen["config"]
