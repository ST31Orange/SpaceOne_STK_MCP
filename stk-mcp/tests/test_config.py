from __future__ import annotations

from spaceone_stk_mcp.config import Settings


def test_default_mode_is_headed_and_user_controllable():
    settings = Settings()
    assert settings.stk_visible is True
    assert settings.stk_user_control is True
    assert settings.quit_on_disconnect is False
    assert settings.close_scenario_on_disconnect is False
