"""Task file rules: slug, filename, ref allocation, frontmatter and body, written and read, the draft of an
update, and the history copied from another task file."""

import datetime
import re
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Literal

import yaml

from gemba import metadata, platform, values
from gemba.metadata import Conditions

# Where a record is made: inside the harness of the task, or from the obeya.
Place = Literal["harness", "obeya"]

TASKS_DIR = "tasks"
ARCHIVE_DIR = "archive"
GITKEEP = ".gitkeep"

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# A ref is `<PREFIX>-<N>`, or `<INITIALS>-<PREFIX>-<N>` in an obeya with a team; both are read in any obeya, since
# the source of a copied history may come from an obeya of the other kind. The slug is lowercase, so the ref ends
# where it starts.
FILENAME_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})-(?P<ref>(?:[A-Z]+-)?[A-Z]+-[1-9][0-9]*)-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
STATUSES = ("open", "in-progress", "blocked", "done")
DONE = "done"
# The keys of the frontmatter in the order gemba writes them; done_at only while the task is done.
FRONTMATTER_KEYS = ("status", "ref", "updated_at", "done_at", "metadata")
UPDATES_HEADING = "## Updates"
SECTION_PREFIX = "## "
# A heading under `## Updates`; its text must be the ISO date of the subsection.
SUBSECTION_HEADING = re.compile(r"^### (?P<text>.*?)\s*$")
# What a scan reports for a stray entry, a folder then anything else: directly under tasks/ or under a member's
# folder, where a workstream is expected, and directly under tasks/ in an obeya with a team, where a member is.
STRAY_WORKSTREAM = (
    "folder is not a workstream of the config; its files are not listed",
    "entry is not a workstream folder of the config",
)
STRAY_MEMBER = (
    "folder is not a member of the team; its files are not listed",
    "entry is not a member folder of the team",
)
BULLET_PREFIX = "- "
CONTINUATION_PREFIX = "  "
FRONTMATTER_DELIMITER = "---"


class TaskError(Exception):
    """A file is not a valid task; the message names the failing rule."""


@dataclass(frozen=True)
class Task:
    """A task read from disk, with the fields of its listing record in record order.

    `owner` is the member whose folder holds the task in an obeya with a team, else None.
    """

    path: str
    owner: str | None
    workstream: str
    archived: bool
    ref: str
    date: datetime.date
    title: str
    status: str
    updated_at: datetime.date
    done_at: datetime.date | None
    metadata: dict[str, object]
    description: str | None


@dataclass(frozen=True)
class Filters:
    """Listing filters: values of one filter are alternatives, different filters are conditions.

    An empty collection or None leaves that filter out. Date ranges are inclusive.
    `metadata` holds the metadata conditions, and `schemas` the keys of the effective
    schema of each workstream, which tell a key the task lacks from one it may not hold.
    """

    statuses: Collection[str] = ()
    ref: str | None = None
    created_from: datetime.date | None = None
    created_to: datetime.date | None = None
    updated_from: datetime.date | None = None
    updated_to: datetime.date | None = None
    done_from: datetime.date | None = None
    done_to: datetime.date | None = None
    metadata: Conditions = field(default_factory=Conditions)
    schemas: Mapping[str, Collection[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Transition:
    """What a status transition did to a task file, so that a command reports it without reading the file again."""

    old_status: str
    new_status: str
    old_updated_at: datetime.date
    new_updated_at: datetime.date
    done_at: datetime.date | None = None  # the date written when the task reached done
    done_at_removed: bool = False  # whether the task left done and its done_at was dropped

    @property
    def changed(self) -> bool:
        return self.new_status != self.old_status


@dataclass(frozen=True)
class Problem:
    """Something found while scanning that is not a readable task, and why."""

    path: str
    problem: str


@dataclass(frozen=True)
class History:
    """The dated history of a task file: the dates of its subsections, in order, and the lines of its updates section
    from the first `### ` heading on, without the blank lines at their end."""

    dates: tuple[datetime.date, ...]
    lines: tuple[str, ...]


def is_valid_slug(slug: str) -> bool:
    return bool(SLUG_PATTERN.match(slug))


def filename(created: datetime.date, ref: str, slug: str) -> str:
    return f"{created.isoformat()}-{ref}-{slug}.md"


def next_ref(root: Path, prefix: str, initials: str | None = None) -> str:
    """Allocate `<prefix>-<N>`, or `<initials>-<prefix>-<N>` when `initials` are given, from the highest N used with
    that start anywhere under tasks/, archives included.

    A ref with initials never matches the start of a bare prefix, nor one member's
    initials another's, so each member and prefix has a counter of its own.
    """
    start = prefix if initials is None else f"{initials}-{prefix}"
    pattern = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(start)}-(\d+)-")
    highest = 0
    tasks_dir = root / TASKS_DIR
    if tasks_dir.is_dir():
        for path in tasks_dir.rglob("*"):
            match = pattern.match(path.name)
            if match and path.is_file():
                highest = max(highest, int(match.group(1)))
    return f"{start}-{highest + 1}"


class FrontmatterDumper(yaml.SafeDumper):
    """Block style for maps, flow style for lists of scalars: `project: [checkout, landing]`.

    A value written under two keys, such as one date for `updated_at` and `done_at`, is
    written twice and never as a YAML anchor and alias.
    """

    def ignore_aliases(self, data: object) -> bool:
        return True


FrontmatterDumper.add_representer(
    list, lambda dumper, data: dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)
)


