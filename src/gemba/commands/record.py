"""`gemba record`: write the drafted update of a day into a task, from its harness or from the tasks repo."""

from __future__ import annotations

import argparse
import datetime
import sys
import textwrap
from pathlib import Path, PurePosixPath

from gemba import config, harness, platform, skills, tasks, values
from gemba.commands import harness as harness_command


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "record",
        help="write the drafted update of a day into a task, from its harness or from the tasks repo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.fill(
            f"Write the bullets of a draft under ### YYYY-MM-DD in the {tasks.UPDATES_HEADING} section of a task, "
            "appending them when that day already has a subsection, move updated_at to the day when it is later, "
            "and delete the draft. Inside a harness the task is the one of the harness and the path of the draft "
            "is relative to the harness root. From the tasks repo the task is named by its ref, archives included, "
            "and the draft lies directly in the tasks repo root. Nothing is committed.",
            width=79,
        ),
    )
    parser.add_argument(
        "ref",
        nargs="?",
        help="ref of the task, such as SUP-1: required from the tasks repo; inside a harness, only the ref of its task",
    )
    parser.add_argument(
        "file",
        help=f"the draft, such as update.md, relative to the root of the harness or of the tasks repo: lines "
        f"starting with '{tasks.BULLET_PREFIX}', continued by lines indented by two spaces",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="the day the update is about (default: today); not after today, not before the task was created",
    )
    parser.add_argument(
        "--harness", type=Path, help=f"harness root (default: walk up to the nearest {harness.CONFIG_FILENAME})"
    )
    parser.add_argument(
        "--root", type=Path, help=f"tasks repo root (default: walk up to the nearest {config.CONFIG_FILENAME})"
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        folder = harness_root(args.harness)
    except harness.HarnessError as exc:
        return fail(str(exc))
    if folder is None and args.ref is None:
        return fail(
            "no harness found and no ref given: outside a harness, name the task by its ref, "
            "as in gemba record <ref> update.md"
        )
    try:
        gemba_config = config.load(root=args.root, cwd=folder)
        identity = None if folder is None else harness.read_config(folder, list(skills.PROVIDERS))
    except (harness.HarnessError, config.ConfigError) as exc:
        return fail(str(exc))

    root = gemba_config.root
    errors = []
    task: tasks.Task | None = None
    if folder is None or identity is None:
        place: tasks.Place = "repo"
        base = root
        try:
            task = tasks.find_by_ref(root, gemba_config.workstreams, args.ref)
        except tasks.TaskError as exc:
            errors.append(str(exc))
        else:
            if task is None:
                errors.append(f"no task has ref '{args.ref}' under {tasks.TASKS_DIR}/, archives included")
    else:
        place, base = "harness", folder
        task_file = root / identity.task
        if not task_file.is_file():
            return fail(
                f"record not done: the task file {identity.task} named by {harness.CONFIG_FILENAME} "
                f"was not found there, under {root}"
            )
        archived = PurePosixPath(identity.task).parent.name == tasks.ARCHIVE_DIR
        try:
            task = tasks.read(task_file, root, identity.workstream, archived)
        except tasks.TaskError as exc:
            return fail(f"record not done: {identity.task} is not a valid task: {exc}")
        if args.ref is not None and (problem := harness.ref_problem(args.ref, identity)):
            errors.append(problem)
    text = None if task is None else platform.decode((root / task.path).read_bytes())

    today = datetime.date.today()
    day = today if args.date is None else values.iso_date(args.date)
    if day is None:
        errors.append(f"invalid date '{args.date}': use YYYY-MM-DD")
    # Without a task there is no creation date to compare with, only today.
    elif problem := tasks.date_problem(day, task.date if task is not None else datetime.date.min, today):
        errors.append(problem)
    bullets, draft_errors = tasks.read_draft(base, args.file, place)
    errors.extend(f"{args.file} {problem}" for problem in draft_errors)
    if task is not None and text is not None:
        _frontmatter, body = tasks.split(text)
        if problem := tasks.updates_problem(body):
            errors.append(f"{task.path} {problem}")
    if errors:
        return fail("record not done:\n" + "\n".join(f"- {error}" for error in errors))
    assert task is not None and text is not None and day is not None, "every failed check appended an error"

    recorded, previous, updated_at = tasks.record(text, task.date, today, day, bullets)
    (root / task.path).write_bytes(recorded.encode("utf-8"))
    try:
        (base / args.file).unlink()
    except OSError as exc:
        return fail(
            f"{task.path} is recorded but the draft {args.file} could not be deleted: {exc.strerror}; "
            "delete it by hand and do not record it again, which would write its bullets twice"
        )
    print(task.path)
    if updated_at == previous:
        print(f"updated_at: {previous.isoformat()} (unchanged)")
    else:
        print(f"updated_at: {previous.isoformat()} -> {updated_at.isoformat()}")
    return 0


def harness_root(given: Path | None) -> Path | None:
    """The harness the record is made in: the one `--harness` names, else the nearest one at or above the working
    directory; None when there is none, and the record is made from the tasks repo."""
    if given is not None:
        return harness_command.locate(given)
    try:
        return harness.find_root(Path.cwd())
    except harness.HarnessError:
        return None


def fail(message: str) -> int:
    print(f"gemba record: {message}", file=sys.stderr)
    return 1
