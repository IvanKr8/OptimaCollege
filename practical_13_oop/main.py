import sys
import logging
from cli.facade import CLI
from cli.strategies import InfoCommandStrategy, GameplayCommandStrategy, InfrastructureCommandStrategy
from core.models import GameSession
from data.storage import FileSaveRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def build_application(out_stream=None, save_path: str = "savegame.json") -> tuple[CLI, GameSession]:
    session = GameSession()
    repository = FileSaveRepository(save_path)
    cli = CLI(out_stream=out_stream)

    cli.use_strategy(InfoCommandStrategy(cli, session))
    cli.use_strategy(GameplayCommandStrategy(cli, session))
    cli.use_strategy(InfrastructureCommandStrategy(cli, session, repository))
    return cli, session


def main() -> None:
    cli, _ = build_application()
    if len(sys.argv) > 1:
        cli.exec_command(" ".join(sys.argv[1:]))
        return

    cli.write_line("Консольна текстова гра запущена. Введіть 'help' для перегляду команд.")
    while cli.running:
        try:
            raw_input = input("> ")
            cli.exec_command(raw_input)
        except (KeyboardInterrupt, EOFError):
            cli.write_line("\nРоботу перервано користувачем.")
            break


if __name__ == "__main__":
    main()