def dump_frontmatter(data: Mapping[str, object], dumper: type[FrontmatterDumper] = FrontmatterDumper) -> str:
    """The YAML lines of a frontmatter map, keys in the order given."""
    return yaml.dump(
        data,
        Dumper=dumper,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=float("inf"),
    )


def render(
    status: str,
    ref: str,
    updated_at: datetime.date,
    metadata: dict[str, object],
    description: str | None = None,
) -> str:
    """Full task file content: frontmatter in fixed key order, then the body."""
    frontmatter = dump_frontmatter({"status": status, "ref": ref, "updated_at": updated_at, "metadata": metadata})
    body = f"{UPDATES_HEADING}\n"
    if description and description.strip():
        body = f"{description.strip()}\n\n{body}"
    return f"---\n{frontmatter}---\n\n{body}"


def scan(
    root: Path,
    workstream_ids: Iterable[str],
    include_archived: bool,
    configured: Collection[str] | None = None,
    owners: Sequence[str] | None = None,
) -> tuple[list[Task], list[Problem]]:
    """Read the `.md` files of the given workstream folders, archives only on request.

    With `owners`, the folders of an obeya with a team: the workstream folders of each
    of those members, `tasks/<owner>/<workstream>/`, each task with its owner. Tasks come
    ordered by date, workstream and filename; problems by path. When `configured` holds
    the workstream ids of the config, every other non-hidden entry under tasks/, or with
    `owners` every entry under tasks/ that is not one of them and every entry under
    their folders that is not configured, is a problem, so that tasks never disappear
    silently.
    """
    found: list[Task] = []
    problems: list[Problem] = []
    tasks_dir = root / TASKS_DIR
    holders: list[tuple[Path, str | None]] = (
        [(tasks_dir, None)] if owners is None else [(tasks_dir / owner, owner) for owner in owners]
    )
    workstreams = list(workstream_ids)
    for holder, owner in holders:
        for workstream in workstreams:
            folders = [(holder / workstream, False)]
            if include_archived:
                folders.append((holder / workstream / ARCHIVE_DIR, True))
            for folder, archived in folders:
                for path in _task_files(folder):
                    try:
                        found.append(read(path, root, workstream, archived, owner))
                    except TaskError as exc:
                        problems.append(Problem(path.relative_to(root).as_posix(), str(exc)))
    if configured is not None:
        if owners is not None:
            problems.extend(_strays(root, tasks_dir, owners, *STRAY_MEMBER))
        for holder, _owner in holders:
            problems.extend(_strays(root, holder, configured, *STRAY_WORKSTREAM))
    found.sort(key=lambda task: (task.date, task.workstream, PurePosixPath(task.path).name, task.path))
    problems.sort(key=lambda problem: problem.path)
    return found, problems


