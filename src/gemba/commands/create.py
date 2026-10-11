"""`gemba create`: validate a creation request, allocate the ref and write the task file."""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from gemba import config, metadata, tasks, values

CREATION_STATUSES = ("open", "in-progress", "blocked")


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "create",
        help="create a task file",
        description="Validate the request against gemba.yaml, allocate the ref and write the task file.",
    )
    parser.add_argument("--workstream", required=True, help="workstream identifier from gemba.yaml")
    parser.add_argument("--slug", required=True, help="lowercase ASCII words joined by single hyphens")
    parser.add_argument("--date", help="creation date as YYYY-MM-DD (default: today)")
    parser.add_argument("--status", default="open", help="open (default), in-progress or blocked")
    parser.add_argument("--description", help="short description written at the top of the body")
    parser.add_argument(
        "--set",
        dest="assignments",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="metadata value, converted by the declared type of its field (null for none); "
        "repeat a key of a text field to build a list",
    )
    parser.add_argument("--root", type=Path, help="tasks repo root (default: walk up to the nearest gemba.yaml)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail(str(exc))

    errors = []
    workstream = gemba_config.workstreams.get(args.workstream)
    if workstream is None:
        errors.append(
            f"unknown workstream '{args.workstream}' (valid workstreams: {', '.join(gemba_config.workstreams)})"
        )
    if not tasks.is_valid_slug(args.slug):
        errors.append(f"invalid slug '{args.slug}': use lowercase ASCII letters and digits joined by single hyphens")
    if args.status == "done":
        errors.append("status 'done' is not allowed at creation (allowed: open, in-progress, blocked)")
    elif args.status not in CREATION_STATUSES:
        errors.append(f"invalid status '{args.status}' (allowed: open, in-progress, blocked)")
    created, date_error = parse_date(args.date)
    if date_error:
        errors.append(date_error)
    assignments, assignment_errors = metadata.parse_assignments(args.assignments, allow_add=False)
    errors.extend(assignment_errors)

    task_metadata: dict[str, object] = {}
    if workstream is not None:
        schema = gemba_config.effective_schema(workstream.id)
        assigned = metadata.assign(schema, {}, assignments, f"'{workstream.id}'")
        errors.extend(assigned.problems)
        task_metadata = assigned.values

    if errors:
        return fail("task not created:\n" + "\n".join(f"- {error}" for error in errors))
    assert workstream is not None and created is not None, "every failed check above appended an error"

    ref = tasks.next_ref(gemba_config.root, workstream.prefix)
    folder = gemba_config.root / tasks.TASKS_DIR / workstream.id
    target = folder / tasks.filename(created, ref, args.slug)
    relative = target.relative_to(gemba_config.root).as_posix()
    if target.exists():
        return fail(f"task not created: {relative} already exists")

    for path in (folder, folder / tasks.ARCHIVE_DIR):
        path.mkdir(parents=True, exist_ok=True)
        (path / tasks.GITKEEP).touch(exist_ok=True)
    content = tasks.render(args.status, ref, created, task_metadata, args.description)
    with target.open("x", encoding="utf-8") as handle:
        handle.write(content)

    print(relative)
    print(ref)
    return 0


def parse_date(text: str | None) -> tuple[datetime.date | None, str | None]:
    if text is None:
        return datetime.date.today(), None
    created = values.iso_date(text)
    if created is None:
        return None, f"invalid date '{text}': use YYYY-MM-DD"
    return created, None


def fail(message: str) -> int:
    print(f"gemba create: {message}", file=sys.stderr)
    return 1
