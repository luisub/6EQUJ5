"""
PURPOSE: Analog ability framework: unlock ID verification, cooldown and cost management,
         actor-time dilation, decoy targeting diversion, phase shielding, and checkpoint persistence.
CALLED BY: video_game.engine.player, video_game.engine.scenes.field, video_game.tests.test_combat.
HOW TO MODIFY: Add new analog abilities by subclassing Ability; tune costs and durations in
               video_game/data/balance.json; maintain zero wildcard imports.
"""

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import pygame

BALANCE_PATH = Path(__file__).resolve().parent.parent / "data" / "balance.json"


@dataclass
class AbilityConfig:
    """Configuration parameters for analog abilities loaded from balance.json."""
    id: str
    name: str
    cost: int = 30
    cooldown: float = 6.0
    duration: float = 4.0
    actor_time_modifier: float = 1.0
    decoy_health: int = 50
    shield_hp: int = 45
    unlock_events: List[str] = field(default_factory=list)

    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> "AbilityConfig":
        """Instantiate config from dictionary."""
        return cls(
            id=str(data.get("id", "ability")),
            name=str(data.get("name", "Analog Ability")),
            cost=int(data.get("cost", 30)),
            cooldown=float(data.get("cooldown", 6.0)),
            duration=float(data.get("duration", 4.0)),
            actor_time_modifier=float(data.get("actor_time_modifier", 1.0)),
            decoy_health=int(data.get("decoy_health", 50)),
            shield_hp=int(data.get("shield_hp", 45)),
            unlock_events=list(data.get("unlock_events", [])),
        )

    @classmethod
    def load_from_file(
        cls,
        path: Optional[Union[str, Path]] = None,
        ability_id: str = "decoy",
    ) -> "AbilityConfig":
        """Load single ability configuration from balance.json."""
        p = Path(path) if path else BALANCE_PATH
        if not p.exists():
            return cls(id=ability_id, name=ability_id)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        a_dict = data.get("abilities", {}).get(ability_id, {})
        return cls.load_from_dict(a_dict)


class DecoyEntity:
    """
    Entangled holographic decoy deployed in the combat field.
    Draws enemy line-of-sight and targeting vectors away from player.
    """

    def __init__(self, x: float, y: float, health: int = 50, duration: float = 4.0):
        self.x: float = float(x)
        self.y: float = float(y)
        self.width: int = 16
        self.height: int = 32
        self.health: int = health
        self.max_health: int = health
        self.duration: float = duration
        self.lifetime: float = duration
        self.is_dead: bool = False
        self.vx = self.vy = 0.0
        self.rect: pygame.Rect = pygame.Rect(int(x), int(y), self.width, self.height)

    def update(self, dt: float):
        """Update decoy lifetime and status."""
        if self.is_dead:
            return
        self.lifetime -= dt
        if self.lifetime <= 0.0 or self.health <= 0:
            self.is_dead = True

    def take_damage(self, amount: int) -> int:
        """Absorb damage directed at decoy."""
        if self.is_dead:
            return 0
        actual = min(self.health, amount)
        self.health -= actual
        if self.health <= 0:
            self.is_dead = True
        return actual


