"""MODULE: tests/test_greenkeeper_projectiles.py
PURPOSE: Verify real projectiles reach the exposed core without bypassing blockers.
CALLED BY: pytest during focused and full game checks.
HOW TO MODIFY: Preserve real projectile-manager ordering, collision and volley coverage.
"""
import pygame
import pytest
import math
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.bosses.base import STATE_VULNERABLE
from video_game.engine.weapons import CombatTarget, ProjectileManager
from video_game.engine.world import COLLISION_SOLID, COLLISION_EMPTY

class Room:
    tile_size=16
    width_px=1000
    height_px=500
    def __init__(self, solids=()): self.solids=set(solids)
    def get_tile(self, x, y): return COLLISION_SOLID if (x,y) in self.solids else COLLISION_EMPTY

def boss_open():
    b=Greenkeeper(); b.skip_intro(); b.phase_state=STATE_VULNERABLE; b.weak_point_exposed=True
    return b

def fire(manager,x,y,direction=1, *, pierce=1, lifetime=2, shared=None):
    return manager.spawn(x,y,direction,0,1000,10,is_charged=pierce>1,pierce_count=pierce,lifetime=lifetime,volley_hit_target_ids=shared)

@pytest.mark.parametrize('start,direction',[(400,1),(580,-1)])
@pytest.mark.parametrize('dt,steps',[(0.01,30),(0.3,1)])
def test_core_hits_at_actual_window_from_both_sides(start,direction,dt,steps):
    b=boss_open(); p=ProjectileManager(); bolt=fire(p,start,b.weak_point_rect.centery,direction)
    hits=[]
    for _ in range(steps):
        hits.extend(p.update(dt,Room(),targets=[b]))
        if hits: break
    assert len(hits)==1 and hits[0].damage_dealt==20
    assert b.weak_point_rect.collidepoint(hits[0].hit_x,hits[0].hit_y)
    assert not bolt.active


def test_no_early_hit_and_lifetime_does_not_create_instant_core_damage():
    b=boss_open(); p=ProjectileManager(); bolt=fire(p,400,b.weak_point_rect.centery,lifetime=.05)
    assert p.update(.05,Room(),targets=[b]) == []
    assert b.health==300 and not bolt.active


def test_diagonal_aim_reaches_window_with_small_steps():
    b=boss_open(); p=ProjectileManager()
    x,y=390.0,130.0
    dx,dy=b.weak_point_rect.centerx-x,b.weak_point_rect.centery-y
    distance=math.hypot(dx,dy)
    p.spawn(x,y,dx/distance,dy/distance,1000,10,lifetime=2)
    hits=[]
    for _ in range(30):
        hits.extend(p.update(.01,Room(),targets=[b]))
        if hits: break
    assert len(hits)==1 and hits[0].damage_dealt==20
    assert b.weak_point_rect.collidepoint(hits[0].hit_x,hits[0].hit_y)


def test_closed_and_off_target_resolve_at_body():
    b=boss_open(); b.weak_point_exposed=False
    p=ProjectileManager(); fire(p,400,b.weak_point_rect.centery)
    hits=p.update(.2,Room(),targets=[b])
    assert hits[0].damage_dealt==10 and hits[0].hit_x==b.rect.left
    b=boss_open(); p=ProjectileManager(); fire(p,400,b.y+80)
    hits=p.update(.2,Room(),targets=[b])
    assert hits[0].damage_dealt==10 and hits[0].hit_x==b.rect.left

@pytest.mark.parametrize('col',[25,29])
def test_wall_before_body_or_between_body_and_core_wins(col):
    b=boss_open(); p=ProjectileManager(); fire(p,380,b.weak_point_rect.centery)
    hits=p.update(.3,Room({(col,12)}),targets=[b])
    assert hits==[] and b.health==300 and not p.projectiles


def test_front_target_blocks_core_and_behind_target_for_nonpiercing():
    b=boss_open(); front=CombatTarget('front',pygame.Rect(460,195,8,14),health=100)
    behind=CombatTarget('behind',pygame.Rect(570,195,8,14),health=100)
    p=ProjectileManager(); fire(p,400,b.weak_point_rect.centery)
    hits=p.update(.3,Room(),targets=[behind,b,front])
    assert [h.target_id for h in hits]==['front']
    assert b.health==300 and behind.health==100


def test_charged_pierce_preserves_order_and_hits_each_once():
    b=boss_open(); front=CombatTarget('front',pygame.Rect(460,195,8,14),health=100)
    behind=CombatTarget('behind',pygame.Rect(570,195,8,14),health=100)
    p=ProjectileManager(); fire(p,400,b.weak_point_rect.centery,pierce=3)
    hits=p.update(.3,Room(),targets=[behind,b,front])
    assert [h.target_id for h in hits]==['front',b.target_id,'behind']
    assert [h.damage_dealt for h in hits]==[10,20,10]
    assert b.hit_count==1 and front.hit_count==1 and behind.hit_count==1


def test_shared_fan_damages_core_only_once():
    b=boss_open(); p=ProjectileManager(); shared=set()
    fire(p,400,b.weak_point_rect.centery,shared=shared)
    fire(p,400,b.weak_point_rect.centery,shared=shared)
    hits=p.update(.2,Room(),targets=[b])
    assert len(hits)==1 and hits[0].damage_dealt==20 and b.health==280
    assert b.target_id in shared and not p.projectiles
