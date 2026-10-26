"""Sync rules of an obeya with a team: who owns each path a push or a pull changes, the checks of an outgoing change,
what an incoming one shows, the confirmation of shared files, and every line the hooks and `gemba sync` print.

The adapters read git and hand this module plain data: the paths of a net change, the
commits of a range, the member's own task files as of the commit pushed. It runs
nothing and reads no file, so the hooks and `gemba sync` reach the same verdict.
"""

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

from gemba import config, obeya, tasks
from gemba.harness import HARNESSES_DIR

# What a path is to the member of the clone: their own, another member's, private to each clone, or shared.
Kind = Literal["own", "member", "private", "shared"]
# The order the uncommitted changes are listed in, and how each kind is named there.
KINDS: tuple[Kind, ...] = ("own", "member", "private", "shared")
# The name of the setting that confirms the shared files of a push, given to that one git command.
SHARED_SETTING = "gemba.shared"
REFUSAL_FOOTER = "the gemba-sync skill explains each problem; git push --no-verify skips these checks"
# How a line names a private path.
PRIVATE = "private to each clone"
# The hooks a clone counts as installed: they run `gemba hook`, whoever wrote them.
INSTALLED: tuple[obeya.HookState, ...] = ("current", "earlier", "chained")


@dataclass(frozen=True)
class Owner:
    """What a path is to the member of the clone, and the member whose folder holds it when it is another's."""

    kind: Kind
    member: str | None = None


@dataclass(frozen=True)
class Commit:
    """One commit of a range: its full and short ids, its author's name, its subject and the paths it changes, empty
    for a merge."""

    id: str
    short: str
    author: str
    subject: str
    paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class OwnFile:
    """A path under tasks/<me>/ in the net change, with its text as of the commit pushed, or None when it is deleted
    there or cannot be read, and then `unreadable` says why."""

    path: str
    text: str | None
    unreadable: str | None = None


@dataclass(frozen=True)
class Context:
    """What the checks need of the config: the member of the clone, their initials, every member of the team, active
    or not, and the workstream identifiers."""

    me: str
    initials: str
    members: tuple[str, ...]
    workstreams: tuple[str, ...]


@dataclass(frozen=True)
class Outgoing:
    """The verdict of an outgoing change: the problems no confirmation lifts, and the lines of the shared files, empty
    once confirmed."""

    problems: tuple[str, ...]
    shared: tuple[str, ...]

    def lines(self, tip: str) -> list[str]:
        """What the pre-push hook prints for the pushed commit `tip`, the way to confirm the shared files last."""
        lines = [*self.problems, *self.shared]
        if self.shared:
            lines.append(f"confirm them with {confirm_command(tip)}")
        return lines


@dataclass(frozen=True)
class Incoming:
    """The report of what came in, and whether it lists a path, so that a hook stays silent when it does not."""

    lines: tuple[str, ...]
    listed: bool


def context_of(gemba_config: config.Config) -> Context | None:
    """The context of the checks in the obeya of `gemba_config`, or None without a team or without `me`."""
    if gemba_config.team is None or gemba_config.me is None:
        return None
    return Context(
        me=gemba_config.me,
        initials=gemba_config.team[gemba_config.me].initials,
        members=tuple(gemba_config.team),
        workstreams=tuple(gemba_config.workstreams),
    )


def classify(path: str, me: str, members: Collection[str]) -> Owner:
    """What the POSIX `path`, relative to the obeya root, is to the member `me` among `members`, active or not."""
    parts = PurePosixPath(path).parts
    if path == config.LOCAL_FILENAME or (len(parts) > 1 and parts[0] == HARNESSES_DIR):
        return Owner("private")
    if len(parts) > 2 and parts[0] == tasks.TASKS_DIR:
        if parts[1] == me:
            return Owner("own")
        if parts[1] in members:
            return Owner("member", parts[1])
    return Owner("shared")


