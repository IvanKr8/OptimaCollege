from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional

T = TypeVar("T")


class IRenderer(ABC, Generic[T]):
    @abstractmethod
    def render(self, target: T) -> str:
        raise NotImplementedError


class IRenderable(ABC, Generic[T]):
    def __init__(self):
        self._renderer: IRenderer[T] | None = None

    def use_renderer(self, renderer: IRenderer[T]) -> None:
        self._renderer = renderer

    @abstractmethod
    def render(self, renderer: IRenderer[T] | None = None) -> str:
        raise NotImplementedError


class CharacterProfile:
    """Character profile containing stats, items, and abilities."""
    def __init__(self, name: str, role: str, hp: int, damage: int, armor: int, resist: float, speed: int):
        self.name = name
        self.role = role
        self.max_hp = hp
        self.hp = hp
        self.damage = damage
        self.armor = armor
        self.resist = resist
        self.speed = speed
        self.items: list[str] = []
        self.abilities: list[str] = []

    def add_item(self, item_name: str) -> None:
        self.items.append(item_name)

    def add_ability(self, ability_name: str) -> None:
        self.abilities.append(ability_name)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def calculate_physical_damage(self, target: "CharacterProfile") -> int:
        """Calculates physical damage using armor and resistance formulas."""
        net_dmg = max(0, self.damage - target.armor)
        final_dmg = int(net_dmg * (1.0 - target.resist))
        return max(1, final_dmg)

    def calculate_magic_damage(self, target: "CharacterProfile", res_pen: float = 0.0) -> int:
        """Calculates magic damage ignoring armor with resistance penetration."""
        effective_resist = max(0.0, target.resist - res_pen)
        base_magic = float(self.damage)
        final_dmg = int(base_magic * (1.0 - effective_resist))
        return max(1, final_dmg)

    def take_damage(self, amount: int) -> int:
        actual = max(0, amount)
        self.hp = max(0, self.hp - actual)
        return actual

    def heal(self, amount: int) -> int:
        if not self.is_alive:
            return 0
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + max(0, amount))
        return self.hp - old_hp

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "max_hp": self.max_hp,
            "hp": self.hp,
            "damage": self.damage,
            "armor": self.armor,
            "resist": self.resist,
            "speed": self.speed,
            "items": self.items,
            "abilities": self.abilities,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterProfile":
        profile = cls(
            data["name"],
            data["role"],
            data["max_hp"],
            data["damage"],
            data["armor"],
            data["resist"],
            data["speed"],
        )
        profile.hp = data["hp"]
        profile.items = list(data.get("items", []))
        profile.abilities = list(data.get("abilities", []))
        return profile


class TurnRecord:
    """Encapsulates a single turn action record for combat history."""
    def __init__(self, turn_number: int, actor: str, action_type: str, details: str):
        self.turn_number = turn_number
        self.actor = actor
        self.action_type = action_type
        self.details = details

    def to_string(self) -> str:
        return f"[Хід {self.turn_number}] {self.actor} виконує '{self.action_type}': {self.details}"


class GameConfig:
    """Game configuration container for save/load persistence."""
    def __init__(self, difficulty: str = "Normal"):
        self.difficulty = difficulty

    def to_dict(self) -> dict:
        return {"difficulty": self.difficulty}

    @classmethod
    def from_dict(cls, data: dict) -> "GameConfig":
        return cls(difficulty=data.get("difficulty", "Normal"))


class GameSession(IRenderable["GameSession"]):
    """Core game session managing turn-based logic, profiles, and history."""
    def __init__(self):
        super().__init__()
        self.config = GameConfig()
        self.roster: list[CharacterProfile] = [
            CharacterProfile("Артур", "Воїн", 120, 25, 8, 0.1, 100),
            CharacterProfile("Еліна", "Маг", 90, 35, 3, 0.05, 120),
            CharacterProfile("Роланд", "Слідопит", 100, 28, 5, 0.08, 110),
        ]
        self.player: Optional[CharacterProfile] = None
        self.enemy: Optional[CharacterProfile] = None
        self.is_active: bool = False
        self.turn_number: int = 0
        self.score: int = 0
        self.history: list[TurnRecord] = []

    def select_character(self, index: int) -> CharacterProfile:
        if index < 0 or index >= len(self.roster):
            raise ValueError("Обрано неіснуючий індекс персонажа.")
        template = self.roster[index]
        self.player = CharacterProfile(
            template.name, template.role, template.max_hp,
            template.damage, template.armor, template.resist, template.speed
        )
        return self.player

    def start_game(self) -> None:
        if self.player is None:
            raise RuntimeError("Спочатку потрібно обрати персонажа.")
        self.is_active = True
        self.turn_number = 1
        self.score = 0
        self.history.clear()
        self.enemy = CharacterProfile("Темний Лицар", "Бос", 130, 22, 10, 0.15, 95)
        self.history.append(TurnRecord(self.turn_number, "Система", "Старт", "Бій розпочато проти Темного Лицаря."))

    def execute_player_attack(self) -> str:
        if not self.is_active or self.player is None or self.enemy is None:
            return "Гра не активна."
        
        dmg = self.player.calculate_physical_damage(self.enemy)
        self.enemy.take_damage(dmg)
        self.score += dmg * 10
        msg = f"{self.player.name} завдає {dmg} фізичної шкоди ворогу ({self.enemy.hp}/{self.enemy.max_hp} HP)."
        self.history.append(TurnRecord(self.turn_number, self.player.name, "Атака", msg))

        if not self.enemy.is_alive:
            self.is_active = False
            self.score += 500
            win_msg = "Ворога переможено!"
            self.history.append(TurnRecord(self.turn_number, "Система", "Перемога", win_msg))
            return msg + " " + win_msg

        # Enemy counter attack
        edmg = self.enemy.calculate_physical_damage(self.player)
        self.player.take_damage(edmg)
        emsg = f"{self.enemy.name} контратакує на {edmg} шкоди ({self.player.hp}/{self.player.max_hp} HP)."
        self.history.append(TurnRecord(self.turn_number, self.enemy.name, "Атака", emsg))

        if not self.player.is_alive:
            self.is_active = False
            lose_msg = "Ваш персонаж загинув."
            self.history.append(TurnRecord(self.turn_number, "Система", "Поразка", lose_msg))
            return msg + " " + emsg + " " + lose_msg

        self.turn_number += 1
        return msg + " " + emsg

    def create_memento(self) -> dict:
        return {
            "config": self.config.to_dict(),
            "is_active": self.is_active,
            "turn_number": self.turn_number,
            "score": self.score,
            "player": self.player.to_dict() if self.player else None,
            "enemy": self.enemy.to_dict() if self.enemy else None,
            "history": [{"turn": h.turn_number, "actor": h.actor, "type": h.action_type, "details": h.details} for h in self.history]
        }

    def restore_memento(self, data: dict) -> None:
        self.config = GameConfig.from_dict(data.get("config", {}))
        self.is_active = data["is_active"]
        self.turn_number = data["turn_number"]
        self.score = data["score"]
        self.player = CharacterProfile.from_dict(data["player"]) if data["player"] else None
        self.enemy = CharacterProfile.from_dict(data["enemy"]) if data["enemy"] else None
        self.history = [
            TurnRecord(h["turn"], h["actor"], h["type"], h["details"])
            for h in data.get("history", [])
        ]

    def render(self, renderer: IRenderer["GameSession"] | None = None) -> str:
        if renderer is not None:
            return renderer.render(self)
        return f"Хід: {self.turn_number}, Очки: {self.score}"
