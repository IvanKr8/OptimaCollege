from core.models import IRenderer, Character, GameSession


class CLIGraphic:
    """Utility helpers for drawing console borders, tables, and health bars."""
    @staticmethod
    def box(title: str, lines: list[str], width: int = 56) -> str:
        top = f"+{'=' * (width - 2)}+"
        header = f"| {title.ljust(width - 4)} |"
        sep = f"+{'-' * (width - 2)}+"
        body = [f"| {line.ljust(width - 4)} |" for line in lines]
        return "\n".join([top, header, sep, *body, top])

    @staticmethod
    def health_bar(current: int, maximum: int, bar_len: int = 16) -> str:
        ratio = 0.0 if maximum <= 0 else max(0.0, min(1.0, current / maximum))
        filled = int(round(ratio * bar_len))
        return f"[{'#' * filled}{'.' * (bar_len - filled)}] {current}/{maximum}"


class CharacterRenderer(IRenderer[Character]):
    """Concrete console renderer for Character objects."""
    def render(self, target: Character) -> str:
        hp_bar = CLIGraphic.health_bar(target.hp, target.max_hp)
        lines = [
            f"Ім'я: {target.name}",
            f"Клас: {target.role}",
            f"Здоров'я: {hp_bar}",
            f"Сила атаки: {target.attack_power}",
        ]
        return CLIGraphic.box("КАРТКА ПЕРСОНАЖА", lines)


class GameStateRenderer(IRenderer[GameSession]):
    """Concrete console renderer for the active GameSession state."""
    def render(self, target: GameSession) -> str:
        if not target.is_active or target.player is None or target.enemy is None:
            selected = target.player.name if target.player else "не обрано"
            lines = [
                "Статус гри: очікування старту",
                f"Обраний герой: {selected}",
                "Введіть 'heroes' та 'select <номер>' для підготовки.",
            ]
            return CLIGraphic.box("СТАН ІГРОВОЇ СЕСІЇ", lines)

        p_hp = CLIGraphic.health_bar(target.player.hp, target.player.max_hp)
        e_hp = CLIGraphic.health_bar(target.enemy.hp, target.enemy.max_hp)
        lines = [
            f"Хід: {target.turn} | Очки: {target.score}",
            f"Герой {target.player.name}: {p_hp}",
            f"Ворог {target.enemy.name}: {e_hp}",
        ]
        return CLIGraphic.box("АРЕНА БОЮ", lines)