def _strays(root: Path, folder: Path, expected: Collection[str], for_folder: str, for_entry: str) -> list[Problem]:
    """A problem for every non-hidden entry directly under `folder` whose name is not in `expected`: `for_folder`
    for a folder, `for_entry` for anything else."""
    if not folder.is_dir():
        return []
    return [
        Problem(entry.relative_to(root).as_posix(), for_folder if entry.is_dir() else for_entry)
        for entry in folder.iterdir()
        if not entry.name.startswith(".") and entry.name not in expected
    ]


def find_by_ref(
    root: Path, workstream_ids: Iterable[str], ref: str, owners: Sequence[str] | None = None
) -> Task | None:
    """The readable task whose ref is `ref`, archives included, or None when no task has it; `owners` are the members
    of the team, whose folders are scanned, in an obeya with a team."""
    found, _problems = scan(root, workstream_ids, include_archived=True, owners=owners)
    holders = [task for task in found if task.ref == ref]
    if len(holders) > 1:
        raise TaskError(f"ref '{ref}' is held by several tasks: {', '.join(task.path for task in holders)}")
    return holders[0] if holders else None


def status_problem(status: object) -> str | None:
    """Why `status` is not one of the four statuses, or None when it is."""
    if status in STATUSES:
        return None
    return f"invalid status {_show(status)} (allowed: {', '.join(STATUSES)})"


def transition(text: str, status: str, day: datetime.date) -> tuple[str, Transition]:
    """The task file content moved to `status` on `day`, and what moved.

    One rule table for every status change after creation: reaching `done` sets
    `done_at` to `day`, any other status holds no `done_at`, and `updated_at` moves to
    `day` only when it is later. The same status returns the text as it was. Otherwise
    the frontmatter is dumped again in the fixed key order and the body is kept byte for
    byte.
    """
    if problem := status_problem(status):
        raise TaskError(problem)
    lines = text.split("\n")
    closing = _closing_line(lines)
    data = _frontmatter_map(lines, closing)
    current = data.get("status")
    if problem := status_problem(current):
        raise TaskError(problem)
    assert isinstance(current, str), "status_problem accepts the four statuses only"
    previous = _date_field(data, "updated_at")
    if previous is None:
        raise TaskError("updated_at is missing")
    if current == status:
        return text, Transition(current, status, previous, previous)

    updated_at = max(previous, day)
    data["status"] = status
    data["updated_at"] = updated_at
    done_at = None
    removed = False
    if status == DONE:
        data["done_at"] = done_at = day
    else:
        removed = data.pop("done_at", None) is not None
    return _rewritten(data, lines, closing), Transition(current, status, previous, updated_at, done_at, removed)


def set_metadata(text: str, values: Mapping[str, object]) -> str:
    """The task file content with `values` as its metadata map.

    Every other frontmatter key keeps its value, `updated_at` included, the frontmatter
    is dumped again in the fixed key order and the body is kept byte for byte.
    """
    lines = text.split("\n")
    closing = _closing_line(lines)
    data = _frontmatter_map(lines, closing)
    data["metadata"] = dict(values)
    return _rewritten(data, lines, closing)


def _rewritten(data: dict[Any, object], lines: list[str], closing: int) -> str:
    """The frontmatter `data` dumped in the fixed key order, then the body after line `closing` as it was."""
    ordered = {key: data[key] for key in FRONTMATTER_KEYS if key in data}
    ordered.update((key, value) for key, value in data.items() if key not in ordered)
    body = "\n".join(lines[closing + 1 :])
    return f"{FRONTMATTER_DELIMITER}\n{dump_frontmatter(ordered)}{FRONTMATTER_DELIMITER}\n{body}"


def start(text: str, today: datetime.date) -> tuple[str, Transition]:
    """The task file content with work started, and what moved.

    An `open` task moves to `in-progress` through `transition`; a task with any other
    status is returned as it was, with a transition that changed nothing.
    """
    lines = text.split("\n")
    current = _frontmatter_map(lines, _closing_line(lines)).get("status")
    return transition(text, "in-progress" if current == "open" else str(current), today)


