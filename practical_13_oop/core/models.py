from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")


class IRenderer(ABC, Generic[T]):
    """Interface for rendering domain objects into formatted text."""
    @abstractmethod
    def render(self, target: T) -> str:
        raise NotImplementedError


class IRenderable(ABC, Generic[T]):
    """Interface allowing domain objects to delegate rendering to an external renderer."""
    def __init__(self):
        self._renderer: IRenderer[T] | None = None

    def use_renderer(self, renderer: IRenderer[T]) -> None:
        self._renderer = renderer

    @abstractmethod
    def render(self, renderer: IRenderer[T] | None = None) -> str:
        raise NotImplementedError


class Character(IRenderable["Character"]):
    """Game character entity holding combat stats and rendering delegation."""
    def __init__(self, name: str, role: str, max_hp: int, attack_power: int):
        super().__init__()
        self.name = name
        self.role = role
        self.max_hp = max_hp
        self.hp = max_hp
        self.attack_power = attack_power

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

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

    def render(self, renderer: IRenderer["Character"] | None = None) -> str:
        active_renderer = renderer if renderer is not None else self._renderer
        if active_renderer is None:
            return f"{self.name} [{self.role}] HP: {self.hp}/{self.max_hp}"
        return active_renderer.render(self)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "max_hp": self.max_hp,
            "hp": self.hp,
            "attack_power": self.attack_power,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        char = cls(data["name"], data["role"], data["max_hp"], data["attack_power"])
        char.hp = data["hp"]
        return char


class GameMemento:
    """Memento snapshot capturing game state for persistence."""
    def __init__(self, state_data: dict):
        self._state_data = dict(state_data)

    def get_state(self) -> dict:
        return dict(self._state_data)


class GameSession(IRenderable["GameSession"]):
    """Core game session managing roster, active battle, and turn progression."""
    def __init__(self):
        super().__init__()
        self.roster: list[Character] = [
            Character("Артур", "Воїн", 120, 22),
            Character("Еліна", "Маг", 85, 34),
            Character("Роланд", "Слідопит", 100, 27),
        ]
        self.player: Character | None = None
        self.enemy: Character | None = None
        self.is_active: bool = False
        self.turn: int = 0
        self.score: int = 0

    def select_character(self, index: int) -> Character:
        if index < 0 or index >= len(self.roster):
            raise ValueError("Обрано неіснуючий індекс персонажа.")
        template = self.roster[index]
        self.player = Character(template.name, template.role, template.max_hp, template.attack_power)
        return self.player

    def start_game(self) -> None:
        if self.player is None:
            raise RuntimeError("Спочатку потрібно обрати персонажа.")
        self.is_active = True
        self.turn = 1
        self.score = 0
        self.enemy = Character("Темний Лицар", "Бос", 110, 18)

    def create_memento(self) -> GameMemento:
        return GameMemento({
            "is_active": self.is_active,
            "turn": self.turn,
            "score": self.score,
            "player": self.player.to_dict() if self.player else None,
            "enemy": self.enemy.to_dict() if self.enemy else None,
        })

    def restore_memento(self, memento: GameMemento) -> None:
        data = memento.get_state()
        self.is_active = data["is_active"]
        self.turn = data["turn"]
        self.score = data["score"]
        self.player = Character.from_dict(data["player"]) if data["player"] else None
        self.enemy = Character.from_dict(data["enemy"]) if data["enemy"] else None

    def render(self, renderer: IRenderer["GameSession"] | None = None) -> str:
        active_renderer = renderer if renderer is not None else self._renderer
        if active_renderer is None:
            return f"Хід: {self.turn}, Рахунок: {self.score}"
        return active_renderer.render(self)