class Ability:
    """
    Base class for player-activated analog abilities.
    Enforces unlock checking, resource cost, cooldown gating, and checkpoint reset rules.
    """

    def __init__(self, config_obj: AbilityConfig):
        self.cfg: AbilityConfig = config_obj
        self.id: str = config_obj.id
        self.name: str = config_obj.name
        self.is_unlocked: bool = (len(config_obj.unlock_events) == 0)
        self.cooldown_timer: float = 0.0
        self.active_timer: float = 0.0
        self.is_active: bool = False

    def check_unlocked(self, campaign: Optional[Any] = None) -> bool:
        """Verify if unlock criteria have been satisfied in campaign state."""
        if len(self.cfg.unlock_events) == 0:
            self.is_unlocked = True
            return True
        if campaign is None:
            return self.is_unlocked

        st = getattr(campaign, "state", None)
        recorded = list(getattr(st, "events_recorded", [])) + list(getattr(st, "completed_event_types", [])) + list(getattr(st, "applied_event_ids", []))
        records = getattr(st, "validation_records", [])
        rec_ids = {r.get("id") if isinstance(r, dict) else getattr(r, "id", "") for r in records}
        inventory = getattr(st, "inventory", {})
        room_flags = getattr(st, "room_flags", {})

        self.is_unlocked = False
        for ev in self.cfg.unlock_events:
            if ev in recorded or ev in rec_ids or inventory.get(ev, 0) > 0 or room_flags.get(ev, False):
                self.is_unlocked = True
                return True
        return self.is_unlocked

    def can_activate(self, current_energy: float, campaign: Optional[Any] = None) -> bool:
        """
        Verify whether ability can be triggered right now.
        Locked equipment CANNOT activate under any circumstances.
        """
        self.check_unlocked(campaign)
        if not self.is_unlocked:
            return False
        if self.cooldown_timer > 0.0:
            return False
        if self.is_active:
            return False
        if current_energy < self.cfg.cost:
            return False
        return True

    def activate(self, player: Any, context: Optional[Any] = None) -> bool:
        """Trigger ability effects and set active timer."""
        self.is_active = True
        self.active_timer = self.cfg.duration
        return True

    def update(self, dt: float, is_paused: bool = False):
        """Update active and cooldown timers."""
        if is_paused or dt <= 0.0:
            return

        if self.is_active:
            self.active_timer -= dt
            if self.active_timer <= 0.0:
                self.is_active = False
                self.active_timer = 0.0
                self.cooldown_timer = self.cfg.cooldown
                self.on_deactivate()

        elif self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

    def on_deactivate(self):
        """Hook called when ability duration expires."""
        pass

    def reset(self):
        """Reset ability state to pristine on death or checkpoint respawn."""
        self.is_active = False
        self.active_timer = 0.0
        self.cooldown_timer = 0.0
        self.on_deactivate()


class QuantumDecoyAbility(Ability):
    """
    Quantum Entanglement Holographic Decoy.
    Projects an analog electromagnetic ghost that draws enemy aim and projectiles.
    """

    def __init__(self, config_obj: Optional[AbilityConfig] = None):
        cfg = config_obj or AbilityConfig.load_from_file(ability_id="decoy")
        super().__init__(cfg)
        self.active_decoy: Optional[DecoyEntity] = None

    def activate(self, player: Any, context: Optional[Any] = None) -> bool:
        super().activate(player, context)
        px = getattr(player, "x", 0.0)
        py = getattr(player, "y", 0.0)
        self.active_decoy = DecoyEntity(
            x=px,
            y=py,
            health=self.cfg.decoy_health,
            duration=self.cfg.duration,
        )
        return True

    def update(self, dt: float, is_paused: bool = False):
        super().update(dt, is_paused=is_paused)
        if self.active_decoy is not None and not is_paused:
            self.active_decoy.update(dt)
            if self.active_decoy.is_dead:
                self.active_decoy = None

    def on_deactivate(self):
        self.active_decoy = None


class PhaseShieldAbility(Ability):
    """
    Biosecurity Phase Barrier.
    Deploys a localized containment forcefield absorbing incoming kinetic and energy damage.
    """

    def __init__(self, config_obj: Optional[AbilityConfig] = None):
        cfg = config_obj or AbilityConfig.load_from_file(ability_id="shielding")
        super().__init__(cfg)
        self.remaining_shield_hp: int = 0

    def activate(self, player: Any, context: Optional[Any] = None) -> bool:
        super().activate(player, context)
        self.remaining_shield_hp = self.cfg.shield_hp
        return True

    def absorb_damage(self, amount: int) -> Tuple[int, int]:
        """
        Absorb damage up to remaining shield capacity.
        Returns: (absorbed_damage, spillover_damage)
        """
        if not self.is_active or self.remaining_shield_hp <= 0:
            return 0, amount

        absorbed = min(self.remaining_shield_hp, amount)
        self.remaining_shield_hp -= absorbed
        spillover = amount - absorbed

        if self.remaining_shield_hp <= 0:
            self.is_active = False
            self.active_timer = 0.0
            self.cooldown_timer = self.cfg.cooldown

        return absorbed, spillover

    def on_deactivate(self):
        self.remaining_shield_hp = 0


