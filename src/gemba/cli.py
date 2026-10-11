"""Entry point of the `gemba` command: subcommand dispatch and `--version`."""

import argparse
import sys
from collections.abc import Sequence
from importlib.metadata import version
from typing import NoReturn

from gemba.commands import archive, config, create, harness, init, mark, record, report, skills, worktree
from gemba.commands import list as list_  # named after the process; the alias keeps list() usable
from gemba.commands import set as set_  # named after the process; the alias keeps set() usable

COMMANDS = (init, create, list_, skills, config, harness, record, mark, archive, report, set_, worktree)


class ArgumentParser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit with 1, like every other gemba error."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser(prog="gemba", description="Task-based system for working with AI agents.")
    parser.add_argument("--version", action="version", version=version("gemba-cli"))
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    for command in COMMANDS:
        command.register(subparsers)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(sys.stderr)
        return 1
    return args.handler(args)
