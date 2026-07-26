from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.memory_server.routes as routes
from utils.language_utils import get_global_language_full


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_process_requests_keep_language_task_local_across_awaits(monkeypatch):
    both_requests_entered = asyncio.Event()
    entered_count = 0
    observed: dict[str, str] = {}

    async def aload_characters():
        nonlocal entered_count
        entered_count += 1
        if entered_count == 2:
            both_requests_entered.set()
        await both_requests_entered.wait()
        return {"猫娘": {"EnglishNeko": {}, "JapaneseNeko": {}}}

    async def update_history(_history, lanlan_name, **_kwargs):
        observed[lanlan_name] = get_global_language_full()

    monkeypatch.setattr(
        routes.runtime,
        "_config_manager",
        SimpleNamespace(aload_characters=aload_characters),
    )
    monkeypatch.setattr(
        routes.runtime,
        "recent_history_manager",
        SimpleNamespace(update_history=update_history),
    )
    monkeypatch.setattr(
        routes.runtime,
        "time_manager",
        SimpleNamespace(astore_conversation=AsyncMock()),
    )
    monkeypatch.setattr(routes.runtime, "embedding_warmup_worker", None)
    monkeypatch.setattr(routes.gates, "_touch_activity", lambda: None)
    monkeypatch.setattr(
        routes.post_turn,
        "_spawn_outbox_post_turn_signals",
        AsyncMock(),
    )
    monkeypatch.setattr(routes.review, "maybe_spawn_review", AsyncMock())

    english_result, japanese_result = await asyncio.gather(
        routes.process_conversation(
            routes.HistoryRequest(input_history="[]", language="en"),
            "EnglishNeko",
        ),
        routes.process_conversation(
            routes.HistoryRequest(input_history="[]", language="ja"),
            "JapaneseNeko",
        ),
    )

    assert english_result == {"status": "processed"}
    assert japanese_result == {"status": "processed"}
    assert observed == {
        "EnglishNeko": "en",
        "JapaneseNeko": "ja",
    }


def test_all_memory_write_routes_install_request_language_context():
    source = routes.__file__
    assert source is not None
    route_source = Path(source).read_text(encoding="utf-8")
    assert route_source.count("with language_context(memory_language):") == 4
