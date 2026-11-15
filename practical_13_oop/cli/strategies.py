import logging
from abc import ABC, abstractmethod
from typing import Callable
from cli.parser import Args
from cli.graphics import CharacterRenderer, GameStateRenderer
from core.models import GameSession
from data.storage import FileSaveRepository


class Command:
    """Encapsulates a single CLI command handler and its description."""
    def __init__(self, name: str, description: str, handler: Callable[[Args], None]):
        self.name = name
        self.description = description
        self.handler = handler

    def execute(self, args: Args) -> None:
        self.handler(args)


class ICommandStrategy(ABC):
    """Strategy interface for grouping and executing related CLI commands."""
    def __init__(self):
        self._commands: dict[str, Command] = {}

    def get_command_selectors(self) -> list[str]:
        return list(self._commands.keys())

    def get_commands_info(self) -> list[tuple[str, str]]:
        return [(cmd.name, cmd.description) for cmd in self._commands.values()]

    def register_command(self, name: str, description: str, func: Callable[[Args], None]) -> None:
        self._commands[name.lower()] = Command(name.lower(), description, func)

    def exec_command(self, selector: str, args: Args) -> None:
        cmd = self._commands.get(selector.lower())
        if cmd is None:
            raise KeyError(f"Команда '{selector}' не знайдена у стратегії.")
        cmd.execute(args)


class InfoCommandStrategy(ICommandStrategy):
    """Strategy responsible for displaying characters, stats, and help information."""
    def __init__(self, cli: "CLI", session: GameSession):
        super().__init__()
        self.cli = cli
        self.session = session
        self.register_command("heroes", "Показати список доступних персонажів", self._show_heroes)
        self.register_command("status", "Показати поточний стан гри", self._show_status)
        self.register_command("help", "Вивести перелік усіх доступних команд", self._show_help)

    def _show_heroes(self, args: Args) -> None:
        self.cli.write_line("Доступні персонажі для вибору:")
        for idx, hero in enumerate(self.session.roster, start=1):
            self.cli.write_line(f"  {idx}. {hero.name} | Клас: {hero.role} | HP: {hero.max_hp} | Атака: {hero.attack_power}")
        if "detail" in args.options and args.options["detail"].isdigit():
            idx = int(args.options["detail"]) - 1
            if 0 <= idx < len(self.session.roster):
                hero = self.session.roster[idx]
                hero.use_renderer(CharacterRenderer())
                self.cli.display(hero)

    def _show_status(self, args: Args) -> None:
        self.session.use_renderer(GameStateRenderer())
        self.cli.display(self.session)

    def _show_help(self, args: Args) -> None:
        self.cli.write_line("Список доступних команд:")
        for name, desc in self.cli.list_all_commands():
            self.cli.write_line(f"  {name:<10} : {desc}")


class GameplayCommandStrategy(ICommandStrategy):
    """Strategy handling character selection, game start, and combat turn actions."""
    def __init__(self, cli: "CLI", session: GameSession):
        super().__init__()
        self.cli = cli
        self.session = session
        self.register_command("select", "Обрати персонажа за номером: select <номер>", self._select_hero)
        self.register_command("start", "Розпочати нову гру з обраним персонажем", self._start_game)
        self.register_command("attack", "Атакувати противника у поточному ході", self._attack)
        self.register_command("heal", "Відновити здоров'я персонажа", self._heal)

    def _select_hero(self, args: Args) -> None:
        if not args.positional or not args.positional[0].isdigit():
            self.cli.write_line("Вкажіть номер персонажа, наприклад: select 1")
            return
        idx = int(args.positional[0]) - 1
        try:
            hero = self.session.select_character(idx)
            hero.use_renderer(CharacterRenderer())
            logging.info(f"Користувач обрав персонажа {hero.name}")
            self.cli.write_line(f"Обрано персонажа: {hero.name}")
            self.cli.display(hero)
        except ValueError as err:
            self.cli.write_line(str(err))

    def _start_game(self, args: Args) -> None:
        try:
            self.session.start_game()
            logging.info("Розпочато нову ігрову сесію.")
            self.cli.write_line("Гру розпочато. Бій проти Темного Лицаря почався.")
            self.session.use_renderer(GameStateRenderer())
            self.cli.display(self.session)
        except RuntimeError as err:
            self.cli.write_line(str(err))

    def _attack(self, args: Args) -> None:
        if not self.session.is_active or self.session.player is None or self.session.enemy is None:
            self.cli.write_line("Гра ще не активна. Виконайте команду start.")
            return

        dmg = self.session.enemy.take_damage(self.session.player.attack_power)
        self.session.score += dmg * 10
        self.cli.write_line(f"{self.session.player.name} завдає {dmg} шкоди ворогу.")

        if not self.session.enemy.is_alive:
            self.session.is_active = False
            self.session.score += 500
            logging.info("Гравець переміг у бою.")
            self.cli.write_line(f"Перемога. Підсумковий рахунок: {self.session.score}")
            return

        enemy_dmg = self.session.player.take_damage(self.session.enemy.attack_power)
        self.cli.write_line(f"{self.session.enemy.name} відповідає ударом на {enemy_dmg} шкоди.")

        if not self.session.player.is_alive:
            self.session.is_active = False
            logging.info("Персонаж гравця зазнав поразки.")
            self.cli.write_line("Ваш персонаж загинув. Гру завершено.")
            return

        self.session.turn += 1
        self.session.use_renderer(GameStateRenderer())
        self.cli.display(self.session)

    def _heal(self, args: Args) -> None:
        if not self.session.is_active or self.session.player is None or self.session.enemy is None:
            self.cli.write_line("Лікування доступне лише під час активної гри.")
            return

        restored = self.session.player.heal(20)
        self.cli.write_line(f"{self.session.player.name} відновив {restored} очок здоров'я.")
        enemy_dmg = self.session.player.take_damage(self.session.enemy.attack_power)
        self.cli.write_line(f"{self.session.enemy.name} атакує у відповідь на {enemy_dmg} шкоди.")
        if not self.session.player.is_alive:
            self.session.is_active = False
            self.cli.write_line("Ваш персонаж загинув. Гру завершено.")
            return
        self.session.turn += 1


class InfrastructureCommandStrategy(ICommandStrategy):
    """Strategy handling persistence and application lifecycle commands."""
    def __init__(self, cli: "CLI", session: GameSession, repository: FileSaveRepository):
        super().__init__()
        self.cli = cli
        self.session = session
        self.repository = repository
        self.register_command("save", "Зберегти поточний стан гри у файл", self._save_game)
        self.register_command("load", "Завантажити збережений стан гри з файлу", self._load_game)
        self.register_command("exit", "Вийти з консольного додатка", self._exit_app)

    def _save_game(self, args: Args) -> None:
        memento = self.session.create_memento()
        self.repository.save(memento)
        logging.info("Стан гри збережено у файл.")
        self.cli.write_line("Стан і результати гри успішно збережено.")

    def _load_game(self, args: Args) -> None:
        try:
            memento = self.repository.load()
            self.session.restore_memento(memento)
            logging.info("Стан гри відновлено зі збереження.")
            self.cli.write_line("Збереження успішно завантажено.")
            self.session.use_renderer(GameStateRenderer())
            self.cli.display(self.session)
        except FileNotFoundError as err:
            self.cli.write_line(str(err))

    def _exit_app(self, args: Args) -> None:
        logging.info("Користувач ініціював вихід із програми.")
        self.cli.write_line("Завершення роботи додатка.")
        self.cli.running = False
