"""Harness rules: the layout of a run, its harness config, the guide, the notes, the commit messages and removal."""

import datetime
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml

from gemba import platform, tasks, worktree

HARNESSES_DIR = "harnesses"
NOTES_DIR = "notes"
ASSETS_DIR = "assets"
WORKTREES_DIR = worktree.WORKTREES_DIR
CONFIG_FILENAME = "harness.yaml"
TASK_LINK = "task.md"
GITIGNORE = ".gitignore"
GITIGNORE_TEXT = f"{WORKTREES_DIR}/\n"
BRANCH = "main"
OBEYA_HEADING = "## Your obeya"
WORKSTREAM_HEADING = "## Your workstream"
# The section of the guide texts of the personal config, which the person whose agent reads the guide wrote.
USER_HEADING = "## Your user"

# Levels between the obeya root and a harness root: harnesses/<workstream>/<stem>.
DEPTH = 3

# The last line `remove` prints in each of its outcomes.
NOT_REMOVED = "not removed: pass --yes to delete the harness"
REMOVED = "removed"
REMOVAL_REFUSED = "harness not removed:"

FILED_NAME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$")
NOTE_KEYS = ("type", "date", "time", "approved", "assets", "resolved_at")

Gate = Literal["always", "optional", "never"]


class HarnessError(Exception):
    """The command cannot act on a harness; nothing may be written."""


@dataclass(frozen=True)
class NoteType:
    """What a note of this type answers, and whether it waits for the user's approval."""

    definition: str
    gate: Gate


# The built-in note types, in the order the guide and the help list them.
NOTE_TYPES = {
    "finding": NoteType("what is true and the evidence for it", "never"),
    "blocker": NoteType("why the run cannot continue, what was tried, what is needed", "never"),
    "decision": NoteType("the options, their trade-offs and the recommendation or the choice", "optional"),
    "summary": NoteType("where the run stands at a milestone and what remains", "never"),
    "external-action": NoteType("something to be done outside the harness, word for word", "always"),
}


@dataclass(frozen=True)
class NoteFrontmatter:
    """The frontmatter of a filed note, as gemba writes it."""

    type: str
    date: datetime.date
    time: str
    approved: bool | None = None
    assets: tuple[str, ...] = ()
    resolved_at: str | None = None


@dataclass(frozen=True)
class HarnessConfig:
    """The identity of a run, written once by launch."""

    task: str  # task file path relative to the obeya root, POSIX separators
    ref: str
    workstream: str
    agent_providers: tuple[str, ...]
    launched_at: datetime.date
    gemba_version: str


class _Quoted(str):
    """A string always written between double quotes, so that YAML never reads it as another type."""


class _Dumper(tasks.FrontmatterDumper):
    """The task frontmatter style, plus double quotes for `_Quoted` strings."""


_Dumper.add_representer(
    _Quoted, lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style='"')
)


def render_config(config: HarnessConfig) -> str:
    """`harness.yaml`: one key per line in fixed order."""
    return tasks.dump_frontmatter(
        {
            "task": config.task,
            "ref": config.ref,
            "workstream": config.workstream,
            "agent_providers": list(config.agent_providers),
            "launched_at": config.launched_at,
            "gemba_version": _Quoted(config.gemba_version),
        },
        _Dumper,
    )


def read_config(harness_root: Path, known_providers: Sequence[str]) -> HarnessConfig:
    """The harness config at `harness_root`, refusing a file that launch would not have written."""
    path = harness_root / CONFIG_FILENAME
    where = f"invalid harness config {path}"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HarnessError(f"{where}: {exc.strerror}") from None
    except (yaml.YAMLError, ValueError) as exc:
        raise HarnessError(f"{where}: malformed YAML: {exc}") from None
    if not isinstance(data, dict):
        raise HarnessError(f"{where}: the file must be a map")
    for key in ("task", "ref", "workstream", "gemba_version"):
        if not isinstance(data.get(key), str) or not data[key]:
            raise HarnessError(f"{where}: {key} must be a non-empty string")
    providers = data.get("agent_providers")
    if not isinstance(providers, list) or not providers or not all(item in known_providers for item in providers):
        raise HarnessError(
            f"{where}: agent_providers must be a non-empty list of known providers ({', '.join(known_providers)})"
        )
    launched_at = data.get("launched_at")
    if not isinstance(launched_at, datetime.date) or isinstance(launched_at, datetime.datetime):
        raise HarnessError(f"{where}: launched_at must be an ISO date (YYYY-MM-DD)")
    return HarnessConfig(
        task=data["task"],
        ref=data["ref"],
        workstream=data["workstream"],
        agent_providers=tuple(providers),
        launched_at=launched_at,
        gemba_version=data["gemba_version"],
    )


