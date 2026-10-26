"""Git on the obeya: every git command `gemba sync`, `gemba hook` and `gemba init` run on the obeya's repository, and
the hooks of its hooks folder.

Each command is an argument list, run as `git --no-optional-locks -c core.quotePath=false
-C <root>`, and only reads: none fetches, pulls, pushes or writes the index or the config, so
that reading never changes the clone, and paths come unquoted, in UTF-8. A command that fails
raises `GitError` with git's message, which the adapter words into its refusal. What git gives
is handed to `sync` as plain data: commits, the paths of a net change, file texts and patches.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from gemba import obeya, platform, sync, tasks

# The full id of a commit, SHA-1 or SHA-256, as a pushed ref names it; an id of zeros names no commit.
COMMIT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class GitError(Exception):
    """A git command on the obeya failed; the message is the command and what git said."""


@dataclass(frozen=True)
class Range:
    """The commits reachable from a tip and from none of the excluded ones: all of them oldest first, those that are
    not merges and the merges, the commits the range starts from, and the paths it changes in the end."""

    every: tuple[sync.Commit, ...]
    commits: tuple[sync.Commit, ...]
    merges: tuple[sync.Commit, ...]
    bases: tuple[str, ...]
    net: tuple[str, ...]


def has_repository(root: Path) -> bool:
    """Whether the obeya root holds `.git`, a folder or the file of a linked worktree: git is never run without it,
    since it would read the repository around the obeya."""
    return (root / ".git").exists()


def hooks_folder(root: Path) -> Path:
    """The folder git runs the hooks of the obeya from, as git names it, joined to the root when it is relative."""
    return root / Path(_text(root, "rev-parse", "--git-path", "hooks").strip())


def hooks_path(root: Path) -> str | None:
    """The value of `core.hooksPath` as configured, or None when it is not set."""
    values = _values(root, "core.hooksPath")
    return values[-1] if values else None


def hook_text(path: Path) -> str | None:
    """The text of a hook, None when there is none; bytes that are not UTF-8 read as a hook of another tool."""
    if not path.exists():
        return None
    if not path.is_file():
        return ""
    data = path.read_bytes()
    try:
        return platform.decode(data)
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")


def hook_states(root: Path) -> dict[str, obeya.HookState]:
    """The state of each hook of a team in the hooks folder git names, `core.hooksPath` included."""
    folder = hooks_folder(root)
    return {name: obeya.hook_state(name, hook_text(folder / name)) for name in obeya.HOOKS}


def branch(root: Path) -> str | None:
    """The name of the branch checked out, or None when `HEAD` is detached."""
    name = _text(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    return None if name == "HEAD" else name


def upstream(root: Path) -> str | None:
    """The short name of the upstream of the branch checked out, such as `origin/main`, or None when it has none."""
    result = _run(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    return result.stdout.decode("utf-8").strip() if result.returncode == 0 else None


def commit_id(root: Path, revision: str) -> str | None:
    """The full id of the commit `revision` names, or None when it names none the clone has."""
    result = _run(root, "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}")
    return result.stdout.decode("utf-8").strip() if result.returncode == 0 else None


def remote_tips(root: Path, remote: str) -> list[str]:
    """The ids the clone holds for the branches of `remote`, as last fetched."""
    return _text(root, "for-each-ref", "--format=%(objectname)", f"refs/remotes/{remote}/").split()


def shared_values(root: Path) -> list[str]:
    """Every value of the setting that confirms the shared files of a push, as git passes it to a hook."""
    return _values(root, sync.SHARED_SETTING)


def read_range(root: Path, tip: str, excluded: Sequence[str]) -> Range:
    """The range of commits reachable from `tip` and from none of `excluded`, and the paths it changes in the end.

    Its bases are the commits of its boundary, reduced to those none of the others holds;
    a path is in the net change when its content at the tip differs from its content at
    every base, and a range with commits and no base counts every path of its tip.
    """
    not_excluded = ["--not", *excluded] if excluded else []
    ids = _text(root, "rev-list", "--reverse", tip, *not_excluded).split()
    if not ids:
        return Range(every=(), commits=(), merges=(), bases=(), net=())
    merge_ids = set(_text(root, "rev-list", "--merges", tip, *not_excluded).split())
    every = tuple(_commit(root, commit, commit in merge_ids) for commit in ids)
    boundary = [
        line[1:] for line in _text(root, "rev-list", "--boundary", tip, *not_excluded).split() if line[0] == "-"
    ]
    bases = _text(root, "merge-base", "--independent", *boundary).split() if len(boundary) > 1 else boundary
    if bases:
        changed = [set(_names(root, "diff", "--name-only", "--no-renames", "-z", base, tip)) for base in bases]
        net = set.intersection(*changed)
    else:
        net = set(_names(root, "ls-tree", "-r", "--name-only", "-z", tip))
    return Range(
        every=every,
        commits=tuple(commit for commit in every if commit.id not in merge_ids),
        merges=tuple(commit for commit in every if commit.id in merge_ids),
        bases=tuple(bases),
        net=tuple(sorted(net)),
    )


def own_files(root: Path, tip: str, me: str, net: Sequence[str]) -> tuple[list[sync.OwnFile], list[str]]:
    """The task files of the net change under tasks/<me>/ as of `tip`, and every path under tasks/<me>/ there."""
    folder = PurePosixPath(tasks.TASKS_DIR, me).as_posix()
    paths = _names(root, "ls-tree", "-r", "--name-only", "-z", tip, "--", f"{folder}/")
    present = set(paths)
    files = []
    for path in net:
        if path.startswith(f"{folder}/") and path.endswith(".md"):
            if path not in present:
                files.append(sync.OwnFile(path, None))
                continue
            data = _bytes(root, "cat-file", "blob", f"{tip}:{path}")
            try:
                files.append(sync.OwnFile(path, platform.decode(data)))
            except UnicodeDecodeError:
                files.append(sync.OwnFile(path, None, unreadable="the file is not UTF-8 text"))
    return files, paths


def patch(root: Path, base: str | None, tip: str, paths: Sequence[str]) -> str:
    """The patch of `paths` from `base`, or from no file at all, to `tip`, shown whole: no external diff and no text
    conversion runs, and bytes that are not UTF-8 are replaced."""
    if not paths:
        return ""
    start = base if base is not None else _empty_tree(root)
    data = _bytes(root, "diff", "--no-color", "--no-ext-diff", "--no-textconv", start, tip, "--", *paths)
    try:
        return platform.decode(data)
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace").replace("\r\n", "\n")


def uncommitted(root: Path) -> list[str]:
    """Every path with a change not committed, staged, unstaged or untracked, ignored files left out."""
    entries = _names(root, "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all")
    return [entry[3:] for entry in entries]


def _commit(root: Path, commit: str, merge: bool) -> sync.Commit:
    full, short, author, subject = _text(root, "log", "-1", "--format=%H%x00%h%x00%an%x00%s", commit).split("\0")
    paths = (
        ()
        if merge
        else tuple(
            _names(root, "diff-tree", "-r", "--root", "--no-commit-id", "--name-only", "--no-renames", "-z", commit)
        )
    )
    return sync.Commit(id=full, short=short, author=author, subject=subject.rstrip("\n"), paths=paths)


def _empty_tree(root: Path) -> str:
    """The id of the empty tree in the object format of the repository, computed without writing it."""
    return _text(root, "hash-object", "-t", "tree", "--stdin", stdin=b"").strip()


def _values(root: Path, key: str) -> list[str]:
    """Every value of a setting, none when it is not set."""
    result = _run(root, "config", "--get-all", key)
    if result.returncode == 1 and not result.stdout:
        return []
    if result.returncode != 0:
        raise GitError(_failure(("config", "--get-all", key), result))
    return result.stdout.decode("utf-8").splitlines()


def _names(root: Path, *arguments: str) -> list[str]:
    """The NUL-separated entries a command given `-z` prints."""
    return [entry for entry in _bytes(root, *arguments).decode("utf-8").split("\0") if entry]


def _text(root: Path, *arguments: str, stdin: bytes | None = None) -> str:
    """The standard output of a git command that must succeed, as UTF-8 text."""
    return _bytes(root, *arguments, stdin=stdin).decode("utf-8")


def _bytes(root: Path, *arguments: str, stdin: bytes | None = None) -> bytes:
    """The standard output of a git command that must succeed."""
    result = _run(root, *arguments, stdin=stdin)
    if result.returncode != 0:
        raise GitError(_failure(arguments, result))
    return result.stdout


def _run(root: Path, *arguments: str, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "--no-optional-locks", "-c", "core.quotePath=false", "-C", str(root), *arguments]
    try:
        if stdin is None:
            return subprocess.run(command, capture_output=True, stdin=subprocess.DEVNULL)
        return subprocess.run(command, capture_output=True, input=stdin)
    except OSError as exc:
        raise GitError(f"git could not be run: {exc}") from None


def _failure(arguments: tuple[str, ...], result: subprocess.CompletedProcess[bytes]) -> str:
    """The failed command and git's message, its hints included."""
    message = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
    command = f"git {' '.join(arguments)} failed"
    return f"{command}: {message}" if message else command