class TimeDilationAbility(Ability):
    """
    Relativistic Subspace Dilation.
    Modulates the actor-time modifier so enemies and hazards operate at 0.35x speed.
    """

    def __init__(self, config_obj: Optional[AbilityConfig] = None):
        cfg = config_obj or AbilityConfig.load_from_file(ability_id="time_dilation")
        super().__init__(cfg)

    def get_actor_time_modifier(self) -> float:
        """Returns time scaling factor for enemies and enemy projectiles."""
        if self.is_active:
            return self.cfg.actor_time_modifier
        return 1.0


class SerendipityTapeDeckAbility(Ability):
    """
    Analog Serendipity Tape Deck.
    Broadcasts randomized analog acoustic/RF loops (vinyl noise, erratic jazz pulses)
    that shatter The Core's predictive targeting, break active aim locks,
    and grant the Anomaly Strike buff dealing 3.0x critical damage.
    """

    def __init__(self, config_obj: Optional[AbilityConfig] = None):
        cfg = config_obj or AbilityConfig.load_from_file(ability_id="serendipity_tape_deck")
        super().__init__(cfg)
        self.anomaly_multiplier: float = 3.0

    def activate(self, player: Any, context: Optional[Any] = None) -> bool:
        super().activate(player, context)
        setattr(player, "has_serendipity_buff", True)
        setattr(player, "serendipity_timer", self.cfg.duration)

        # Shatter predictions of any enemies in range
        enemy_mgr = getattr(context, "enemy_manager", None)
        if enemy_mgr is None and hasattr(player, "enemy_manager"):
            enemy_mgr = getattr(player, "enemy_manager")
        if enemy_mgr is not None and hasattr(enemy_mgr, "enemies"):
            self.disrupt_enemy_predictions(enemy_mgr.enemies, player)
        return True

    def disrupt_enemy_predictions(self, enemies: Sequence[Any], player: Any):
        """Shatter predictive locks on all active Core enemies within range."""
        for enemy in enemies:
            if getattr(enemy, "is_dead", False):
                continue
            # Break telegraph locks and force stagger
            if getattr(enemy, "telegraph_active", False) or getattr(enemy, "telegraph_locked", False):
                enemy.telegraph_active = False
                enemy.telegraph_locked = False
                enemy.state = "recovery"
                enemy.state_timer = 1.20
            # Apply prediction_shattered status condition
            if hasattr(enemy, "apply_status"):
                enemy.apply_status("prediction_shattered", self.cfg.duration)

    def on_deactivate(self):
        super().on_deactivate()

    def update(self, dt: float, is_paused: bool = False):
        super().update(dt, is_paused=is_paused)