def ref_problem(given: str, harness_config: HarnessConfig) -> str | None:
    """Why `given` cannot name the task recorded inside the harness of `harness_config`, or None when it is the ref of
    that task."""
    if given == harness_config.ref:
        return None
    return (
        f"{given} is not the task of this harness, {harness_config.ref}: "
        f"record {given} from the obeya or from its own harness"
    )


@dataclass(frozen=True)
class Manifest:
    """What a run holds, shown before its harness is removed."""

    path: str  # harness root relative to the obeya root, POSIX separators
    task: str
    launched_at: datetime.date
    notes: int
    assets: int
    commits: int
    worktrees: int
    uncommitted: tuple[str, ...] | None  # None when the state of the harness repository could not be read


def render_manifest(manifest: Manifest) -> str:
    """The lines of the manifest: the harness path, one `key: value` line per count, then each uncommitted path."""
    uncommitted = manifest.uncommitted
    return "\n".join(
        [
            manifest.path,
            f"task: {manifest.task}",
            f"launched_at: {manifest.launched_at.isoformat()}",
            f"{NOTES_DIR}: {manifest.notes}",
            f"{ASSETS_DIR}: {manifest.assets}",
            f"commits: {manifest.commits}",
            f"{WORKTREES_DIR}: {manifest.worktrees}",
            f"uncommitted: {'unknown' if uncommitted is None else len(uncommitted)}",
            *(f"- {path}" for path in uncommitted or ()),
        ]
    )


def uncommitted_paths(status_lines: Sequence[str]) -> tuple[str, ...]:
    """The path of every line of `git status --porcelain`, in the order git reports them."""
    return tuple(line[3:] for line in status_lines if line.strip())


def removal_problems(
    working_directory: Path,
    harness_root: Path,
    status_lines: Sequence[str] | None,
    worktree_states: Sequence[worktree.State] = (),
    orphans: Sequence[tuple[str, str, int]] = (),
    force: bool = False,
) -> list[str]:
    """Every reason the harness at `harness_root` cannot be deleted now; both paths are resolved.

    `status_lines` are the lines of `git status --porcelain` in the harness, or None when
    the state of its repository could not be read. An uncommitted path never refuses:
    nothing in the harness repository outlives the run, and the manifest lists it.
    `worktree_states` are the folders under `worktrees/` and `orphans` the branches of
    the run left without a worktree, as (repository, branch, unpushed commits). With
    `force` neither refuses; the working directory and an unreadable harness repository
    still do.
    """
    problems = []
    if working_directory.is_relative_to(harness_root):
        problems.append(
            "the working directory is inside the harness: run the command from outside it, such as the obeya root"
        )
    if status_lines is None:
        problems.append("the state of the harness repository could not be read with git status")
    if force:
        return problems
    for state in worktree_states:
        problems.extend(worktree.pending_problems(state))
    for repo, branch, unpushed in orphans:
        if problem := worktree.orphan_problem(repo, branch, unpushed):
            problems.append(problem)
    return problems


def harness_path(root: Path, workstream: str, stem: str) -> Path:
    """Where the harness of the task file `<stem>.md` of `workstream` lives under the obeya root."""
    return root / HARNESSES_DIR / workstream / stem


def task_link_target(task: str) -> str:
    """The relative target of `task.md` for the task file at `task`, relative to the obeya root."""
    return PurePosixPath(*[".."] * DEPTH, task).as_posix()


def task_link_content(task: str) -> str:
    """The content of `task.md` where the system creates no links: the same relative path, on one line."""
    return f"{task_link_target(task)}\n"


def find_root(start: Path | str) -> Path:
    """The nearest folder at or above `start` that holds a harness config."""
    start = Path(start).resolve()
    for folder in (start, *start.parents):
        if (folder / CONFIG_FILENAME).is_file():
            return folder
    raise HarnessError(f"no harness found: no {CONFIG_FILENAME} in {start} or any parent folder")


def render_guide(asset_text: str, base_guide: str | None, workstream_guide: str | None, user_guide: str | None) -> str:
    """The guide of a harness: the asset as shipped, then the base text, the workstream's and the personal one, each
    in its section."""
    guide = asset_text
    sections = ((OBEYA_HEADING, base_guide), (WORKSTREAM_HEADING, workstream_guide), (USER_HEADING, user_guide))
    for heading, text in sections:
        if text is not None and text.strip():
            guide = f"{guide.rstrip()}\n\n{heading}\n\n{text.strip()}\n"
    return guide


