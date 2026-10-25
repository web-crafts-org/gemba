"""`gemba record`: write the drafted update of a day into a task, or copy the history of another task file into it,
from its harness or from the tasks repo."""

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
        help="write the drafted update of a day into a task, or copy the history of another task file into it, "
        "from its harness or from the tasks repo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.fill(
            f"Write the bullets of a draft under ### YYYY-MM-DD in the {tasks.UPDATES_HEADING} section of a task, "
            "appending them when that day already has a subsection, move updated_at to the day when it is later, "
            "and delete the draft. With --from, copy instead the whole dated history of another task file, as it "
            f"is, into a task whose {tasks.UPDATES_HEADING} section is empty, and move updated_at to its last date "
            "when it is later; that file is only read. Inside a harness the task is the one of the harness and the "
            "path of the draft is relative to the harness root. From the tasks repo the task is named by its ref, "
            "archives included, and the draft lies directly in the tasks repo root. Nothing is committed.",
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
        nargs="?",
        help=f"the draft, such as update.md, relative to the root of the harness or of the tasks repo: lines "
        f"starting with '{tasks.BULLET_PREFIX}', continued by lines indented by two spaces; not with --from",
    )
    parser.add_argument(
        "--from",
        dest="source",
        metavar="FILE",
        help=f"copy the history of this task file, relative to the working directory, instead of recording a draft; "
        f"the {tasks.UPDATES_HEADING} section of the task must be empty",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="the day the update is about (default: today); not after today, not before the task was created; "
        "not with --from",
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
    ref, draft, usage = positionals(args)
    if folder is None and ref is None:
        usage.append(
            "no harness found and no ref given: outside a harness, name the task by its ref, "
            "as in gemba record <ref> update.md"
        )
    if len(usage) == 1:
        return fail(usage[0])
    if usage:
        return fail("record not done:\n" + "\n".join(f"- {problem}" for problem in usage))
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
        assert ref is not None, "a record with no harness and no ref was refused"
        try:
            task = tasks.find_by_ref(root, gemba_config.workstreams, ref)
        except tasks.TaskError as exc:
            errors.append(str(exc))
        else:
            if task is None:
                errors.append(f"no task has ref '{ref}' under {tasks.TASKS_DIR}/, archives included")
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
        if ref is not None and (problem := harness.ref_problem(ref, identity)):
            errors.append(problem)
    text = None if task is None else platform.decode((root / task.path).read_bytes())

    today = datetime.date.today()
    if args.source is not None:
        return copy(root, task, text, errors, args.source, today)
    assert draft is not None, "positionals refuses a record with neither a draft nor --from"
    day = today if args.date is None else values.iso_date(args.date)
    if day is None:
        errors.append(f"invalid date '{args.date}': use YYYY-MM-DD")
    # Without a task there is no creation date to compare with, only today.
    elif problem := tasks.date_problem(day, task.date if task is not None else datetime.date.min, today):
        errors.append(problem)
    bullets, draft_errors = tasks.read_draft(base, draft, place)
    errors.extend(f"{draft} {problem}" for problem in draft_errors)
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
        (base / draft).unlink()
    except OSError as exc:
        return fail(
            f"{task.path} is recorded but the draft {draft} could not be deleted: {exc.strerror}; "
            "delete it by hand and do not record it again, which would write its bullets twice"
        )
    print(task.path)
    print_updated_at(previous, updated_at)
    return 0


def positionals(args: argparse.Namespace) -> tuple[str | None, str | None, list[str]]:
    """The ref and the draft the positionals name, and every usage problem of the call.

    Argparse fills `ref` first, so a lone positional is the draft without `--from` and
    the ref with it.
    """
    given = [value for value in (args.ref, args.file) if value is not None]
    problems = []
    if args.source is None:
        if not given:
            problems.append(
                "a draft or --from is needed: gemba record [<ref>] update.md, "
                "or gemba record [<ref>] --from <task file>"
            )
        if len(given) == 1:
            return None, given[0], problems
        return args.ref, args.file, problems
    if len(given) == 2:
        problems.append("--from takes no draft: it copies the history of a task file, a draft records one day")
    if args.date is not None:
        problems.append("--date does not apply to --from: the dates are those of the history")
    return args.ref, None, problems


def copy(
    root: Path, task: tasks.Task | None, text: str | None, errors: list[str], source: str, today: datetime.date
) -> int:
    """Copy the history of the task file `source`, relative to the working directory, into `task`, after the
    problems of the task found so far, `errors`."""
    source_text, source_errors = tasks.read_source(Path(source))
    errors.extend(f"{source} {problem}" for problem in source_errors)
    history = None
    if source_text is not None:
        history, history_errors = tasks.history(source_text)
        errors.extend(f"{source} {problem}" for problem in history_errors)
    if history is not None:
        # Without a task there is no creation date to compare with, only today.
        created = task.date if task is not None else datetime.date.min
        errors.extend(f"{source} {problem}" for problem in tasks.history_problems(history, created, today))
    if task is not None and text is not None:
        _frontmatter, body = tasks.split(text)
        if problem := tasks.history_target_problem(body):
            errors.append(f"{task.path} {problem}")
    if errors:
        return fail("record not done:\n" + "\n".join(f"- {error}" for error in errors))
    assert task is not None and text is not None and history is not None, "every failed check appended an error"

    copied, previous, updated_at = tasks.copy_history(text, task.date, today, history)
    (root / task.path).write_bytes(copied.encode("utf-8"))
    print(task.path)
    first, last = history.dates[0].isoformat(), history.dates[-1].isoformat()
    print(
        f"copied: 1 day, {first}"
        if len(history.dates) == 1
        else f"copied: {len(history.dates)} days, {first} to {last}"
    )
    print_updated_at(previous, updated_at)
    return 0


def print_updated_at(previous: datetime.date, updated_at: datetime.date) -> None:
    if updated_at == previous:
        print(f"updated_at: {previous.isoformat()} (unchanged)")
    else:
        print(f"updated_at: {previous.isoformat()} -> {updated_at.isoformat()}")


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
