import logging
from abc import ABC, abstractmethod
from typing import Callable
from cli.parser import Args
from cli.graphics import CharacterRenderer, GameStateRenderer
from core.models import GameSession, CharacterProfile
from data.storage import FileSaveRepository


class Command:
    def __init__(self, name: str, description: str, handler: Callable[[Args], None]):
        self.name = name
        self.description = description
        self.handler = handler

    def execute(self, args: Args) -> None:
        self.handler(args)


class ICommandStrategy(ABC):
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
    def __init__(self, cli: "CLI", session: GameSession):
        super().__init__()
        self.cli = cli
        self.session = session
        self.register_command("heroes", "Показати список доступних персонажів", self._show_heroes)
        self.register_command("status", "Показати поточний стан гри", self._show_status)
        self.register_command("history", "Вивести історію ходів поточного бою", self._show_history)
        self.register_command("help", "Вивести перелік усіх доступних команд", self._show_help)

    def _show_heroes(self, args: Args) -> None:
        self.cli.write_line("Доступні персонажі для вибору:")
        for idx, hero in enumerate(self.session.roster, start=1):
            self.cli.write_line(f"  {idx}. {hero.name} | Клас: {hero.role} | HP: {hero.max_hp} | Шкода: {hero.damage} | Броня: {hero.armor}")

    def _show_status(self, args: Args) -> None:
        self.session.use_renderer(GameStateRenderer())
        self.cli.display(self.session)

    def _show_history(self, args: Args) -> None:
        self.cli.write_line("Історія ходів поточного бою:")
        if not self.session.history:
            self.cli.write_line("  Історія порожня.")
        else:
            for record in self.session.history:
                self.cli.write_line(f"  {record.to_string()}")

    def _show_help(self, args: Args) -> None:
        self.cli.write_line("Список доступних команд:")
        for name, desc in self.cli.list_all_commands():
            self.cli.write_line(f"  {name:<10} : {desc}")


class GameplayCommandStrategy(ICommandStrategy):
    def __init__(self, cli: "CLI", session: GameSession):
        super().__init__()
        self.cli = cli
        self.session = session
        self.register_command("select", "Обрати персонажа за номером: select <номер>", self._select_hero)
        self.register_command("start", "Розпочати нову гру з обраним персонажем", self._start_game)
        self.register_command("attack", "Зробити атаку у покроковому режимі бою", self._attack)

    def _select_hero(self, args: Args) -> None:
        if not args.positional or not args.positional[0].isdigit():
            self.cli.write_line("Вкажіть номер персонажа, наприклад: select 1")
            return
        idx = int(args.positional[0]) - 1
        try:
            hero = self.session.select_character(idx)
            hero.use_renderer(CharacterRenderer())
            self.cli.write_line(f"Обрано персонажа: {hero.name}")
            self.cli.display(hero)
        except ValueError as err:
            self.cli.write_line(str(err))

    def _start_game(self, args: Args) -> None:
        try:
            self.session.start_game()
            self.cli.write_line("Бій розпочато у покроковому режимі.")
            self.session.use_renderer(GameStateRenderer())
            self.cli.display(self.session)
        except RuntimeError as err:
            self.cli.write_line(str(err))

    def _attack(self, args: Args) -> None:
        if not self.session.is_active:
            self.cli.write_line("Гра не активна. Виконайте start.")
            return
        result = self.session.execute_player_attack()
        self.cli.write_line(result)
        self.session.use_renderer(GameStateRenderer())
        self.cli.display(self.session)


class InfrastructureCommandStrategy(ICommandStrategy):
    def __init__(self, cli: "CLI", session: GameSession, repository: FileSaveRepository):
        super().__init__()
        self.cli = cli
        self.session = session
        self.repository = repository
        self.register_command("save", "Зберегти стан гри у файл", self._save_game)
        self.register_command("load", "Завантажити стан гри з файлу", self._load_game)
        self.register_command("exit", "Вийти з додатка", self._exit_app)

    def _save_game(self, args: Args) -> None:
        state = self.session.create_memento()
        self.repository.save(state)
        self.cli.write_line("Стан гри успішно збережено.")

    def _load_game(self, args: Args) -> None:
        try:
            state = self.repository.load()
            self.session.restore_memento(state)
            self.cli.write_line("Збереження успішно завантажено.")
            self.session.use_renderer(GameStateRenderer())
            self.cli.display(self.session)
        except FileNotFoundError as err:
            self.cli.write_line(str(err))

    def _exit_app(self, args: Args) -> None:
        self.cli.write_line("Вихід з додатка.")
        self.cli.running = False