def approval_problem(note_type: str, approval: bool) -> str | None:
    """Why `--approval` cannot be given for this type, or None when the request is valid."""
    if approval and NOTE_TYPES[note_type].gate == "never":
        return f"type '{note_type}' takes no approval: --approval is for decision notes"
    return None


def is_gated(note_type: str, approval: bool) -> bool:
    """Whether a note of this type, filed with or without `--approval`, waits for the user's approval."""
    gate = NOTE_TYPES[note_type].gate
    return gate == "always" or gate == "optional" and approval


def note_filename(now: datetime.datetime, slug: str) -> str:
    """`YYYY-MM-DD-HHMMSS-<slug>.md`, which sorts in filing order."""
    return f"{now:%Y-%m-%d-%H%M%S}-{slug}.md"


def filed_slug(name: str) -> str | None:
    """The slug of a filed note's file name, or None when the name is not one of a filed note."""
    match = FILED_NAME_PATTERN.match(name)
    return match["slug"] if match else None


def render_note_frontmatter(frontmatter: NoteFrontmatter) -> str:
    """The frontmatter block of a note, delimiter lines included, keys in fixed order."""
    data: dict[str, object] = {
        "type": frontmatter.type,
        "date": frontmatter.date,
        "time": _Quoted(frontmatter.time),
    }
    if frontmatter.approved is not None:
        data["approved"] = frontmatter.approved
    if frontmatter.assets:
        data["assets"] = list(frontmatter.assets)
    if frontmatter.resolved_at is not None:
        data["resolved_at"] = _Quoted(frontmatter.resolved_at)
    delimiter = tasks.FRONTMATTER_DELIMITER
    return f"{delimiter}\n{tasks.dump_frontmatter(data, _Dumper)}{delimiter}\n"


def split_note(text: str) -> tuple[str | None, str]:
    """The frontmatter block of a note, or None without one, and the text after its closing line."""
    lines = text.split("\n")
    if lines[0].rstrip() != tasks.FRONTMATTER_DELIMITER:
        return None, text
    for index in range(1, len(lines)):
        if lines[index].rstrip() == tasks.FRONTMATTER_DELIMITER:
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1 :])
    raise HarnessError(f"the frontmatter is not closed by a {tasks.FRONTMATTER_DELIMITER} line")


def parse_note_frontmatter(block: str) -> NoteFrontmatter:
    """Read a frontmatter block that gemba wrote, refusing anything gemba would not write."""
    try:
        data = yaml.safe_load(block)
    except (yaml.YAMLError, ValueError) as exc:
        raise HarnessError(f"the frontmatter is not valid YAML: {exc}") from None
    if not isinstance(data, dict):
        raise HarnessError("the frontmatter must be a map")
    unknown = [str(key) for key in data if key not in NOTE_KEYS]
    if unknown:
        raise HarnessError(f"the frontmatter holds keys gemba does not write: {', '.join(unknown)}")
    note_type = data.get("type")
    if note_type not in NOTE_TYPES:
        raise HarnessError(f"the frontmatter type {note_type!r} is not a note type ({', '.join(NOTE_TYPES)})")
    date = data.get("date")
    if not isinstance(date, datetime.date) or isinstance(date, datetime.datetime):
        raise HarnessError("the frontmatter date must be an ISO date (YYYY-MM-DD)")
    time = data.get("time")
    if not isinstance(time, str) or not TIME_PATTERN.match(time):
        raise HarnessError('the frontmatter time must be a quoted "HH:MM:SS"')
    approved = data.get("approved")
    if "approved" in data and not isinstance(approved, bool):
        raise HarnessError("the frontmatter approved must be true or false")
    assets = data.get("assets", [])
    if not isinstance(assets, list) or not all(isinstance(asset, str) for asset in assets):
        raise HarnessError("the frontmatter assets must be a list of paths")
    resolved_at = data.get("resolved_at")
    if "resolved_at" in data and not isinstance(resolved_at, str):
        raise HarnessError("the frontmatter resolved_at must be a quoted ISO 8601 date and time")
    return NoteFrontmatter(note_type, date, time, approved, tuple(assets), resolved_at)