def outgoing(
    net: Collection[str],
    commits: Sequence[Commit],
    merges: Sequence[Commit],
    own_files: Sequence[OwnFile],
    own_paths: Collection[str],
    context: Context,
    confirmed: bool,
) -> Outgoing:
    """Every problem of an outgoing change, in the order they are reported, and the lines of its shared files.

    `net` holds the paths of the net change, `commits` the outgoing commits that are not
    merges, oldest first, and `merges` the others; they name the commits behind each path.
    `own_files` holds the files of the net change under tasks/<me>/ as of the commit pushed,
    `own_paths` every path under tasks/<me>/ there, and `confirmed` says that the push is
    confirmed for its commit, which lifts the shared lines only.
    """
    paths = sorted(net)
    kinds = {path: classify(path, context.me, context.members) for path in paths}
    problems: list[str] = []
    for path in paths:
        member = kinds[path].member
        if member is not None:
            problems.append(
                f"{_changes(path, commits, merges)} {path}, in the folder of {member}: only {member} writes it"
            )
    private_by_commit = set()
    for commit in commits:
        for path in sorted(commit.paths):
            if classify(path, context.me, context.members).kind == "private":
                private_by_commit.add(path)
                problems.append(f"{commit.short} changes {path}, {PRIVATE}: it never leaves the clone")
    for path in paths:
        if kinds[path].kind == "private" and path not in private_by_commit:
            problems.append(f"{_changes(path, commits, merges)} {path}, {PRIVATE}: it never leaves the clone")
    for own in sorted(own_files, key=lambda own: own.path):
        if own.path not in net or not own.path.endswith(".md"):
            continue
        if own.unreadable is not None:
            problems.append(f"{own.path} is not a valid task: {own.unreadable}")
        elif own.text is not None:
            problems.extend(_own_file_problems(own.path, own.text, context))
    problems.extend(_duplicate_problems(own_paths, net))
    shared = [] if confirmed else [path for path in paths if kinds[path].kind == "shared"]
    return Outgoing(
        problems=tuple(problems),
        shared=tuple(f"{_changes(path, commits, merges)} the shared file {path}" for path in shared),
    )


def _own_file_problems(path: str, text: str, context: Context) -> list[str]:
    """Why a task file of the member, as of the commit pushed, may not go out: one problem, or none."""
    parts = PurePosixPath(path).parts
    in_folder = len(parts) in (4, 5) and parts[2] in context.workstreams
    archived = len(parts) == 5
    if not in_folder or (archived and parts[3] != tasks.ARCHIVE_DIR):
        return [f"{path} is not in a workstream folder of {tasks.TASKS_DIR}/{context.me}/"]
    try:
        task = tasks.parse(parts[-1], text, path, workstream=parts[2], archived=archived, owner=context.me)
    except tasks.TaskError as exc:
        return [f"{path} is not a valid task: {exc}"]
    if task.ref.split("-")[0] != context.initials or task.ref.count("-") != 2:
        return [f"{path} holds {task.ref}, without the initials of {context.me} ({context.initials})"]
    return []


def _duplicate_problems(own_paths: Collection[str], net: Collection[str]) -> list[str]:
    """A problem for every ref two files of the member hold as of the commit pushed, when the push changes one."""
    holders: dict[str, list[str]] = {}
    for path in sorted(own_paths):
        match = tasks.FILENAME_PATTERN.match(PurePosixPath(path).name)
        if match is not None:
            holders.setdefault(match["ref"], []).append(path)
    return [
        f"{ref} is held by {_listed(paths)}: a ref is never held twice"
        for ref, paths in holders.items()
        if len(paths) > 1 and any(path in net for path in paths)
    ]


def incoming(
    net: Collection[str],
    commits: Sequence[Commit],
    merges: Sequence[Commit],
    patch: str,
    context: Context,
    pulled: bool,
) -> Incoming:
    """The report of what a pull brings, `pulled` after a pull and before it otherwise.

    `net` holds the paths the pull changes in the end, `commits` its commits that are not
    merges and `merges` the others, and `patch` the patch of the member's own paths of the
    net change, from the first base to the tip, shown whole.
    """
    paths = sorted(net)
    kinds = {path: classify(path, context.me, context.members).kind for path in paths}
    own = [path for path in paths if kinds[path] == "own"]
    shared = [path for path in paths if kinds[path] == "shared"]
    private = [path for path in paths if kinds[path] == "private"]
    lines: list[str] = []
    if own:
        lines.append("- your tasks:")
        lines.extend(f"  {path}, by {_who(path, commits, merges, authors=True)}" for path in own)
        if patch.strip():
            lines.extend(f"    {line}" for line in patch.rstrip("\n").split("\n"))
    if shared:
        lines.append("- shared files:")
        lines.extend(f"  {path}, by {_who(path, commits, merges, authors=True)}" for path in shared)
    overwritten = "the pull wrote it over yours" if pulled else "a pull writes it over yours"
    lines.extend(
        f"- {path}, {PRIVATE}, by {_who(path, commits, merges, authors=True)}: {overwritten}" for path in private
    )
    others = [
        commit
        for commit in commits
        if commit.paths and all(classify(path, context.me, context.members).kind == "member" for path in commit.paths)
    ]
    if others:
        verb = "changes" if len(others) == 1 else "change"
        lines.append(f"- {_count(len(others))} {verb} only the tasks of other members")
    return Incoming(lines=tuple(lines), listed=bool(own or shared or private))


def confirmed(values: Sequence[str], tip: str) -> bool:
    """Whether one value of the setting names the commit pushed, in full."""
    return tip in values


