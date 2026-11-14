"""PURPOSE: Verify an earned-state normal-input route across science and reality.
CALLED BY: pytest tests/test_mechanics_route.py.
HOW TO MODIFY: Keep all saves/settings and captures inside pytest temporary paths.
"""
from video_game.tools.mechanics_route import run_route


def test_earned_campaign_mechanics_and_child_continue(tmp_path):
    result = run_route(tmp_path / 'captures')
    actions = result['trace']
    assert len([x for x in actions if x['action'] == 'lab_validated']) == 7
    assert any(x['action'] == 'lab_incomplete_pause_exit_reset' for x in actions)
    assert any(x['action'] == 'relay_wrong_recover_and_cassette' for x in actions)
    assert any(x['action'] == 'flashback_interrupted_completed_reentered' for x in actions)
    assert any(x['action'] == 'tape_activation' for x in actions)
    wall = next(x for x in actions if x['action'] == 'wall_jump')
    assert wall['launch_vx'] < 0 and wall['launch_vy'] < 0 and wall['lock_timer'] > 0
    assert next(x for x in actions if x['action'] == 'child_continue_and_relay_restore')['state']['scene'] == 'BUNKER_HUB'
    assert actions[-1]['action'] == 'new_game_isolation'
    assert result['gate_g3'] == 'not verified'
