"""The selection shared by `gemba list` and `gemba report`: its options, their validation and the scan."""

from __future__ import annotations

import argparse
import datetime
import json
from dataclasses import dataclass

from gemba import config, metadata, tasks, values

# Destination of each date option, named after the Filters field it fills.
DATE_OPTIONS = (
    ("created_from", "--from"),
    ("created_to", "--to"),
    ("updated_from", "--updated-from"),
    ("updated_to", "--updated-to"),
    ("done_from", "--done-from"),
    ("done_to", "--done-to"),
)


@dataclass(frozen=True)
class Scope:
    """The workstream folders a selection scans; unless they were filtered, every stray entry under tasks/ too."""

    workstreams: tuple[str, ...]
    include_archived: bool
    filtered: bool


def add_options(parser: argparse.ArgumentParser) -> None:
    """Register the selection filters on the parser of a command."""
    parser.add_argument(
        "--workstream",
        dest="workstreams",
        action="append",
        default=[],
        metavar="ID",
        help="workstream identifier from gemba.yaml; repeat for several (default: every workstream)",
    )
    parser.add_argument(
        "--status",
        dest="statuses",
        action="append",
        default=[],
        metavar="STATUS",
        help="open, in-progress, blocked or done; repeat for several (default: every status)",
    )
    parser.add_argument("--ref", help="exact task ref, such as SUP-1")
    parser.add_argument(
        "--from", dest="created_from", metavar="YYYY-MM-DD", help="created on or after (the filename date)"
    )
    parser.add_argument(
        "--to", dest="created_to", metavar="YYYY-MM-DD", help="created on or before (the filename date)"
    )
    parser.add_argument("--updated-from", dest="updated_from", metavar="YYYY-MM-DD", help="updated_at on or after")
    parser.add_argument("--updated-to", dest="updated_to", metavar="YYYY-MM-DD", help="updated_at on or before")
    parser.add_argument(
        "--done-from", dest="done_from", metavar="YYYY-MM-DD", help="done_at on or after; tasks without it never match"
    )
    parser.add_argument(
        "--done-to", dest="done_to", metavar="YYYY-MM-DD", help="done_at on or before; tasks without it never match"
    )
    parser.add_argument("--include-archived", action="store_true", help="also read the archive/ folders")
    parser.add_argument(
        "--where",
        dest="conditions",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "metadata condition on a declared key, the value written by the type of the key (null finds unset "
            "values); matches an equal value or a list containing it; repeat a key for alternatives"
        ),
    )
    parser.add_argument(
        "--where-from",
        dest="lower",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="lower bound, included, on a number or date key; one per key; null values never match",
    )
    parser.add_argument(
        "--where-to",
        dest="upper",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="upper bound, included, on a number or date key; one per key; null values never match",
    )


def build(args: argparse.Namespace, gemba_config: config.Config) -> tuple[Scope, tasks.Filters, list[str]]:
    """The scan scope and the filters of the options, and every invalid filter."""
    errors = []
    workstreams = list(dict.fromkeys(args.workstreams))
    for workstream in workstreams:
        if workstream not in gemba_config.workstreams:
            errors.append(
                f"unknown workstream '{workstream}' (valid workstreams: {', '.join(gemba_config.workstreams)})"
            )
    for status in dict.fromkeys(args.statuses):
        if problem := tasks.status_problem(status):
            errors.append(problem)
    dates: dict[str, datetime.date | None] = {}
    for dest, option in DATE_OPTIONS:
        text = getattr(args, dest)
        dates[dest] = None if text is None else values.iso_date(text)
        if text is not None and dates[dest] is None:
            errors.append(f"invalid date '{text}' for {option}: use YYYY-MM-DD")
    conditions, condition_errors = metadata.parse_conditions(
        args.conditions, args.lower, args.upper, gemba_config.types()
    )
    errors.extend(condition_errors)

    # A workstream filter is the scan scope: no other folder is read or reported.
    scope = Scope(tuple(workstreams or gemba_config.workstreams), args.include_archived, bool(workstreams))
    filters = tasks.Filters(
        statuses=args.statuses,
        ref=args.ref,
        created_from=dates["created_from"],
        created_to=dates["created_to"],
        updated_from=dates["updated_from"],
        updated_to=dates["updated_to"],
        done_from=dates["done_from"],
        done_to=dates["done_to"],
        metadata=conditions,
        schemas={
            workstream: [field.name for field in gemba_config.effective_schema(workstream)]
            for workstream in gemba_config.workstreams
        },
    )
    return scope, filters, errors


def select(
    gemba_config: config.Config, scope: Scope, filters: tasks.Filters
) -> tuple[list[tasks.Task], list[tasks.Problem]]:
    """The tasks of the scope that pass the filters, and the problems of the scan.

    Every value of a scanned task whose key has a declared type and that is not of that
    type is a problem too, whatever the filters, and its task is still selected when it
    matches.
    """
    found, problems = tasks.scan(
        gemba_config.root,
        scope.workstreams,
        scope.include_archived,
        configured=None if scope.filtered else list(gemba_config.workstreams),
    )
    types = gemba_config.types()
    for task in found:
        for key, value in task.metadata.items():
            if key in types and (problem := metadata.value_problem(types[key], value)):
                problems.append(tasks.Problem(task.path, f"metadata value of '{key}' {problem}"))
    problems.sort(key=lambda problem: problem.path)
    return [task for task in found if tasks.matches(task, filters)], problems


def dump(document: object) -> str:
    """A document as `list` and `report` print it: indented JSON, dates as ISO strings."""
    return json.dumps(document, indent=2, ensure_ascii=False, default=_iso)


def _iso(value: object) -> str:
    if isinstance(value, datetime.date):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} is not JSON serializable")
