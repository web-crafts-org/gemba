"""`gemba set`: write metadata values of a task after its creation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gemba import config, metadata, tasks


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "set",
        help="set metadata values of a task",
        description=(
            "Write metadata values into the task with this ref, archives included, each converted by the "
            "declared type of its field. The metadata map is completed with the keys of the current schema, "
            "as null, and keeps the keys the schema no longer declares. Only the metadata is rewritten: "
            "updated_at, the body, the harness of the task and git are not touched."
        ),
    )
    parser.add_argument("ref", help="ref of the task, such as SUP-1")
    parser.add_argument(
        "assignments",
        nargs="+",
        metavar="KEY=VALUE",
        help=(
            "key=value sets a value written by the type of its field, key=null clears it, and key+=number adds "
            "to a number field, null counting as zero; repeat a key of a text field to set a list"
        ),
    )
    parser.add_argument("--root", type=Path, help="tasks repo root (default: walk up to the nearest gemba.yaml)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail(str(exc))

    assignments, errors = metadata.parse_assignments(args.assignments, allow_add=True)
    try:
        task = tasks.find_by_ref(gemba_config.root, gemba_config.workstreams, args.ref)
    except tasks.TaskError as exc:
        task = None
        errors.append(str(exc))
    else:
        if task is None:
            errors.append(f"no task has ref '{args.ref}' under {tasks.TASKS_DIR}/, archives included")
    assigned = None
    if task is not None:
        schema = gemba_config.effective_schema(task.workstream)
        assigned = metadata.assign(schema, task.metadata, assignments, f"'{task.workstream}'")
        errors.extend(assigned.problems)
    if errors:
        return fail("metadata not set:\n" + "\n".join(f"- {error}" for error in errors))
    assert task is not None and assigned is not None, "every failed check appended an error"

    if assigned.changed:
        task_file = gemba_config.root / task.path
        try:
            text = tasks.set_metadata(task_file.read_bytes().decode("utf-8"), assigned.values)
        except tasks.TaskError as exc:
            return fail(f"metadata not set: {task.path}: {exc}")
        task_file.write_bytes(text.encode("utf-8"))
    print(task.path)
    for change in assigned.changes:
        if change.added:
            print(f"{change.key}: added as null")
        elif change.changed:
            print(f"{change.key}: {metadata.show(change.old)} -> {metadata.show(change.new)}")
        else:
            print(f"{change.key}: {metadata.show(change.new)} (unchanged)")
    return 0


def fail(message: str) -> int:
    print(f"gemba set: {message}", file=sys.stderr)
    return 1
