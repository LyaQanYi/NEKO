import re
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_card_forge_polling_and_interactions_are_lifecycle_safe_and_keyboard_accessible():
    source = _read("card-forge/src/App.jsx")

    assert source.count("let requestVersion = 0") == 2
    assert "if (!cancelled && version === requestVersion) setCloudInventory(cards)" in source
    assert source.count("cancelled || version !== requestVersion") >= 2
    assert "forgedCard.storyGenerationStatus === 'temporary-fallback'" in source
    assert "throw new Error('forge_story_temporary_fallback')" in source
    assert "故事生成暂时不可用，请再次点击所选卡片重试。" in source
    assert "'铸造未完成，请再次点击所选卡片重试。'" in source
    assert "hasForgedRef.current = false" in source
    assert source.count('role="button"') >= 2
    assert source.count("event.key === 'Enter' || event.key === ' '") >= 2
    assert "aria-pressed={isPicked}" in source


def test_mobile_avatar_layout_keeps_screen_share_control_for_every_renderer():
    methods_source = _read("static/avatar/avatar-ui-buttons/methods-buttons.js")
    assert "id: 'screen'" in methods_source
    assert "titleKey: 'buttons.screenShare'" in methods_source
    assert "mobileOnly: true" in methods_source

    renderer_sources = [
        _read("static/live2d/live2d-ui-buttons.js"),
        _read("static/vrm/vrm-ui-buttons.js"),
        _read("static/mmd/mmd-ui-buttons.js"),
        _read("static/pngtuber-core.js"),
    ]
    for source in renderer_sources:
        assert "config.mobileOnly" in source
        assert "config.id === 'screen'" in source


def test_stop_script_resolves_runtime_ports_before_terminating_processes():
    source = _read("stop-card-forge.ps1")

    assert "$env:NEKO_MAIN_SERVER_PORT" in source
    assert "$env:MAIN_SERVER_PORT" in source
    assert '"N.E.K.O\\port_config.json"' in source
    assert "$env:NEKO_CARD_FORGE_PORT" in source
    assert "$ports = @($mainServerPort, $cardForgePort, 5173)" in source
    authorization_pattern = (
        r"(?i)(Authorization\s*[:=]\s*(?:[A-Za-z][A-Za-z0-9_-]*\s+)?)\S+"
    )
    assert authorization_pattern in source

    command_line = "tool.exe --header Authorization: Basic dXNlcjpwYXNz --safe"
    redacted = re.sub(authorization_pattern, r"\1<redacted>", command_line)
    assert "dXNlcjpwYXNz" not in redacted
    assert "Authorization: Basic <redacted>" in redacted


def test_live2d_click_actions_are_not_dispatched_by_the_generic_listener_twice():
    source = _read("static/live2d/live2d-ui-buttons.js")

    assert "window.dispatchEvent(new CustomEvent('live2d-social-click'))" in source
    assert "window.dispatchEvent(new CustomEvent('live2d-goodbye-click'))" in source
    assert "} else if (config.id !== 'social' && config.id !== 'goodbye') {" in source