def confirm_command(tip: str) -> str:
    """The git command that pushes the commit `tip` with its shared files confirmed."""
    return f"git -c {SHARED_SETTING}={tip} push"


def refusal(remote_ref: str, lines: Sequence[str]) -> list[str]:
    """What the pre-push hook prints for one refused ref, before the footer."""
    return [f"gemba hook pre-push: push to {remote_ref} refused:", *(f"- {line}" for line in lines)]


def came_in(verb: str, count: int) -> str:
    """The first line a hook prints after a pull that changed a listed path."""
    return f"gemba hook {verb}: {_count(count)} came in"


def uncommitted_line(path: str, context: Context) -> tuple[int, str]:
    """An uncommitted change as `gemba sync` lists it, with the rank of its kind, by which the list is ordered."""
    owner = classify(path, context.me, context.members)
    label = {"own": "yours", "member": f"of {owner.member}", "private": "private", "shared": "shared"}[owner.kind]
    return KINDS.index(owner.kind), f"- {label}: {path}"


def hooks_line(on: bool, states: Mapping[str, obeya.HookState]) -> str | None:
    """What `gemba sync` says when the hooks of the clone disagree with `git_hooks`, or None when they agree."""
    if on:
        missing = [name for name, state in states.items() if state not in INSTALLED]
        return f"hooks: on for this clone, but {_listed(missing)} not installed: run gemba init" if missing else None
    left = [name for name, state in states.items() if state in ("current", "earlier")]
    if not left:
        return None
    return f"hooks: off for this clone, but {_listed(left)} written by gemba still there: run gemba init"


def report(
    branch: str,
    upstream: str,
    incoming_count: int,
    incoming_report: Incoming,
    outgoing_commits: Sequence[Commit],
    outgoing_verdict: Outgoing,
    tip: str,
    uncommitted: Sequence[str],
    context: Context,
    hooks: str | None,
) -> list[str]:
    """The lines of `gemba sync`: the branch, what comes in, what goes out with its problems, the uncommitted changes,
    the hooks when they disagree with the config, and the verdict of a push of `tip`, last."""
    lines = [f"branch {branch}, upstream {upstream}"]
    lines.append(f"incoming: {_count(incoming_count)}" if incoming_count else "incoming: none")
    lines.extend(incoming_report.lines)
    lines.append(f"outgoing: {_count(len(outgoing_commits))}" if outgoing_commits else "outgoing: none")
    lines.extend(f"- {commit.short} {commit.author}: {commit.subject}" for commit in outgoing_commits)
    if outgoing_verdict.problems:
        lines.append("refused:")
        lines.extend(f"- {problem}" for problem in outgoing_verdict.problems)
    if outgoing_verdict.shared:
        lines.append("to confirm:")
        lines.extend(f"- {line}" for line in outgoing_verdict.shared)
    if uncommitted:
        lines.append("uncommitted:")
        lines.extend(line for _rank, line in sorted(uncommitted_line(path, context) for path in uncommitted))
    else:
        lines.append("uncommitted: none")
    if hooks is not None:
        lines.append(hooks)
    lines.append(f"push: {_verdict(bool(outgoing_commits), outgoing_verdict, tip)}")
    return lines


def _verdict(sending: bool, verdict: Outgoing, tip: str) -> str:
    if not sending:
        return "nothing to push"
    if verdict.problems:
        return "refused"
    if verdict.shared:
        return f"needs confirmation: {confirm_command(tip)}"
    return "ready"


def _changes(path: str, commits: Sequence[Commit], merges: Sequence[Commit]) -> str:
    """`<who> changes`, or `<who> change` when several commits change `path`."""
    named = _behind(path, commits, merges)
    return f"{_who(path, commits, merges)} {'changes' if len(named) == 1 else 'change'}"


def _who(path: str, commits: Sequence[Commit], merges: Sequence[Commit], authors: bool = False) -> str:
    """The commits that are not merges and change `path`, or, when none does, the merges of the range."""
    named = [_named(commit, authors) for commit in _behind(path, commits, merges)]
    if not named:
        return "these commits"
    if any(path in commit.paths for commit in commits):
        return _listed(named)
    return f"{'merge' if len(named) == 1 else 'merges'} {_listed(named)}"


def _behind(path: str, commits: Sequence[Commit], merges: Sequence[Commit]) -> list[Commit]:
    """The commits that are not merges and change `path`, or the merges when none does."""
    return [commit for commit in commits if path in commit.paths] or list(merges)


def _named(commit: Commit, authors: bool) -> str:
    return f"{commit.short} ({commit.author})" if authors else commit.short


def _count(count: int) -> str:
    return f"{count} commit" if count == 1 else f"{count} commits"


def _listed(names: Sequence[str]) -> str:
    """`a`, `a and b`, or `a, b and c`."""
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"
