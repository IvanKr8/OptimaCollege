import sys
from cli.parser import ArgParser
from cli.strategies import ICommandStrategy
from core.models import IRenderable


class CLI:
    """Facade coordinating argument parsing, command strategies, and console rendering."""
    def __init__(self, out_stream=None):
        self.out = out_stream if out_stream is not None else sys.stdout
        self.parser = ArgParser()
        self._strategies: list[ICommandStrategy] = []
        self._selector_map: dict[str, ICommandStrategy] = {}
        self.running: bool = True

    def use_strategy(self, strategy: ICommandStrategy) -> None:
        self._strategies.append(strategy)
        for selector in strategy.get_command_selectors():
            self._selector_map[selector.lower()] = strategy

    def list_all_commands(self) -> list[tuple[str, str]]:
        result = []
        for strategy in self._strategies:
            result.extend(strategy.get_commands_info())
        return result

    def display(self, renderable: IRenderable) -> None:
        output = renderable.render()
        self.write_line(output)

    def write_line(self, text: str) -> None:
        self.out.write(text + "\n")
        self.out.flush()

    def exec_command(self, raw_string: str) -> None:
        args = self.parser.parse_args(raw_string)
        if not args.command:
            return
        strategy = self._selector_map.get(args.command)
        if strategy is None:
            self.write_line(f"Невідома команда '{args.command}'. Введіть 'help' для довідки.")
            return
        strategy.exec_command(args.command, args)