def archive_destination(task: Task) -> PurePosixPath:
    """Where `gemba archive` moves the task file: the same name under `archive/` of the folder that holds it, the
    workstream folder of the obeya or of its owner."""
    path = PurePosixPath(task.path)
    return path.parent / ARCHIVE_DIR / path.name


def owner_of(path: str) -> str:
    """The member whose folder holds the task at `path`, relative to the obeya root, in an obeya with a team."""
    return PurePosixPath(path).parts[1]


def archive_problem(task: Task, harness_folder: str | None, destination_exists: bool) -> str | None:
    """Why the task cannot be archived, phrased after its ref, or None when it can.

    `harness_folder` is the harness folder of the task, relative to the obeya root,
    when a folder exists there: the `task.md` link inside it would break with the move.
    The status is not checked.
    """
    if task.archived:
        return f"is already archived ({task.path})"
    if harness_folder is not None:
        return f"has a harness at {harness_folder}: remove it first with gemba harness remove {task.ref}"
    if destination_exists:
        return f"cannot move to {archive_destination(task)}: a file is already there"
    return None


def updates_problem(body: str) -> str | None:
    """The first rule of the updates section that `body` breaks, or None when the section is valid."""
    problems = updates_problems(body)
    return problems[0] if problems else None


def updates_problems(body: str) -> list[str]:
    """Every rule of the updates section that `body` breaks, in the order of its lines.

    The body holds one `## Updates` line and no `## ` heading after it, and every `### `
    heading under it is an ISO date, in strictly increasing order. The other lines under
    a date heading are not checked. Scanning stops at a `## ` heading after the section,
    since what follows is not the section.
    """
    lines = body.split("\n")
    found = [index for index, line in enumerate(lines) if line.rstrip() == UPDATES_HEADING]
    if not found:
        return [f"has no '{UPDATES_HEADING}' section"]
    if len(found) > 1:
        return [f"holds '{UPDATES_HEADING}' more than once; the section must appear once, at the end of the body"]
    problems = []
    previous: datetime.date | None = None
    for line in lines[found[0] + 1 :]:
        heading = line.rstrip()
        if heading.startswith(SECTION_PREFIX):
            problems.append(f"has '{heading}' after '{UPDATES_HEADING}', which must be the last section of the body")
            break
        match = SUBSECTION_HEADING.match(line)
        if match is None:
            continue
        day = values.iso_date(match["text"].strip())
        if day is None:
            problems.append(f"has '{heading}' under '{UPDATES_HEADING}', which is not a date heading (### YYYY-MM-DD)")
            continue
        if previous is not None and day <= previous:
            order = "repeats a date" if day == previous else f"follows '### {previous.isoformat()}'"
            problems.append(
                f"has '{heading}' under '{UPDATES_HEADING}', which {order}; the dates must be strictly increasing"
            )
        previous = day
    return problems


def history(text: str) -> tuple[History | None, list[str]]:
    """The history of the text of a task file that `read_source` accepted, or every problem that keeps it from
    being copied.

    The updates section follows its rules, holds at least one date heading, and holds no
    non-blank line before its first `### ` heading, each such line named by its number in
    the file.
    """
    lines = text.split("\n")
    closing = _closing_line(lines)
    body = lines[closing + 1 :]
    problems = updates_problems("\n".join(body))
    found = [index for index, line in enumerate(body) if line.rstrip() == UPDATES_HEADING]
    if len(found) != 1:
        return None, problems
    end = next(
        (index for index in range(found[0] + 1, len(body)) if body[index].rstrip().startswith(SECTION_PREFIX)),
        len(body),
    )
    first: int | None = None
    stray: list[str] = []
    dates: list[datetime.date] = []
    for index in range(found[0] + 1, end):
        match = SUBSECTION_HEADING.match(body[index])
        if match is None:
            if first is None and body[index].strip():
                stray.append(str(closing + index + 2))  # the number of the line in the file, counted from 1
            continue
        if first is None:
            first = index
        if (day := values.iso_date(match["text"].strip())) is not None:
            dates.append(day)
    if stray and first is not None:
        where = f"line {stray[0]}" if len(stray) == 1 else f"lines {', '.join(stray)}"
        problems.insert(
            0,
            f"has text under '{UPDATES_HEADING}' before its first date heading, at {where}: "
            "every line of a history belongs to a date",
        )
    if not dates:
        problems.append(f"has no date heading under '{UPDATES_HEADING}': there is no history to copy")
    if problems:
        return None, problems
    assert first is not None, "a date heading was found"
    return History(tuple(dates), tuple(_trimmed(body[first:end]))), []