class AbilityManager:
    """
    Coordinates player ability inventory, energy recharge, active abilities,
    campaign validation unlocking, and HUD status queries.
    """

    def __init__(self, balance_file: Optional[Union[str, Path]] = None):
        p = Path(balance_file) if balance_file else BALANCE_PATH
        energy_cfg = {"max_energy": 100, "recharge_rate": 12.0}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    b_data = json.load(f)
                energy_cfg = b_data.get("abilities", {}).get("energy", energy_cfg)
            except Exception:
                pass

        self.max_energy: float = float(energy_cfg.get("max_energy", 100))
        self.recharge_rate: float = float(energy_cfg.get("recharge_rate", 12.0))
        self.energy: float = self.max_energy

        decoy_cfg = AbilityConfig.load_from_file(balance_file, "decoy")
        shield_cfg = AbilityConfig.load_from_file(balance_file, "shielding")
        dilation_cfg = AbilityConfig.load_from_file(balance_file, "time_dilation")
        tape_cfg = AbilityConfig.load_from_file(balance_file, "serendipity_tape_deck")

        self.abilities: Dict[str, Ability] = {
            "decoy": QuantumDecoyAbility(decoy_cfg),
            "shielding": PhaseShieldAbility(shield_cfg),
            "time_dilation": TimeDilationAbility(dilation_cfg),
            "serendipity_tape_deck": SerendipityTapeDeckAbility(tape_cfg),
        }
        self.ability_order: List[str] = ["decoy", "shielding", "time_dilation", "serendipity_tape_deck"]
        self.selected_ability_id: str = "decoy"

    @property
    def selected_ability(self) -> Ability:
        return self.abilities[self.selected_ability_id]

    def sync_unlocks(self, campaign: Optional[Any] = None):
        """Update unlock status of all abilities based on campaign state."""
        for ab in self.abilities.values():
            ab.check_unlocked(campaign)

    def select_ability(self, ability_id: str) -> bool:
        """Select ability by id. Fails if ability is locked."""
        if ability_id not in self.abilities:
            return False
        ab = self.abilities[ability_id]
        if not ab.is_unlocked:
            return False
        self.selected_ability_id = ability_id
        return True

    def cycle_ability(self, direction: int = 1) -> str:
        """Cycle to next unlocked ability."""
        unlocked = [aid for aid in self.ability_order if self.abilities[aid].is_unlocked]
        if not unlocked:
            return self.selected_ability_id
        if self.selected_ability_id not in unlocked:
            self.selected_ability_id = unlocked[0]
            return self.selected_ability_id
        curr_idx = unlocked.index(self.selected_ability_id)
        next_idx = (curr_idx + direction) % len(unlocked)
        self.selected_ability_id = unlocked[next_idx]
        return self.selected_ability_id

    def trigger_selected_ability(self, player: Any, context: Optional[Any] = None) -> bool:
        """Activate currently selected ability if affordable and off cooldown."""
        ab = self.selected_ability
        if not ab.can_activate(self.energy):
            return False
        self.energy -= ab.cfg.cost
        return ab.activate(player, context)

    def update(self, dt: float, is_paused: bool = False):
        """Recharge energy and step active abilities."""
        if is_paused or dt <= 0.0:
            return

        # Energy recharge
        if self.energy < self.max_energy:
            self.energy = min(self.max_energy, self.energy + self.recharge_rate * dt)

        # Update all abilities
        for ab in self.abilities.values():
            ab.update(dt, is_paused=is_paused)

    def get_actor_time_modifier(self) -> float:
        """Query active time dilation modifier across all abilities."""
        dil = self.abilities.get("time_dilation")
        if isinstance(dil, TimeDilationAbility):
            return dil.get_actor_time_modifier()
        return 1.0

    def get_active_decoy(self) -> Optional[DecoyEntity]:
        """Query active decoy entity if present."""
        dec = self.abilities.get("decoy")
        if isinstance(dec, QuantumDecoyAbility):
            return dec.active_decoy
        return None

    def absorb_shield_damage(self, amount: int) -> Tuple[int, int]:
        """Delegate incoming damage to phase shield if active."""
        sh = self.abilities.get("shielding")
        if isinstance(sh, PhaseShieldAbility):
            return sh.absorb_damage(amount)
        return 0, amount

    def is_serendipity_active(self) -> bool:
        """Query if Serendipity Tape Deck anomaly disruption is currently active."""
        tape = self.abilities.get("serendipity_tape_deck")
        return bool(tape and tape.is_active)

    def reset_on_checkpoint(self):
        """Reset ability timers and restore full energy on player respawn/checkpoint reload."""
        self.energy = self.max_energy
        for ab in self.abilities.values():
            ab.reset()

    def save_state(self) -> Dict[str, Any]:
        """Serialize state for save game / checkpoint persistence."""
        return {
            "energy": self.energy,
            "selected_ability_id": self.selected_ability_id,
            "abilities": {
                aid: {
                    "is_unlocked": ab.is_unlocked,
                    "cooldown_timer": ab.cooldown_timer,
                    "active_timer": ab.active_timer,
                    "is_active": ab.is_active,
                }
                for aid, ab in self.abilities.items()
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for save game / checkpoint persistence."""
        return self.save_state()

    def load_state(self, data: Dict[str, Any]):
        """Restore state from checkpoint data."""
        self.energy = float(data.get("energy", self.max_energy))
        self.selected_ability_id = str(data.get("selected_ability_id", "decoy"))
        ab_data = data.get("abilities", {})
        for aid, s in ab_data.items():
            if aid in self.abilities:
                ab = self.abilities[aid]
                ab.is_unlocked = bool(s.get("is_unlocked", ab.is_unlocked))
                ab.cooldown_timer = float(s.get("cooldown_timer", 0.0))
                ab.active_timer = float(s.get("active_timer", 0.0))
                ab.is_active = bool(s.get("is_active", False))

