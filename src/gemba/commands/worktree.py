"""`gemba worktree`: add, list and remove the git worktrees of the repositories a run works on."""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
import time
from pathlib import Path

from gemba import config, harness, platform, skills, worktree
from gemba.commands import harness as harness_command


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "worktree",
        help="add, list and remove the worktrees of the repositories of a run",
        description=(
            f"Check out the repositories of repos_dir as git worktrees under {worktree.WORKTREES_DIR}/ of a "
            "harness, each on the local branch of the run, list them and remove them. Every verb runs inside a "
            "harness; nothing is ever pushed or deleted on the remote."
        ),
    )
    parser.set_defaults(handler=lambda _args: harness_command.usage(parser))
    verbs = parser.add_subparsers(dest="verb", metavar="<verb>")

    add = verbs.add_parser(
        "add",
        help="create the worktree of a repository, or move it to another base",
        description=textwrap.fill(
            f"Fetch {worktree.REMOTE} with pruning and create {worktree.WORKTREES_DIR}/<repo> on the local branch "
            f"<branch_prefix>/<obeya>/<ref>, started at {worktree.REMOTE}/<branch> or at the default branch "
            f"of {worktree.REMOTE}, with no upstream. <repo> is a folder directly under repos_dir that holds a git "
            "repository. When the worktree is already there, nothing changes without --from; with --from its "
            "branch moves to the new base, refused while anything is uncommitted or on no remote branch. The "
            "harness repository is not committed.",
            width=79,
        ),
    )
    add.add_argument("repo", help="name of a folder directly under repos_dir that holds a git repository")
    add.add_argument(
        "--from",
        dest="base",
        metavar="BRANCH",
        help=f"branch of {worktree.REMOTE} to start from (default: the default branch of {worktree.REMOTE})",
    )
    add.add_argument(
        "--force",
        action="store_true",
        help="delete and recreate a branch of the run left without a worktree; with --from, move the branch even "
        "when uncommitted paths or unpushed commits are discarded",
    )
    harness_command.add_location(add)
    add.set_defaults(handler=run_add)

    list_ = verbs.add_parser(
        "list",
        help="show the branch, upstream and pending work of every worktree",
        description=(
            f"Print, for every folder under {worktree.WORKTREES_DIR}/ in name order, its path, branch, upstream, "
            "the number of uncommitted paths and the number of commits on no remote branch, read from git. With "
            "--available, print instead the repositories that add accepts."
        ),
    )
    list_.add_argument(
        "--available",
        action="store_true",
        help="print the name of every folder directly under repos_dir that holds a git repository, attached or "
        "not, one per line in name order",
    )
    harness_command.add_location(list_)
    list_.set_defaults(handler=run_list)

    remove = verbs.add_parser(
        "remove",
        help="delete the worktree of a repository and its branch, after showing its state",
        description=textwrap.fill(
            f"Show the state of {worktree.WORKTREES_DIR}/<repo>, as list shows it. With --yes, then remove the "
            "worktree from its repository and delete the branch checked out in it. Nothing is deleted while the "
            "worktree has uncommitted paths or commits on no remote branch, unless --force is given. The remote "
            "is never touched.",
            width=79,
        ),
    )
    remove.add_argument("repo", help=f"name of the worktree, the folder under {worktree.WORKTREES_DIR}/")
    remove.add_argument("--yes", action="store_true", help="delete the worktree and its branch after showing them")
    remove.add_argument(
        "--force", action="store_true", help="delete even when uncommitted paths or unpushed commits are discarded"
    )
    harness_command.add_location(remove)
    remove.set_defaults(handler=run_remove)