def history_problems(history: History, created: datetime.date, today: datetime.date) -> list[str]:
    """Why the dates of `history` cannot date the changes of a task created on `created`, one problem per heading."""
    return [
        f"has '### {day.isoformat()}': {problem}"
        for day in history.dates
        if (problem := date_problem(day, created, today))
    ]


def parse_bullets(text: str) -> tuple[list[str], list[str]]:
    """The lines of a drafted update, without the blank lines around them, and every rule the draft breaks.

    Every non-blank line is a `- ` bullet or, continuing the previous bullet, starts with
    two spaces, and at least one bullet is present. The lines come as written, line
    endings aside, and only when the draft breaks no rule.
    """
    lines = [line.removesuffix("\r") for line in text.split("\n")]
    filled = [index for index, line in enumerate(lines) if line.strip()]
    stray = []
    bullets = 0
    for index in filled:
        if lines[index].startswith(BULLET_PREFIX):
            bullets += 1
        elif not (bullets and lines[index].startswith(CONTINUATION_PREFIX)):
            stray.append(str(index + 1))
    problems = []
    if not bullets:
        problems.append(f"holds no bullet: write each one on a line starting with '{BULLET_PREFIX}'")
    if stray:
        which = f"line {stray[0]} is" if len(stray) == 1 else f"lines {', '.join(stray)} are"
        problems.append(f"{which} neither a '{BULLET_PREFIX}' bullet nor a continuation indented by two spaces")
    if problems:
        return [], problems
    return lines[filled[0] : filled[-1] + 1], []


def read_draft(root: Path, given: str, place: Place) -> tuple[list[str], list[str]]:
    """The bullet lines of the draft at `given`, relative to `root`, the resolved root of `place`, and every problem
    found with it.

    Inside a harness the draft lies anywhere in it. From the obeya it lies directly
    in the root, so that neither a task file nor the draft of a run is consumed; the
    parent is compared with `samefile`, so a spelling of the root that differs only in
    case is still the root.
    """
    path = (root / given).resolve()
    if place == "harness":
        if not path.is_relative_to(root):
            return [], ["is not inside the harness (paths are relative to the harness root)"]
    elif not (path.parent.is_dir() and path.parent.samefile(root)):
        return [], ["is not directly in the obeya root (paths are relative to the obeya root)"]
    if not path.is_file():
        return [], ["is not a file" if path.exists() else "does not exist"]
    try:
        text = platform.decode(path.read_bytes())
    except UnicodeDecodeError:
        return [], ["is not UTF-8 text"]
    return parse_bullets(text)


def date_problem(day: datetime.date, created: datetime.date, today: datetime.date) -> str | None:
    """Why `day` cannot date a change to a task created on `created`, or None when it can."""
    if day > today:
        return f"date {day.isoformat()} is after today, {today.isoformat()}"
    if day < created:
        return f"date {day.isoformat()} is before {created.isoformat()}, the creation date of the task"
    return None


