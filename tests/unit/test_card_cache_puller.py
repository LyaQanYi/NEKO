from __future__ import annotations

from pathlib import Path
import json

import pytest

from main_logic.card_cache import puller


pytestmark = pytest.mark.unit


def test_get_client_id_persists_fresh_default_before_returning(tmp_path, monkeypatch) -> None:
    saved: list[dict] = []

    class FakeConfigManager:
        cloudsave_local_state_path = tmp_path / "state" / "cloudsave_local_state.json"

        def load_cloudsave_local_state(self) -> dict:
            return {"client_id": "fresh-client-id"}

        def build_default_cloudsave_local_state(self) -> dict:
            raise AssertionError("loaded default already contains a client_id")

        def save_cloudsave_local_state(self, state: dict) -> None:
            saved.append(dict(state))

    monkeypatch.setattr(puller, "get_config_manager", lambda: FakeConfigManager())

    assert puller._get_client_id() == "fresh-client-id"
    assert saved == [{"client_id": "fresh-client-id"}]


def test_get_client_id_fails_closed_when_fresh_default_cannot_be_saved(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeConfigManager:
        cloudsave_local_state_path = tmp_path / "state" / "cloudsave_local_state.json"

        def load_cloudsave_local_state(self) -> dict:
            return {"client_id": "volatile-client-id"}

        def build_default_cloudsave_local_state(self) -> dict:
            raise AssertionError("loaded default already contains a client_id")

        def save_cloudsave_local_state(self, _state: dict) -> None:
            raise OSError("disk unavailable")

    monkeypatch.setattr(puller, "get_config_manager", lambda: FakeConfigManager())

    assert puller._get_client_id() is None


def test_load_cached_cards_returns_safe_newest_records(tmp_path, monkeypatch) -> None:
    memory_dir = tmp_path / "memory"
    cards_dir = memory_dir / "Lanlan" / "cards"
    cards_dir.mkdir(parents=True)
    (cards_dir / "card-1.json").write_text(
        json.dumps({"id": "card-1", "title": "Cloud card"}),
        encoding="utf-8",
    )
    (cards_dir / "invalid.json").write_text("[]", encoding="utf-8")

    class FakeConfigManager:
        pass

    manager = FakeConfigManager()
    manager.memory_dir = memory_dir
    monkeypatch.setattr(puller, "get_config_manager", lambda: manager)

    assert puller.load_cached_cards() == [{"id": "card-1", "title": "Cloud card"}]