def run_add(args: argparse.Namespace) -> int:
    try:
        folder = harness_command.locate(args.harness)
        gemba_config = config.load(root=args.root, cwd=folder)
        identity = harness.read_config(folder, list(skills.PROVIDERS))
    except (harness.HarnessError, config.ConfigError) as exc:
        return fail("add", str(exc))

    path = worktree.relative_path(args.repo)
    target = worktree.worktree_path(folder, args.repo)
    errors = []
    if gemba_config.obeya is None:
        errors.append(f"no obeya declared: add obeya to {config.CONFIG_FILENAME}")
    repository = None
    if gemba_config.repos_dir is None:
        errors.append(worktree.missing_repos_dir_problem(config.LOCAL_FILENAME))
    else:
        repos = worktree.repos_dir(gemba_config.root, gemba_config.repos_dir)
        if problem := worktree.repo_problem(repos, args.repo, repositories(repos)):
            errors.append(problem)
        else:
            repository = (repos / args.repo).resolve()
    attached = False
    if repository is not None and os.path.lexists(target):
        attached = common_repository(target) == repository
        if not attached:
            errors.append(worktree.folder_problem(path, args.repo))
    if errors:
        return fail("add", refusal(worktree.NOT_ADDED_REFUSAL, errors))
    assert repository is not None and gemba_config.obeya is not None, "every failed check appended an error"

    if attached and args.base is None:
        print(f"{path}\n{worktree.ALREADY_ATTACHED}")
        return 0
    header = worktree.NOT_MOVED_REFUSAL if attached else worktree.NOT_ADDED_REFUSAL
    # The default branch is what the repository records: the fetch never creates or moves it.
    keep_default = f"remote.{worktree.REMOTE}.followRemoteHEAD=never"
    if problem := harness_command.git(repository, "-c", keep_default, "fetch", "--quiet", "--prune", worktree.REMOTE):
        return fail("add", refusal(header, [problem]))
    remote_heads = f"refs/remotes/{worktree.REMOTE}/"
    remote_branches = harness_command.git_lines(repository, "for-each-ref", "--format=%(refname)", remote_heads)
    default = None
    if args.base is None:
        head = harness_command.git_lines(repository, "symbolic-ref", "--quiet", f"{remote_heads}HEAD")
        default = head[0].removeprefix(remote_heads) if head else None
    branches = [line.removeprefix(remote_heads) for line in remote_branches or []]
    if problem := worktree.base_problem(args.base, branches, default):
        return fail("add", refusal(header, [problem]))
    base = args.base or default
    assert base is not None, "base_problem refuses a missing base"

    if attached:
        return move(folder, args.repo, base, args.force)
    branch = worktree.branch_name(gemba_config.branch_prefix, gemba_config.obeya, identity.ref)
    if problem := harness_command.git(repository, "worktree", "prune"):
        return fail("add", refusal(header, [problem]))
    records = worktree.parse_worktrees(harness_command.git_lines(repository, "worktree", "list", "--porcelain") or [])
    if has_branch(repository, branch) and all(record.branch != branch for record in records):
        if not args.force:
            return fail("add", refusal(header, [worktree.existing_branch_problem(args.repo, branch)]))
        if problem := harness_command.git(repository, "branch", "--quiet", "-D", branch):
            return fail("add", refusal(header, [problem]))
    start = worktree.remote_base(base)
    if problem := harness_command.git(
        repository, "worktree", "add", "--quiet", "--no-track", "-b", branch, str(target), start
    ):
        return fail("add", refusal(header, [harness_command.hinted(problem)]))
    print(worktree.render_outcome(path, branch, base, worktree.CREATED))
    return 0


def move(folder: Path, repo: str, base: str, force: bool) -> int:
    """Move the branch of an attached worktree to `base`, after the pending checks unless `force`."""
    state = read_state(folder, repo)
    problems = [] if force else worktree.pending_problems(state)
    if problems:
        print(worktree.render_state(state))
        return fail("add", refusal(worktree.NOT_MOVED_REFUSAL, problems))
    target = worktree.worktree_path(folder, repo)
    start = worktree.remote_base(base)
    if problem := harness_command.git(target, "reset", "--quiet", "--hard", start) or harness_command.git(
        target, "clean", "--quiet", "-d", "--force"
    ):
        return fail("add", refusal(worktree.NOT_MOVED_REFUSAL, [harness_command.hinted(problem)]))
    print(worktree.render_outcome(state.path, state.branch or "detached", base, worktree.MOVED))
    return 0


def run_list(args: argparse.Namespace) -> int:
    try:
        folder = harness_command.locate(args.harness)
    except harness.HarnessError as exc:
        return fail("list", str(exc))
    if args.available:
        return list_available(folder, args.root)
    names = entries(folder)
    if not names:
        print(worktree.NO_WORKTREES)
        return 0
    print("\n\n".join(worktree.render_state(read_state(folder, name)) for name in names))
    return 0


def list_available(folder: Path, root: Path | None) -> int:
    """Print the repositories at the root of repos_dir that `add` accepts, read from the config of `folder`."""
    try:
        gemba_config = config.load(root=root, cwd=folder)
    except config.ConfigError as exc:
        return fail("list", str(exc))
    if gemba_config.repos_dir is None:
        return fail("list", worktree.missing_repos_dir_problem(config.LOCAL_FILENAME))
    repos = worktree.repos_dir(gemba_config.root, gemba_config.repos_dir)
    names = repositories(repos)
    if names is None:
        return fail("list", worktree.not_a_folder_problem(repos))
    print("\n".join(names) if names else worktree.NO_REPOSITORIES)
    return 0