def record(
    text: str, created: datetime.date, today: datetime.date, day: datetime.date, bullets: Sequence[str]
) -> tuple[str, datetime.date, datetime.date]:
    """The task file content with `bullets` recorded under `### <day>`, and `updated_at` before and after.

    The subsection is inserted in date order, or the bullets are appended to the
    subsection of that day when there is one. `updated_at` moves to `day` only when it
    is later, and the frontmatter is dumped again in its own key order; every line of
    the body outside the written subsection is kept as it was.
    """
    if problem := date_problem(day, created, today):
        raise TaskError(problem)
    if not bullets:
        raise TaskError("there is no bullet to record")
    lines = text.split("\n")
    closing = _closing_line(lines)
    data = _load_frontmatter("\n".join(lines[1:closing]))
    if not isinstance(data, dict):
        raise TaskError("frontmatter must be a map")
    body = lines[closing + 1 :]
    if problem := updates_problem("\n".join(body)):
        raise TaskError(problem)
    previous = _date_field(data, "updated_at")
    if previous is None:
        raise TaskError("updated_at is missing")
    updated_at = max(previous, day)
    data["updated_at"] = updated_at
    body = _with_subsection(body, day, list(bullets))
    frontmatter = f"{FRONTMATTER_DELIMITER}\n{dump_frontmatter(data)}{FRONTMATTER_DELIMITER}"
    return "\n".join([frontmatter, *body]), previous, updated_at


def _with_subsection(body: list[str], day: datetime.date, bullets: list[str]) -> list[str]:
    """The lines of a body whose updates section is valid, with `bullets` written under `### <day>`.

    A subsection is separated from its neighbours by one blank line, and the body ends
    with one newline when the written subsection is the last one.
    """
    start = next(index for index, line in enumerate(body) if line.rstrip() == UPDATES_HEADING)
    headings = []
    for index in range(start + 1, len(body)):
        if match := SUBSECTION_HEADING.match(body[index]):
            heading_date = values.iso_date(match["text"].strip())
            assert heading_date is not None, "updates_problem checked every heading"
            headings.append((index, heading_date))

    same = next((index for index, heading_date in headings if heading_date == day), None)
    if same is not None:
        end = next((index for index, _date in headings if index > same), len(body))
        last = max(index for index in range(same, end) if body[index].strip())
        added = bullets if last > same else ["", *bullets]
        rest = body[last + 1 :] if end < len(body) else [""]
        return [*body[: last + 1], *added, *rest]

    subsection = ["", f"### {day.isoformat()}", "", *bullets]
    following = next((index for index, heading_date in headings if heading_date > day), None)
    if following is None:
        return [*_trimmed(body), *subsection, ""]
    return [*_trimmed(body[:following]), *subsection, "", *body[following:]]


def _trimmed(lines: list[str]) -> list[str]:
    """`lines` without the blank lines at their end."""
    end = len(lines)
    while end and not lines[end - 1].strip():
        end -= 1
    return lines[:end]


def history_target_problem(body: str) -> str | None:
    """Why the task whose body is `body` cannot receive a history, or None when its updates section is valid and
    empty, so that a history is never written twice."""
    if problem := updates_problem(body):
        return problem
    lines = body.split("\n")
    start = next(index for index, line in enumerate(lines) if line.rstrip() == UPDATES_HEADING)
    if any(line.strip() for line in lines[start + 1 :]):
        return f"has updates already: --from writes a history only into a task whose '{UPDATES_HEADING}' is empty"
    return None


def copy_history(
    text: str, created: datetime.date, today: datetime.date, history: History
) -> tuple[str, datetime.date, datetime.date]:
    """The task file content with `history` as its updates section, and `updated_at` before and after.

    The lines of the history follow the `## Updates` line and one blank line as they
    are, with none of the rules of a draft, and the file ends with one newline.
    `updated_at` moves to the last date of the history only when it is later, and the
    frontmatter is dumped again in its own key order; every line of the body up to
    `## Updates` is kept as it was.
    """
    if problems := history_problems(history, created, today):
        raise TaskError(problems[0])
    if not history.dates:
        raise TaskError("there is no history to copy")
    lines = text.split("\n")
    closing = _closing_line(lines)
    data = _frontmatter_map(lines, closing)
    body = lines[closing + 1 :]
    if problem := history_target_problem("\n".join(body)):
        raise TaskError(problem)
    previous = _date_field(data, "updated_at")
    if previous is None:
        raise TaskError("updated_at is missing")
    updated_at = max(previous, max(history.dates))
    data["updated_at"] = updated_at
    start = next(index for index, line in enumerate(body) if line.rstrip() == UPDATES_HEADING)
    frontmatter = f"{FRONTMATTER_DELIMITER}\n{dump_frontmatter(data)}{FRONTMATTER_DELIMITER}"
    return "\n".join([frontmatter, *body[: start + 1], "", *history.lines, ""]), previous, updated_at


