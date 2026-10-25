"""`gemba list`: validate the filters, scan the workstream folders and print one JSON document."""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

from gemba import config
from gemba.commands import selection


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "list",
        help="list tasks as one JSON document",
        description=(
            "Scan the workstream folders of gemba.yaml, validate every task file and print one JSON object: "
            "`tasks`, the matching task records, and `problems`, the files that are not valid tasks and the "
            "metadata values that are not of the type their field declares. Values of one filter are "
            "alternatives; different filters must all match. Date ranges and bounds are inclusive."
        ),
    )
    selection.add_options(parser)
    parser.add_argument("--root", type=Path, help="obeya root (default: walk up to the nearest gemba.yaml)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail(str(exc))

    scope, filters, errors = selection.build(args, gemba_config)
    if errors:
        return fail("nothing listed:\n" + "\n".join(f"- {error}" for error in errors))

    found, problems = selection.select(gemba_config, scope, filters)
    document = {
        "tasks": [dataclasses.asdict(task) for task in found],
        "problems": [dataclasses.asdict(problem) for problem in problems],
    }
    print(selection.dump(document))
    return 0


def fail(message: str) -> int:
    print(f"gemba list: {message}", file=sys.stderr)
    return 1