def run_remove(args: argparse.Namespace) -> int:
    try:
        folder = harness_command.locate(args.harness)
    except harness.HarnessError as exc:
        return fail("remove", str(exc))

    path = worktree.relative_path(args.repo)
    if args.repo not in entries(folder):
        return fail("remove", refusal(worktree.NOT_REMOVED_REFUSAL, [f"nothing exists at {path}"]))
    state = read_state(folder, args.repo)
    if state.kind == "not a worktree":
        not_a_worktree = f"{path} is not a worktree; delete it by hand if it is not needed"
        return fail("remove", refusal(worktree.NOT_REMOVED_REFUSAL, [not_a_worktree]))
    print(worktree.render_state(state))
    problems = [] if args.force else worktree.pending_problems(state)
    if problems:
        return fail("remove", refusal(worktree.NOT_REMOVED_REFUSAL, problems))
    if not args.yes:
        print(worktree.NOT_REMOVED)
        return 0
    again = f"gemba worktree remove {args.repo} --yes"
    if problem := delete(worktree.worktree_path(folder, args.repo), path, state.branch, args.force, again):
        return fail("remove", problem)
    print(worktree.REMOVED)
    return 0


def delete(target: Path, path: str, branch: str | None, force: bool, again: str) -> str | None:
    """Remove the worktree at `target`, named `path` in messages, and delete `branch` from its repository.

    None when both succeed, what was left and why otherwise. A path another program holds is retried on the
    schedule of the platform rules and, when it stays held, reported with the command, `again`, that finishes.
    """
    repository = common_repository(target)
    if repository is None:
        return f"{path} was not removed: the repository it belongs to could not be read"
    problem = None
    for delay in (None, *platform.HELD_RETRY_DELAYS):
        if delay is not None:
            time.sleep(delay)
        arguments = ["worktree", "remove", *(["--force"] if force else []), str(target)]
        problem = harness_command.git(repository, *arguments)
        if problem is None or not harness.is_held(problem):
            break
    if problem is not None:
        if harness.is_held(problem):
            return harness.not_removed(path, problem, again)
        return f"{path} was not removed: {harness_command.hinted(problem)}"
    if branch is not None and (problem := harness_command.git(repository, "branch", "--quiet", "-D", branch)):
        return f"{path} was removed but its branch {branch} was not deleted from {repository}: {problem}"
    return None


def entries(harness_root: Path) -> list[str]:
    """The names under `worktrees/` of the harness, in name order; none when the folder does not exist."""
    folder = harness_root / worktree.WORKTREES_DIR
    return sorted(entry.name for entry in folder.iterdir()) if folder.is_dir() else []


def read_state(harness_root: Path, name: str) -> worktree.State:
    """The state of `worktrees/<name>` of the harness, read from git without writing to any repository."""
    folder = harness_root / worktree.WORKTREES_DIR / name
    path = worktree.relative_path(name)
    if folder.is_symlink() or not folder.is_dir() or common_repository(folder) is None:
        return worktree.State(path, kind="not a worktree")
    branch = harness_command.git_lines(folder, "symbolic-ref", "--quiet", "--short", "HEAD")
    upstream = harness_command.git_lines(folder, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    status = harness_command.git_lines(folder, "status", "--porcelain", "--untracked-files=all")
    unpushed = harness_command.git_lines(folder, "rev-list", "--count", "HEAD", "--not", "--remotes")
    if status is None or not unpushed:
        return worktree.State(path, kind="unreadable", branch=branch[0] if branch else None)
    return worktree.State(
        path,
        branch=branch[0] if branch else None,
        upstream=upstream[0] if upstream else None,
        uncommitted=tuple(line[3:] for line in status if line.strip()),
        unpushed=int(unpushed[0]),
    )


def common_repository(folder: Path) -> Path | None:
    """The repository `folder` is a linked worktree of, resolved, or None when it is not one."""
    if not (folder / ".git").is_file():
        return None
    lines = harness_command.git_lines(
        folder, "rev-parse", "--path-format=absolute", "--show-toplevel", "--git-dir", "--git-common-dir"
    )
    if lines is None or len(lines) != 3:
        return None
    top, git_dir, common = (Path(line).resolve() for line in lines)
    if top != folder.resolve() or git_dir == common:
        return None
    return common.parent if common.name == ".git" else common


def repositories(folder: Path) -> list[str] | None:
    """The folders directly under `folder` that hold a git repository, or None when `folder` is not a folder."""
    if not folder.is_dir():
        return None
    return sorted(entry.name for entry in folder.iterdir() if entry.is_dir() and (entry / ".git").exists())


def has_branch(repository: Path, branch: str) -> bool:
    """Whether the repository holds the local branch `branch`."""
    return harness_command.git_lines(repository, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}") is not None


def refusal(header: str, problems: list[str]) -> str:
    return f"{header}\n" + "\n".join(f"- {problem}" for problem in problems)


def fail(verb: str, message: str) -> int:
    # What was printed before, such as the state of a worktree, comes first in a combined capture.
    sys.stdout.flush()
    print(f"gemba worktree {verb}: {message}", file=sys.stderr)
    return 1
