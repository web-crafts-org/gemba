"""Worktree rules: the branch of a run, the repositories folder, the state of a worktree and its problems."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

# The folder of a harness that holds its worktrees, excluded from the harness repository.
WORKTREES_DIR = "worktrees"
# The first segment of every branch of a run when the gemba config declares no branch_prefix.
DEFAULT_BRANCH_PREFIX = "gemba"
# The remote of every operation.
REMOTE = "origin"
HEADS = "refs/heads/"

# The last line each verb prints in each of its outcomes.
CREATED = "created"
MOVED = "moved"
ALREADY_ATTACHED = "already attached, worktree unchanged"
NOT_REMOVED = "not removed: pass --yes to delete the worktree"
REMOVED = "removed"
NO_WORKTREES = "no worktrees"
NOT_A_WORKTREE = "not a worktree"
UNREADABLE = "state not readable with git"
NOT_ADDED_REFUSAL = "worktree not added:"
NOT_MOVED_REFUSAL = "worktree not moved:"
NOT_REMOVED_REFUSAL = "worktree not removed:"

Kind = Literal["worktree", "not a worktree", "unreadable"]


@dataclass(frozen=True)
class Record:
    """One worktree of a repository, as `git worktree list --porcelain` reports it."""

    path: str
    head: str | None
    branch: str | None  # short name; None when detached or bare
    prunable: bool


@dataclass(frozen=True)
class State:
    """What a folder under `worktrees/` holds, read from git when a verb runs and never stored."""

    path: str  # relative to the harness root, POSIX separators
    kind: Kind = "worktree"
    branch: str | None = None  # None when detached
    upstream: str | None = None
    uncommitted: tuple[str, ...] = ()  # each path as `git status --porcelain` names it
    unpushed: int = 0  # commits of HEAD that are on no remote branch


def branch_name(prefix: str, organization: str, ref: str) -> str:
    """The local branch of every worktree of the run of `ref`."""
    return f"{prefix}/{organization}/{ref}"


def relative_path(repo: str) -> str:
    """Where the worktree of `repo` lives, relative to the harness root."""
    return PurePosixPath(WORKTREES_DIR, repo).as_posix()


def worktree_path(harness_root: Path, repo: str) -> Path:
    """Where the worktree of `repo` lives in the harness at `harness_root`."""
    return harness_root / WORKTREES_DIR / repo


def repos_dir(config_root: Path, declared: str) -> Path:
    """The repositories folder: `declared` with `~` expanded, relative to the tasks repo root unless absolute."""
    path = Path(declared).expanduser()
    return path if path.is_absolute() else config_root / path


def repo_problem(folder: Path, repo: str, repositories: Sequence[str] | None) -> str | None:
    """Why `repo` is not a repository at the root of `folder`, or None when it is one.

    `repositories` are the names of the folders directly under `folder` that hold a git
    repository, or None when `folder` is not a folder.
    """
    if repositories is None:
        return f"repos_dir {folder} is not a folder"
    if repo in repositories:
        return None
    found = f"repositories there: {', '.join(sorted(repositories))}" if repositories else "no repository is there"
    return f"no repository named '{repo}' is at the root of {folder} ({found})"


def parse_worktrees(lines: Sequence[str]) -> list[Record]:
    """The records of `git worktree list --porcelain`, the repository's own working tree first."""
    records = []
    block: list[str] = []
    for line in [*lines, ""]:
        if line:
            block.append(line)
        elif block:
            records.append(_record(block))
            block = []
    return records


def _record(block: Sequence[str]) -> Record:
    path = head = branch = None
    prunable = False
    for line in block:
        key, _separator, value = line.partition(" ")
        if key == "worktree":
            path = value
        elif key == "HEAD":
            head = value
        elif key == "branch":
            branch = value.removeprefix(HEADS)
        elif key == "prunable":
            prunable = True
    return Record(path=path or "", head=head, branch=branch, prunable=prunable)


def render_state(state: State) -> str:
    """The block `list`, `remove` and the refusals of `add` print for one folder under `worktrees/`."""
    if state.kind == "not a worktree":
        return f"{state.path}\n{NOT_A_WORKTREE}"
    if state.kind == "unreadable":
        return f"{state.path}\n{UNREADABLE}"
    return "\n".join(
        [
            state.path,
            f"branch: {state.branch or 'detached'}",
            f"upstream: {state.upstream or 'none'}",
            f"uncommitted: {len(state.uncommitted)}",
            f"unpushed: {state.unpushed}",
        ]
    )


def pending_problems(state: State) -> list[str]:
    """One line for the uncommitted paths and one for the unpushed commits of a worktree, when there are any."""
    if state.kind == "not a worktree":
        return [f"{state.path} is not a worktree"]
    if state.kind == "unreadable":
        return [f"the state of {state.path} could not be read with git"]
    problems = []
    if state.uncommitted:
        count = _count(len(state.uncommitted), "uncommitted path")
        problems.append(f"{state.path} has {count}: {', '.join(state.uncommitted)}")
    if state.unpushed:
        problems.append(f"{state.path} has {_count(state.unpushed, 'commit')} not on any remote branch")
    return problems


def orphan_problem(repo: str, branch: str, unpushed: int) -> str | None:
    """Why the branch of a run left in `repo` without a worktree may not be deleted, or None when it may."""
    if not unpushed:
        return None
    return f"branch {branch} of {repo} has {_count(unpushed, 'commit')} not on any remote branch and no worktree"


def existing_branch_problem(repo: str, branch: str) -> str:
    """The refusal of `add` when the branch of the run is already in `repo` without a worktree."""
    return (
        f"branch {branch} already exists in {repo} without a worktree, left by a harness deleted by hand; "
        "--force deletes and recreates it, discarding its commits"
    )


def folder_problem(path: str, repo: str) -> str:
    """The refusal of `add` when the folder of the worktree holds something else."""
    return f"{path} exists and is not a worktree of {repo}; gemba did not put it there"


def base_problem(from_branch: str | None, remote_branches: Sequence[str], default_branch: str | None) -> str | None:
    """Why the base of a worktree cannot be resolved after the fetch, or None when it can."""
    if from_branch is None and default_branch is None:
        return f"the repository records no default branch for {REMOTE}: --from names the base branch"
    base = from_branch or default_branch
    if base not in remote_branches:
        return f"{REMOTE} has no branch {base}"
    return None


def remote_base(branch: str) -> str:
    """The remote-tracking branch a worktree starts from."""
    return f"{REMOTE}/{branch}"


def render_outcome(path: str, branch: str, base: str, verdict: str) -> str:
    """What `add` prints when it creates or moves a worktree."""
    return "\n".join([path, f"branch: {branch}", f"from: {remote_base(base)}", verdict])


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"