def check_draft(path: Path, harness_root: Path) -> list[str]:
    """Every rule the draft at `path` breaks, each phrased for the path as the user gave it."""
    problems = []
    if path.parent.resolve() != (harness_root / NOTES_DIR).resolve():
        problems.append(f"is not directly under {NOTES_DIR}/ of the harness (paths are relative to the harness root)")
    if path.suffix != ".md" or not tasks.is_valid_slug(path.stem):
        problems.append("is not a slug followed by .md (lowercase ASCII letters and digits joined by single hyphens)")
    elif platform.is_reserved_name(path.stem):
        problems.append("is named with a slug reserved on Windows, where it could not be a file name")
    if not path.is_file():
        problems.append("does not exist")
    elif _starts_with_frontmatter(path):
        problems.append("is already filed: it starts with a frontmatter")
    return problems


def check_assets(paths: Sequence[str], harness_root: Path) -> tuple[list[str], list[str]]:
    """The assets as relative paths to write in the frontmatter, and every problem found with them."""
    assets_dir = (harness_root / ASSETS_DIR).resolve()
    relative = []
    problems = []
    for given in paths:
        path = (harness_root / given).resolve()
        if not path.is_relative_to(assets_dir) or path == assets_dir:
            problems.append(f"asset {given} is not under {ASSETS_DIR}/ of the harness")
        elif not path.is_file():
            problems.append(f"asset {given} does not exist")
        else:
            relative.append(path.relative_to(harness_root.resolve()).as_posix())
    return relative, problems


def check_filed(path: Path, harness_root: Path) -> list[str]:
    """Every reason the file at `path` is not a filed note of the harness."""
    problems = []
    if path.parent.resolve() != (harness_root / NOTES_DIR).resolve():
        problems.append(f"is not directly under {NOTES_DIR}/ of the harness (paths are relative to the harness root)")
    if filed_slug(path.name) is None:
        problems.append("is not named as a filed note (YYYY-MM-DD-HHMMSS-<slug>.md)")
    if not path.is_file():
        problems.append("does not exist")
    elif not _starts_with_frontmatter(path):
        problems.append("is not filed: it has no frontmatter")
    return problems


def check_resolvable(frontmatter: NoteFrontmatter) -> str | None:
    """Why a filed note cannot be resolved, or None when it is approved and not resolved yet."""
    if frontmatter.approved is None:
        return "is not gated: it has no approved key, so there is nothing to resolve"
    if frontmatter.resolved_at is not None:
        return f"is already resolved, at {frontmatter.resolved_at}"
    if frontmatter.approved is not True:
        return "is not approved: only the user sets approved: true, by editing the note"
    return None


def _starts_with_frontmatter(path: Path) -> bool:
    with path.open(encoding="utf-8", errors="replace") as handle:
        return handle.readline().rstrip() == tasks.FRONTMATTER_DELIMITER


IDENTITY_HINT = "set your git identity with git config --global user.name and user.email"
LONG_PATH_HINT = "enable paths longer than Windows allows by default with git config --global core.longpaths true"
HELD_CAUSE = "an IDE window or a terminal open on it is the likely cause"
# What git says when it cannot delete a path another program holds open, on Windows above all.
HELD_MESSAGES = ("permission denied", "failed to delete", "directory not empty", "unable to unlink", "resource busy")


def git_hints(problem: str) -> list[str]:
    """What to do about a git failure, read from git's message: none when the message names nothing known.

    A missing identity and a path longer than Windows allows are the two failures a person fixes with one
    git config, so the hint names it; a path git could not delete gets the cause a removal names; every
    other message is relayed as it is.
    """
    hints = []
    lowered = problem.lower()
    if "user.email" in lowered or "identity" in lowered:
        hints.append(IDENTITY_HINT)
    if "filename too long" in lowered:
        hints.append(LONG_PATH_HINT)
    if is_held(problem):
        hints.append(HELD_CAUSE)
    return hints


def is_held(problem: str) -> bool:
    """Whether git's message says a path could not be deleted because another program holds it."""
    lowered = problem.lower()
    return any(message in lowered for message in HELD_MESSAGES)


def not_removed_completely(path: str, left: str, again: str) -> str:
    """What `harness remove` says when the system kept part of the harness at `path`: `left` names what, then
    the likely cause and the command, `again`, that finishes the removal."""
    return f"{path} was not removed completely: {left}; {HELD_CAUSE}; run {again} again to finish it"


def not_removed(path: str, left: str, again: str) -> str:
    """What a worktree removal says when git could not delete the worktree at `path`, worded like a harness."""
    return f"{path} was not removed: {left}; {HELD_CAUSE}; run {again} again to finish it"


def launch_message(ref: str) -> str:
    return f"launch {ref}"


def note_message(note_type: str, slug: str) -> str:
    return f"note {note_type} {slug}"


def resolve_message(slug: str) -> str:
    return f"resolve {slug}"
