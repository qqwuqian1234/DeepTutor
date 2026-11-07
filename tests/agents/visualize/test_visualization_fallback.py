"""Visualization failures fall back to a text explanation."""

from __future__ import annotations

import asyncio

import pytest

from deeptutor.agents.visualize.capability import VisualizeCapability
from deeptutor.core.context import UnifiedContext
from deeptutor.core.stream import StreamEvent, StreamEventType
from deeptutor.runtime.stream_bus import StreamBus


async def _collect(run) -> list:
    bus = StreamBus()
    events = []

    async def _consume() -> None:
        async for event in bus.subscribe():
            events.append(event)

    consumer = asyncio.create_task(_consume())
    await asyncio.sleep(0)
    await run(bus)
    await asyncio.sleep(0)
    await bus.close()
    await consumer
    return events


@pytest.mark.asyncio
async def test_missing_manim_does_not_fail_the_teaching_turn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, str] = {}

    async def fallback(context, stream, *, source, reason):
        called["reason"] = reason
        await stream.content("用静态图和文字说明切线。", source=source, stage="responding")

    monkeypatch.setattr(
        "deeptutor.agents.visualize.capability.stream_teaching_fallback",
        fallback,
    )
    context = UnifiedContext(
        session_id="session_1",
        user_message="画出切线不等式",
        active_capability="visualize",
        language="zh",
        config_overrides={"render_mode": "manim_video"},
    )
    events = await _collect(lambda bus: VisualizeCapability().run(context, bus))
    assert called["reason"]
    content = "".join(
        event.content for event in events if event.type == StreamEventType.CONTENT
    )
    assert "切线" in content
    assert not any(
        event.type == StreamEventType.ERROR and (event.metadata or {}).get("turn_terminal")
        for event in events
    )
