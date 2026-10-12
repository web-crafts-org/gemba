"""`gemba record`: write the drafted update of a day into the task of a harness."""

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
        help="write the drafted update of a day into the task of a harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.fill(
            f"Write the bullets of a draft under ### YYYY-MM-DD in the {tasks.UPDATES_HEADING} section of the task "
            "of this harness, appending them when that day already has a subsection, move updated_at to the day "
            "when it is later, and delete the draft. The path of the draft is relative to the harness root. "
            "Nothing is committed.",
            width=79,
        ),
    )
    parser.add_argument(
        "file",
        help=f"the draft, such as update.md: lines starting with '{tasks.BULLET_PREFIX}', continued by lines "
        f"indented by two spaces",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="the day the update is about (default: today); not after today, not before the task was created",
    )
    harness_command.add_location(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        folder = harness_command.locate(args.harness)
        gemba_config = config.load(root=args.root, cwd=folder)
        identity = harness.read_config(folder, list(skills.PROVIDERS))
    except (harness.HarnessError, config.ConfigError) as exc:
        return fail(str(exc))

    root = gemba_config.root
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
    text = platform.decode(task_file.read_bytes())

    today = datetime.date.today()
    errors = []
    day = today if args.date is None else values.iso_date(args.date)
    if day is None:
        errors.append(f"invalid date '{args.date}': use YYYY-MM-DD")
    elif problem := tasks.date_problem(day, task.date, today):
        errors.append(problem)
    bullets, draft_errors = read_draft(folder, args.file)
    errors.extend(f"{args.file} {problem}" for problem in draft_errors)
    _frontmatter, body = tasks.split(text)
    if problem := tasks.updates_problem(body):
        errors.append(f"{task.path} {problem}")
    if errors:
        return fail("record not done:\n" + "\n".join(f"- {error}" for error in errors))
    assert day is not None, "an invalid date appended an error"

    recorded, previous, updated_at = tasks.record(text, task.date, today, day, bullets)
    task_file.write_bytes(recorded.encode("utf-8"))
    try:
        (folder / args.file).unlink()
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


def read_draft(folder: Path, given: str) -> tuple[list[str], list[str]]:
    """The bullet lines of the draft at `given`, relative to the harness root, and every problem found with it."""
    path = (folder / given).resolve()
    if not path.is_relative_to(folder):
        return [], ["is not inside the harness (paths are relative to the harness root)"]
    if not path.is_file():
        return [], ["is not a file" if path.exists() else "does not exist"]
    try:
        text = platform.decode(path.read_bytes())
    except UnicodeDecodeError:
        return [], ["is not UTF-8 text"]
    return tasks.parse_bullets(text)


def fail(message: str) -> int:
    print(f"gemba record: {message}", file=sys.stderr)
    return 1
