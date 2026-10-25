"""`gemba report`: select tasks as `gemba list` does, then count, group and sum them in one JSON document."""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

from gemba import config, report
from gemba.commands import selection


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "report",
        help="count, group and sum the selected tasks as one JSON document",
        description=(
            "Select tasks with the filters of gemba list, then print one JSON object: `by` and `sum` as given, "
            "`groups`, one entry per combination of grouping values with its task count, refs and sums, "
            "`total`, over every selected task counted once, and `problems`, as gemba list reports them. "
            "Sums are exact; a task without a number to add is counted as missing."
        ),
    )
    selection.add_options(parser)
    parser.add_argument(
        "--by",
        dest="groupings",
        action="append",
        default=[],
        metavar="KEY",
        help="group by workstream, status, or a declared text or boolean field; repeat to group within groups",
    )
    parser.add_argument(
        "--sum",
        dest="sums",
        action="append",
        default=[],
        metavar="KEY",
        help="add up a declared number field per group and in the total; repeat for several",
    )
    parser.add_argument("--root", type=Path, help="obeya root (default: walk up to the nearest gemba.yaml)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail(str(exc))

    scope, filters, errors = selection.build(args, gemba_config)
    types = gemba_config.types()
    errors.extend(report.problems(args.groupings, args.sums, types))
    if errors:
        return fail("nothing reported:\n" + "\n".join(f"- {error}" for error in errors))

    found, problems = selection.select(gemba_config, scope, filters)
    result = report.aggregate(found, args.groupings, args.sums, types, list(gemba_config.workstreams))
    document = {
        "by": args.groupings,
        "sum": args.sums,
        "groups": [
            {"key": group.key, "tasks": group.tasks, "refs": group.refs, "sums": sums(group.sums)}
            for group in result.groups
        ],
        "total": {"tasks": result.tasks, "sums": sums(result.sums)},
        "problems": [dataclasses.asdict(problem) for problem in problems],
    }
    print(selection.dump(document))
    return 0


def sums(found: dict[str, report.Sum]) -> dict[str, dict[str, object]]:
    return {key: {"total": total.total, "missing": total.missing} for key, total in found.items()}


def fail(message: str) -> int:
    print(f"gemba report: {message}", file=sys.stderr)
    return 1
