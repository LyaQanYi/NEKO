from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = PROJECT_ROOT / "scripts" / "card-forge" / "start_card_forge.py"


def _load_launcher():
    spec = importlib.util.spec_from_file_location("card_forge_launcher", LAUNCHER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_configured_port_matches_environment_and_desktop_precedence(tmp_path):
    launcher = _load_launcher()
    config_path = tmp_path / "port_config.json"
    config_path.write_text(
        json.dumps({"MAIN_SERVER_PORT": 43103, "CARD_FORGE_PORT": 43104}),
        encoding="utf-8",
    )

    assert launcher.resolve_configured_port(
        "MAIN_SERVER_PORT",
        48911,
        environment={
            "NEKO_MAIN_SERVER_PORT": "43101",
            "MAIN_SERVER_PORT": "43102",
        },
        config_path=config_path,
    ) == 43101
    assert launcher.resolve_configured_port(
        "CARD_FORGE_PORT",
        3001,
        environment={},
        config_path=config_path,
    ) == 43104
    assert launcher.resolve_configured_port(
        "CARD_FORGE_PORT",
        3001,
        environment={"NEKO_CARD_FORGE_PORT": "invalid"},
        config_path=tmp_path / "missing.json",
    ) == 3001


def test_main_passes_resolved_ports_to_every_child(monkeypatch):
    launcher = _load_launcher()
    launched = []

    monkeypatch.setattr(launcher, "_ensure_windows", lambda: None)
    monkeypatch.setattr(launcher, "ensure_path", lambda *_args: None)
    monkeypatch.setattr(launcher.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr("builtins.input", lambda: "")
    monkeypatch.setattr(
        launcher,
        "resolve_configured_port",
        lambda name, _default: {
            "MAIN_SERVER_PORT": 43101,
            "CARD_FORGE_PORT": 43102,
        }[name],
    )
    monkeypatch.setattr(
        launcher,
        "launch_window",
        lambda title, cwd, command, *, env=None: launched.append(
            (title, cwd, command, env)
        ),
    )

    assert launcher.main() == 0
    assert [item[0] for item in launched] == [
        "N.E.K.O Main Server - 43101",
        "Neko Card Forge Server - 43102",
        "Neko Card Forge Frontend - 5173",
    ]
    for _title, _cwd, _command, env in launched:
        assert env["NEKO_MAIN_SERVER_PORT"] == "43101"
        assert env["NEKO_CARD_FORGE_PORT"] == "43102"
