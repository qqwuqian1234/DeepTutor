"""Text teaching when animation or visualization cannot be delivered.

A missing optional renderer used to raise and end the turn with no
explanation. This path keeps the same model and streams a normal answer
instead, so speech playback and the stored reply still have something to say.
"""

from __future__ import annotations

import logging

from deeptutor.core.context import UnifiedContext
from deeptutor.runtime.stream_bus import StreamBus

logger = logging.getLogger(__name__)

_STARTED = "_teaching_fallback_started"


def _zh(language: str) -> bool:
    return str(language or "").lower().startswith("zh")


def teaching_fallback_prompt(reason: str, *, language: str) -> str:
    detail = " ".join(str(reason or "").split())[:400]
    if _zh(language):
        return (
            "这一轮没能生成动画或交互可视化"
            + (f"（{detail}）" if detail else "")
            + "。请改用文字把学生的问题讲清楚。\n"
            "需要图时，可以给一个完整的 mermaid 代码块作为静态示意图。\n"
            "不要声称已经生成了视频或动画，也不要只回复安装命令。讲解本身必须完整。"
        )
    return (
        "Animation or interactive visualization could not be produced for this turn"
        + (f" ({detail})" if detail else "")
        + ". Teach the student's question in clear text anyway.\n"
        "You may include one complete fenced mermaid diagram when a static figure helps.\n"
        "Do not claim that a video or animation was rendered, and do not stop at an "
        "install instruction. The explanation itself is required."
    )


def _clear_visualize_mode(context: UnifiedContext) -> None:
    from deeptutor.visualizers.protocol import (
        REQUESTED_VISUALIZER_KEY,
        VISUALIZATION_RESULT_KEY,
        VISUALIZE_MODE_KEY,
    )

    for key in (VISUALIZE_MODE_KEY, VISUALIZATION_RESULT_KEY, REQUESTED_VISUALIZER_KEY):
        context.metadata.pop(key, None)


async def stream_teaching_fallback(
    context: UnifiedContext,
    stream: StreamBus,
    *,
    source: str,
    reason: str,
) -> None:
    """Stream a text explanation after a visual capability cannot finish.

    The notice is published as answer text first, so a reader (and progressive
    speech playback) is not left waiting on a second model call.
    """
    if context.metadata.get(_STARTED):
        raise RuntimeError(reason or "Teaching fallback was already used for this turn.")
    context.metadata[_STARTED] = True
    _clear_visualize_mode(context)
    language = context.language
    zh = _zh(language)
    notice = (
        "动画或可视化没有生成成功，下面改为文字讲解。"
        if zh
        else "Animation or visualization did not generate, so this is a text explanation."
    )
    logger.warning("Teaching fallback for %s: %s", source, reason)
    await stream.progress(
        notice,
        source=source,
        stage="responding",
        metadata={"teaching_fallback": True},
    )
    await stream.content(notice + "\n\n", source=source, stage="responding")
    context.metadata["teaching_fallback_prompt"] = teaching_fallback_prompt(
        reason, language=language
    )
    from deeptutor.agents.chat.agentic_pipeline import AgenticChatPipeline

    pipeline = AgenticChatPipeline(
        language=language,
        event_source=source,
        event_stage="responding",
    )
    await pipeline.run(context, stream)


__all__ = ["stream_teaching_fallback", "teaching_fallback_prompt"]
