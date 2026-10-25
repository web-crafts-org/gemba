"""Report rules: the groupings, counts and sums over tasks already selected.

The one module that knows tasks and metadata together: a task is grouped by its own
workstream, status and, in an obeya with a team, owner, and by its metadata values read
by the type of their field.
"""

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from gemba import metadata
from gemba.tasks import STATUSES, Task

# Properties of every task a report may group by; no metadata field may take these names.
BUILT_IN = metadata.RESERVED
# The property only a task of an obeya with a team has.
OWNER = "owner"
# The types a report groups by: a number is summed and a date bounds a selection.
GROUPED = (metadata.TEXT, metadata.BOOLEAN)
SUMMED = (metadata.NUMBER,)


@dataclass(frozen=True)
class Sum:
    """The total of a number field over some tasks, and how many of them had no number to add."""

    total: int | float
    missing: int


@dataclass(frozen=True)
class Group:
    key: dict[str, object]
    tasks: int
    refs: list[str]
    sums: dict[str, Sum]


@dataclass(frozen=True)
class Report:
    """The groups in order, then the total over every task, each task counted once."""

    groups: list[Group]
    tasks: int
    sums: dict[str, Sum]


def grouping_problem(key: str, types: Mapping[str, str], team: Sequence[str] | None = None) -> str | None:
    """Why a report cannot group by `key`, or None when it can; `team` holds the members, None without a team."""
    if key == OWNER and team is None:
        return f"cannot group by '{key}': this obeya declares no team"
    if key in BUILT_IN:
        return None
    if key not in types:
        return f"cannot group by '{key}': it is not {', '.join(BUILT_IN)} or a field the config declares"
    if types[key] not in GROUPED:
        return (
            f"cannot group by '{key}', a {types[key]} field: group by {', '.join(BUILT_IN)}, or a text or boolean field"
        )
    return None


def sum_problem(key: str, types: Mapping[str, str]) -> str | None:
    """Why a report cannot sum `key`, or None when it can."""
    if key not in types:
        return f"cannot sum '{key}': no metadata schema of the config declares it"
    if types[key] not in SUMMED:
        return f"cannot sum '{key}', a {types[key]} field: only a number field is summed"
    return None


def problems(
    by: Sequence[str], sums: Sequence[str], types: Mapping[str, str], team: Sequence[str] | None = None
) -> list[str]:
    """Every grouping and sum a report cannot take, a key given twice to either included; `team` holds the members,
    None without a team."""
    found = []
    for keys, role in ((by, "grouping"), (sums, "sum")):
        for key in dict.fromkeys(keys):
            reason = grouping_problem(key, types, team) if role == "grouping" else sum_problem(key, types)
            if reason:
                found.append(reason)
            if keys.count(key) > 1:
                found.append(f"'{key}' is given more than once as a {role}")
    return found


def aggregate(
    selected: Sequence[Task],
    by: Sequence[str],
    sums: Sequence[str],
    types: Mapping[str, str],
    workstreams: Sequence[str],
    team: Sequence[str] | None = None,
) -> Report:
    """The groups of the selected tasks, in listing order, and the total.

    A task belongs to one group per combination of its grouping values: a null, missing
    or mistyped value groups under null, and a text list under each distinct item, or
    under null when empty. Groups are ordered grouping after grouping: workstreams in
    the order of `workstreams`, owners in the order of the members in `team`, statuses
    in their order, false before true, text by code point and null last.
    """
    members: dict[tuple[object, ...], list[Task]] = {}
    for task in selected:
        for combination in itertools.product(*(_grouping_values(task, key, types) for key in by)):
            members.setdefault(combination, []).append(task)
    order = sorted(
        members,
        key=lambda combination: [
            _rank(key, value, workstreams, team or ()) for key, value in zip(by, combination, strict=True)
        ],
    )
    groups = [
        Group(
            key=dict(zip(by, combination, strict=True)),
            tasks=len(members[combination]),
            refs=[task.ref for task in members[combination]],
            sums=_sums(members[combination], sums),
        )
        for combination in order
    ]
    return Report(groups=groups, tasks=len(selected), sums=_sums(selected, sums))


def _grouping_values(task: Task, key: str, types: Mapping[str, str]) -> list[object]:
    if key == "workstream":
        return [task.workstream]
    if key == "status":
        return [task.status]
    if key == OWNER:
        return [task.owner]
    value = task.metadata.get(key)
    if metadata.value_problem(types[key], value) is not None:
        return [None]
    if isinstance(value, list):
        return list(dict.fromkeys(value)) or [None]
    return [value]


def _rank(key: str, value: object, workstreams: Sequence[str], team: Sequence[str]) -> tuple[int, object]:
    """Where a grouping value sorts: the order of its grouping, null last."""
    if value is None:
        return (1, 0)
    if key == "workstream":
        return (0, workstreams.index(str(value)))
    if key == OWNER:
        return (0, team.index(str(value)))
    if key == "status":
        return (0, STATUSES.index(str(value)))
    if isinstance(value, bool):
        return (0, int(value))
    return (0, str(value))


def _sums(group: Sequence[Task], keys: Sequence[str]) -> dict[str, Sum]:
    sums = {}
    for key in keys:
        total: int | float = 0
        missing = 0
        for task in group:
            value = task.metadata.get(key)
            if value is None or metadata.value_problem(metadata.NUMBER, value) is not None:
                missing += 1
            else:
                total = metadata.add(total, value)
        sums[key] = Sum(total, missing)
    return sums
