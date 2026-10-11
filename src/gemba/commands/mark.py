"""`gemba mark`: move the status of a task after its creation."""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from gemba import config, tasks, values


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "mark",
        help="move the status of a task",
        description=(
            f"Set the status of the task with this ref to one of {', '.join(tasks.STATUSES)}. Reaching done "
            "writes done_at, leaving done removes it, and updated_at moves to the date when it is later. Only "
            "the frontmatter is rewritten: the body, the harness of the task and git are not touched."
        ),
    )
    parser.add_argument("ref", help="ref of the task, such as SUP-1")
    parser.add_argument("status", help=f"the status to move to: {', '.join(tasks.STATUSES)}")
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="the day of the transition (default: today); not after today, not before the task was created",
    )
    parser.add_argument("--root", type=Path, help="tasks repo root (default: walk up to the nearest gemba.yaml)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail(str(exc))

    errors = []
    if problem := tasks.status_problem(args.status):
        errors.append(problem)
    try:
        task = tasks.find_by_ref(gemba_config.root, gemba_config.workstreams, args.ref)
    except tasks.TaskError as exc:
        task = None
        errors.append(str(exc))
    else:
        if task is None:
            errors.append(f"no task has ref '{args.ref}' under {tasks.TASKS_DIR}/, archives included")
        elif task.archived:
            errors.append(
                f"{task.ref} is archived ({task.path}): move the file out of {tasks.ARCHIVE_DIR}/ before marking it"
            )
    today = datetime.date.today()
    day = today if args.date is None else values.iso_date(args.date)
    if day is None:
        errors.append(f"invalid date '{args.date}': use YYYY-MM-DD")
    # Without a task there is no creation date to compare with, only today.
    elif problem := tasks.date_problem(day, task.date if task is not None else datetime.date.min, today):
        errors.append(problem)
    if errors:
        return fail("task not marked:\n" + "\n".join(f"- {error}" for error in errors))
    assert task is not None and day is not None, "every failed check appended an error"

    task_file = gemba_config.root / task.path
    try:
        text, moved = tasks.transition(task_file.read_bytes().decode("utf-8"), args.status, day)
    except tasks.TaskError as exc:
        return fail(f"task not marked: {task.path}: {exc}")
    if moved.changed:
        task_file.write_bytes(text.encode("utf-8"))
    print(task.path)
    if not moved.changed:
        print(f"status: {moved.old_status}, left as it was")
        return 0
    print(f"status: {moved.old_status} -> {moved.new_status}")
    if moved.done_at is not None:
        print(f"done_at: {moved.done_at.isoformat()}")
    elif moved.done_at_removed:
        print("done_at: removed")
    if moved.new_updated_at == moved.old_updated_at:
        print(f"updated_at: {moved.old_updated_at.isoformat()} (unchanged)")
    else:
        print(f"updated_at: {moved.old_updated_at.isoformat()} -> {moved.new_updated_at.isoformat()}")
    return 0


def fail(message: str) -> int:
    print(f"gemba mark: {message}", file=sys.stderr)
    return 1
