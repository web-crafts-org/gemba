"""Team rules: the members of an obeya shared by a team, who may write a task, and the layout a team requires.

The shared config declares the team and the personal config `me`, the member of the
clone; this module knows neither file, and reads nothing but the names of the folders
directly under tasks/.
"""

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from gemba import tasks

INITIALS_PATTERN = re.compile(r"^[A-Z]+$")
# The keys a member of the team takes.
MEMBER_KEYS = ("initials", "active")
MIGRATE_SKILL = "gemba-migrate"


@dataclass(frozen=True)
class Member:
    """One member of the team: the name of their folder under tasks/, the initials of their refs, and whether they
    are still active; a member who leaves is kept, inactive, so their initials are never reused."""

    id: str
    initials: str
    active: bool = True


def write_problems(
    members: Mapping[str, Member] | None, me: str | None, task: tasks.Task | None, personal_file: str
) -> list[str]:
    """Why the clone whose member is `me` may not write, or may not write `task`, empty in an obeya without a team.

    A write needs an active member, and a task is written only by its owner. `me`, when
    given, is a member of `members`, as the config guarantees; `personal_file` names the
    personal config, where `me` is declared.
    """
    if members is None:
        return []
    if me is None:
        return [
            f"no member declared for this clone: add me to {personal_file}, the personal config "
            f"(members: {', '.join(members)})"
        ]
    problems = []
    if not members[me].active:
        problems.append(f"me is {me}, an inactive member of the team, who writes no task")
    if task is not None and task.owner != me:
        problems.append(f"{task.ref} belongs to {task.owner}: only its owner writes it")
    return problems


def layout_problem(root: Path, workstream_ids: Collection[str]) -> str | None:
    """Why an obeya whose shared config declares a team cannot hold the tasks at `root`, or None when it can.

    A non-hidden folder directly under tasks/ named after a workstream is the layout of
    an obeya without a team, which is never converted in place.
    """
    tasks_dir = root / tasks.TASKS_DIR
    if not tasks_dir.is_dir():
        return None
    folders = sorted(
        PurePosixPath(tasks.TASKS_DIR, entry.name).as_posix()
        for entry in tasks_dir.iterdir()
        if entry.is_dir() and not entry.name.startswith(".") and entry.name in workstream_ids
    )
    if not folders:
        return None
    kind = "the folder" if len(folders) == 1 else "the folders"
    return (
        f"team is declared, but {tasks.TASKS_DIR}/ holds {_listed(folders)}, {kind} of an obeya without a team: "
        f"a team starts in a new obeya, and the {MIGRATE_SKILL} skill brings earlier tasks into it"
    )


def _listed(names: Sequence[str]) -> str:
    """`a`, `a and b`, or `a, b and c`."""
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"