def matches(task: Task, filters: Filters) -> bool:
    """Whether the task passes every filter; the workstream filter is the scan scope, not a filter."""
    if filters.statuses and task.status not in filters.statuses:
        return False
    if filters.ref is not None and task.ref != filters.ref:
        return False
    if not _within(task.date, filters.created_from, filters.created_to):
        return False
    if not _within(task.updated_at, filters.updated_from, filters.updated_to):
        return False
    if filters.done_from is not None or filters.done_to is not None:
        if task.done_at is None or not _within(task.done_at, filters.done_from, filters.done_to):
            return False
    return filters.metadata.matches(task.metadata, filters.schemas.get(task.workstream, ()))


def _within(day: datetime.date, start: datetime.date | None, end: datetime.date | None) -> bool:
    return (start is None or start <= day) and (end is None or day <= end)


def _task_files(folder: Path) -> list[Path]:
    """The non-hidden `.md` files directly under `folder`; none when it does not exist."""
    if not folder.is_dir():
        return []
    return sorted(
        path for path in folder.iterdir() if path.suffix == ".md" and not path.name.startswith(".") and path.is_file()
    )


def read(path: Path, root: Path, workstream: str, archived: bool, owner: str | None = None) -> Task:
    """Read the task file at `path`, applying every reading rule of the task file format.

    Metadata keys are not checked against the schema: a task written under an earlier
    schema stays readable after the config changes. `owner` is the member whose folder
    holds the file, in an obeya with a team.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise TaskError("the file is not UTF-8 text") from None
    except OSError as exc:
        raise TaskError(f"the file cannot be read: {exc.strerror}") from None
    return _parse(path.name, text, path.relative_to(root).as_posix(), workstream, archived, owner)


def read_source(path: Path) -> tuple[str | None, list[str]]:
    """The text of the task file at `path`, whose history is copied into another task, or every problem found with it.

    The bytes go through `platform.decode()`, so a CRLF or a byte-order mark is no
    problem, and the text must pass the reading rules of the task file format. The
    workstream and the archive folder of the file mean nothing here and are not checked.
    """
    if not path.is_file():
        return None, ["is not a file" if path.exists() else "does not exist"]
    try:
        text = platform.decode(path.read_bytes())
    except UnicodeDecodeError:
        return None, ["is not UTF-8 text"]
    except OSError as exc:
        return None, [f"cannot be read: {exc.strerror}"]
    try:
        _parse(path.name, text, path.name, workstream="", archived=False, owner=None)
    except TaskError as exc:
        return None, [f"is not a valid task: {exc}"]
    return text, []


def _parse(name: str, text: str, path: str, workstream: str, archived: bool, owner: str | None) -> Task:
    """The task named `name` whose content is `text`, by the reading rules of the task file format; `path`,
    `workstream`, `archived` and `owner` only locate it."""
    match = FILENAME_PATTERN.match(name)
    if match is None:
        raise TaskError("filename does not match YYYY-MM-DD-<ref>-<slug>.md")
    created = values.iso_date(match["date"])
    if created is None:
        raise TaskError(f"filename date '{match['date']}' is not a valid date")

    frontmatter, body = split(text)
    data = _load_frontmatter(frontmatter)
    if not isinstance(data, dict):
        raise TaskError("frontmatter must be a map")

    status = data.get("status")
    if status is None:
        raise TaskError(f"status is missing (allowed: {', '.join(STATUSES)})")
    if status not in STATUSES:
        raise TaskError(f"invalid status {_show(status)} (allowed: {', '.join(STATUSES)})")
    ref = data.get("ref")
    if ref is None:
        raise TaskError(f"ref is missing (the filename says '{match['ref']}')")
    if ref != match["ref"]:
        raise TaskError(f"ref {_show(ref)} in the frontmatter does not match '{match['ref']}' in the filename")
    updated_at = _date_field(data, "updated_at")
    if updated_at is None:
        raise TaskError("updated_at is missing")
    done_at = _date_field(data, "done_at")
    metadata = _metadata(data)

    return Task(
        path=path,
        owner=owner,
        workstream=workstream,
        archived=archived,
        ref=ref,
        date=created,
        title=display_title(name, ref),
        status=status,
        updated_at=updated_at,
        done_at=done_at,
        metadata=metadata,
        description=description(body),
    )


def display_title(filename: str, ref: str) -> str:
    """`2026-09-30-SUP-1-login-fails-on-safari.md` with ref `SUP-1` reads `Login fails on safari`."""
    slug = filename.removesuffix(".md")[len("YYYY-MM-DD-") :].removeprefix(f"{ref}-")
    words = slug.replace("-", " ")
    return words[:1].upper() + words[1:]


def description(body: str) -> str | None:
    """The first paragraph of the body, or None when the body starts with the updates heading."""
    paragraph: list[str] = []
    for line in body.split("\n"):
        if line.strip():
            paragraph.append(line.rstrip())
        elif paragraph:
            break
    if not paragraph or paragraph[0].strip() == UPDATES_HEADING:
        return None
    return "\n".join(paragraph).strip()


def split(text: str) -> tuple[str, str]:
    """The frontmatter block and the body that follows its closing line."""
    lines = text.split("\n")
    closing = _closing_line(lines)
    return "\n".join(lines[1:closing]), "\n".join(lines[closing + 1 :])


def _closing_line(lines: list[str]) -> int:
    """Index of the line that closes the frontmatter opened by the first line."""
    if lines[0].rstrip() != FRONTMATTER_DELIMITER:
        raise TaskError(f"no frontmatter: the file does not start with a {FRONTMATTER_DELIMITER} line")
    for index in range(1, len(lines)):
        if lines[index].rstrip() == FRONTMATTER_DELIMITER:
            return index
    raise TaskError(f"frontmatter is not closed by a {FRONTMATTER_DELIMITER} line")


def _frontmatter_map(lines: list[str], closing: int) -> dict[Any, object]:
    """The frontmatter between the first line and `closing`, which must be a map; YAML keys may be of any type."""
    data = _load_frontmatter("\n".join(lines[1:closing]))
    if not isinstance(data, dict):
        raise TaskError("frontmatter must be a map")
    return data


def _load_frontmatter(text: str) -> object:
    try:
        return yaml.safe_load(text)
    except yaml.MarkedYAMLError as exc:
        # The block starts on the second line of the file, after the opening delimiter.
        where = f" (line {exc.problem_mark.line + 2})" if exc.problem_mark else ""
        raise TaskError(f"frontmatter is not valid YAML{where}: {exc.problem or exc.context}") from None
    except (yaml.YAMLError, ValueError) as exc:  # ValueError: an impossible date such as 2026-13-01
        raise TaskError(f"frontmatter is not valid YAML: {exc}") from None


def _date_field(data: dict[object, object], key: str) -> datetime.date | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return value
    if isinstance(value, str) and (parsed := values.iso_date(value)) is not None:
        return parsed
    raise TaskError(f"{key} must be an ISO date (YYYY-MM-DD), not {_show(value)}")


def _metadata(data: dict[object, object]) -> dict[str, object]:
    if "metadata" not in data:
        raise TaskError("metadata is missing (it must be a map, {} when empty)")
    found = data["metadata"]
    if not isinstance(found, dict):
        kind = "a list" if isinstance(found, list) else "null" if found is None else "a scalar"
        raise TaskError(f"metadata must be a map, not {kind}")
    for key, value in found.items():
        if not isinstance(key, str):
            raise TaskError(f"metadata key {_show(key)} must be a string")
        if problem := metadata.shape_problem(value):
            raise TaskError(f"metadata value of '{key}' {problem}")
    return found


def _show(value: object) -> str:
    """A frontmatter value as it reads in YAML, quoted when it is a string."""
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)
