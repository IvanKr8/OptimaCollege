from dataclasses import dataclass, field


@dataclass
class Args:
    """Structured representation of parsed terminal arguments and options."""
    command: str
    positional: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)


class ArgParser:
    """Parses raw terminal input strings into structured Args objects."""
    def parse_args(self, raw_string: str) -> Args:
        tokens = raw_string.strip().split()
        if not tokens:
            return Args(command="")

        command = tokens[0].lower()
        positional = []
        options = {}

        idx = 1
        while idx < len(tokens):
            token = tokens[idx]
            if token.startswith("--"):
                key = token[2:]
                if idx + 1 < len(tokens) and not tokens[idx + 1].startswith("--"):
                    options[key] = tokens[idx + 1]
                    idx += 2
                else:
                    options[key] = "true"
                    idx += 1
            else:
                positional.append(token)
                idx += 1

        return Args(command=command, positional=positional, options=options)
