"""`gemba harness`: launch the harness of a task, the folder of one run, file its notes and remove it."""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import shlex
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path, PurePosixPath

from gemba import config, harness, skills, tasks, worktree
from gemba.commands import worktree as worktree_command


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "harness",
        help="launch the harness of a task, file its notes and remove it",
        description="Create the harness of a task, the folder of one run, work inside it, and remove it.",
    )
    parser.set_defaults(handler=lambda _args: usage(parser))
    verbs = parser.add_subparsers(dest="verb", metavar="<verb>")

    launch = verbs.add_parser(
        "launch",
        help="create the harness of a task and open it in the IDE",
        description=(
            f"Create {harness.HARNESSES_DIR}/<workstream>/<task file name>/ for the task with this ref: "
            f"{harness.CONFIG_FILENAME}, {harness.TASK_LINK}, the guide and the harness skills of every agent "
            f"provider of gemba.yaml, {harness.NOTES_DIR}/, {harness.ASSETS_DIR}/ and {harness.WORKTREES_DIR}/, "
            "as a git repository with one commit. A harness already launched is left as it is. On every launch an "
            "open task moves to in-progress, and the IDE command of gemba.yaml, when declared, is started with the "
            "harness path."
        ),
    )
    launch.add_argument("ref", help="ref of the task, such as SUP-1")
    launch.add_argument("--no-open", action="store_true", help="do not start the IDE command of gemba.yaml")
    launch.add_argument("--root", type=Path, help="tasks repo root (default: walk up to the nearest gemba.yaml)")
    launch.set_defaults(handler=run_launch)

    types = "\n".join(f"  {name:<16} {note_type.definition}" for name, note_type in harness.NOTE_TYPES.items())
    note = verbs.add_parser(
        "note",
        help="file a note drafted under notes/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.fill(
            f"File the draft {harness.NOTES_DIR}/<slug>.md: rename it to "
            f"{harness.NOTES_DIR}/YYYY-MM-DD-HHMMSS-<slug>.md after the clock, write its frontmatter above the body, "
            f"which is kept byte for byte, and commit {harness.NOTES_DIR}/ and {harness.ASSETS_DIR}/. Paths are "
            "relative to the harness root. An external-action note always waits for the user's approval, a "
            "decision note only with --approval.",
            width=79,
        ),
        epilog=f"note types:\n{types}",
    )
    note.add_argument("file", help=f"the draft, {harness.NOTES_DIR}/<slug>.md, with no frontmatter")
    note.add_argument("--type", required=True, choices=list(harness.NOTE_TYPES), help="one of the note types below")
    note.add_argument(
        "--approval", action="store_true", help="file a decision note with approved: false, to wait for the user"
    )
    note.add_argument(
        "--asset",
        dest="assets",
        action="append",
        default=[],
        metavar="PATH",
        help=f"an asset under {harness.ASSETS_DIR}/ the note refers to; repeat for several",
    )
    add_location(note)
    note.set_defaults(handler=run_note)

    resolve = verbs.add_parser(
        "resolve",
        help="record that an approved note was acted on",
        description=(
            f"Append resolved_at to the frontmatter of a filed note whose approved is true, keep its body as it "
            f"is, and commit {harness.NOTES_DIR}/ and {harness.ASSETS_DIR}/. Write the outcome into the body "
            "before running it. Paths are relative to the harness root."
        ),
    )
    resolve.add_argument("note", help=f"the filed note, {harness.NOTES_DIR}/YYYY-MM-DD-HHMMSS-<slug>.md")
    add_location(resolve)
    resolve.set_defaults(handler=run_resolve)

    remove = verbs.add_parser(
        "remove",
        help="delete the harness of a task, its worktrees and their branches, after showing what it holds",
        description=(
            "Show the manifest of the harness of the task with this ref: its path, the task, the launch date and "
            f"the number of notes, assets, commits and worktrees. With --yes, then remove every worktree under "
            f"{harness.WORKTREES_DIR}/, delete every branch of the run in the repositories of repos_dir, and delete "
            "the harness folder. Nothing is deleted while the harness repository has uncommitted changes, the "
            "working directory is inside the harness, a worktree or a branch of the run holds uncommitted paths or "
            f"commits on no remote branch, or a folder under {harness.WORKTREES_DIR}/ is not a worktree; --force "
            "discards those three, never the first two. The task file and the remotes are not touched."
        ),
    )
    remove.add_argument("ref", help="ref of the task, such as SUP-1")
    remove.add_argument("--yes", action="store_true", help="delete the harness after showing the manifest")
    remove.add_argument(
        "--force",
        action="store_true",
        help="delete even when the worktrees or the branches of the run hold work that is discarded",
    )
    remove.add_argument("--root", type=Path, help="tasks repo root (default: walk up to the nearest gemba.yaml)")
    remove.set_defaults(handler=run_remove)


def run_launch(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail("launch", str(exc))

    errors = []
    if gemba_config.agent_providers is None:
        errors.append(
            f"no agent providers declared: add agent_providers to {config.CONFIG_FILENAME} "
            f"(known providers: {', '.join(skills.PROVIDERS)})"
        )
    try:
        task = tasks.find_by_ref(gemba_config.root, gemba_config.workstreams, args.ref)
    except tasks.TaskError as exc:
        task = None
        errors.append(str(exc))
    else:
        if task is None:
            errors.append(f"no task has ref '{args.ref}' under {tasks.TASKS_DIR}/, archives included")
        elif task.archived:
            errors.append(f"{task.ref} is archived ({task.path}): an archived task cannot be launched")
        elif task.status == "done":
            errors.append(
                f"{task.ref} is done ({task.path}): a done task cannot be launched; "
                f"move it to open or in-progress first with gemba mark {task.ref} <status>"
            )
    if errors:
        return fail("launch", "harness not launched:\n" + "\n".join(f"- {error}" for error in errors))
    assert task is not None and gemba_config.agent_providers is not None, "every failed check appended an error"

    root = gemba_config.root
    folder = harness.harness_path(root, task.workstream, PurePosixPath(task.path).stem)
    print(folder.relative_to(root).as_posix())
    launched = (folder / harness.CONFIG_FILENAME).is_file()
    today = datetime.date.today()
    if launched and has_commit(folder):
        print("already launched, harness unchanged")
        start_work(root, task, today)
        return open_ide(gemba_config, folder, args.no_open)

    write_layout(gemba_config, task, folder)
    if not launched:
        package_version = version("gemba-cli")
        identity = harness.HarnessConfig(
            task=task.path,
            ref=task.ref,
            workstream=task.workstream,
            agent_providers=gemba_config.agent_providers,
            launched_at=today,
            gemba_version=package_version,
        )
        write_new(folder / harness.CONFIG_FILENAME, harness.render_config(identity))
    start_work(root, task, today)

    if not (folder / ".git").exists():
        problem = git(folder, "init", "--quiet", "--initial-branch", harness.BRANCH)
        if problem:
            return fail("launch", git_failure(problem, task.ref))
    if not has_commit(folder):
        problem = git(folder, "add", "-A") or git(folder, "commit", "--quiet", "-m", harness.launch_message(task.ref))
        if problem:
            return fail("launch", git_failure(problem, task.ref))
    return open_ide(gemba_config, folder, args.no_open)


def start_work(root: Path, task: tasks.Task, today: datetime.date) -> None:
    """Move an open task to in-progress through the status table, and say what happened to its status."""
    task_file = root / task.path
    text, moved = tasks.start(task_file.read_bytes().decode("utf-8"), today)
    if moved.changed:
        task_file.write_bytes(text.encode("utf-8"))
        print(f"status: {moved.old_status} -> {moved.new_status}")
    else:
        print(f"status: {moved.old_status}, left as it was")


def run_note(args: argparse.Namespace) -> int:
    try:
        folder = locate(args.harness)
    except harness.HarnessError as exc:
        return fail("note", str(exc))

    draft = folder / args.file
    errors = [f"{args.file} {problem}" for problem in harness.check_draft(draft, folder)]
    if problem := harness.approval_problem(args.type, args.approval):
        errors.append(problem)
    assets, asset_errors = harness.check_assets(args.assets, folder)
    errors.extend(asset_errors)
    if errors:
        return fail("note", "note not filed:\n" + "\n".join(f"- {error}" for error in errors))

    now = datetime.datetime.now()
    target = draft.parent / harness.note_filename(now, draft.stem)
    relative = target.resolve().relative_to(folder).as_posix()
    if target.exists():
        return fail("note", f"note not filed: {relative} already exists; file the note again")
    try:
        body = draft.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return fail("note", f"note not filed: {args.file} is not UTF-8 text")
    frontmatter = harness.NoteFrontmatter(
        type=args.type,
        date=now.date(),
        time=f"{now:%H:%M:%S}",
        approved=False if harness.is_gated(args.type, args.approval) else None,
        assets=tuple(assets),
    )
    with target.open("xb") as handle:
        handle.write(f"{harness.render_note_frontmatter(frontmatter)}\n{body}".encode())
    draft.unlink()

    if problem := commit(folder, harness.note_message(args.type, draft.stem)):
        return fail("note", f"{relative} is filed but not committed: {problem}")
    print(relative)
    return 0


def run_resolve(args: argparse.Namespace) -> int:
    try:
        folder = locate(args.harness)
    except harness.HarnessError as exc:
        return fail("resolve", str(exc))

    path = folder / args.note
    problems = harness.check_filed(path, folder)
    if problems:
        return fail("resolve", "note not resolved:\n" + "\n".join(f"- {args.note} {problem}" for problem in problems))
    try:
        block, rest = harness.split_note(path.read_bytes().decode("utf-8"))
        assert block is not None, "check_filed found the frontmatter"
        frontmatter = harness.parse_note_frontmatter(block)
    except (harness.HarnessError, UnicodeDecodeError) as exc:
        return fail("resolve", f"note not resolved: {args.note}: {exc}")
    if problem := harness.check_resolvable(frontmatter):
        return fail("resolve", f"note not resolved: {args.note} {problem}")

    resolved_at = datetime.datetime.now().isoformat(timespec="seconds")
    resolved = dataclasses.replace(frontmatter, resolved_at=resolved_at)
    path.write_bytes(f"{harness.render_note_frontmatter(resolved)}{rest}".encode())
    relative = path.resolve().relative_to(folder).as_posix()
    slug = harness.filed_slug(path.name)
    assert slug is not None, "check_filed matched the name"
    if problem := commit(folder, harness.resolve_message(slug)):
        return fail("resolve", f"{relative} is resolved but not committed: {problem}")
    print(relative)
    return 0


def run_remove(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail("remove", str(exc))

    root = gemba_config.root
    try:
        task = tasks.find_by_ref(root, gemba_config.workstreams, args.ref)
    except tasks.TaskError as exc:
        return refuse_removal([str(exc)])
    if task is None:
        return refuse_removal([f"no task has ref '{args.ref}' under {tasks.TASKS_DIR}/, archives included"])
    folder = harness.harness_path(root, task.workstream, PurePosixPath(task.path).stem)
    relative = folder.relative_to(root).as_posix()
    if not folder.exists():
        return refuse_removal([f"{task.ref} has no harness: nothing exists at {relative}"])
    if not (folder / harness.CONFIG_FILENAME).is_file():
        not_a_harness = f"{relative} is not a harness: it holds no {harness.CONFIG_FILENAME}"
        return refuse_removal([f"{not_a_harness}; delete it by hand if it is not needed"])
    try:
        identity = harness.read_config(folder, list(skills.PROVIDERS))
    except harness.HarnessError as exc:
        return refuse_removal([str(exc)])

    status = git_lines(folder, "status", "--porcelain", "--untracked-files=all")
    commits = git_lines(folder, "rev-list", "--count", "HEAD") if has_commit(folder) else ["0"]
    names = worktree_command.entries(folder)
    states = [worktree_command.read_state(folder, name) for name in names]
    orphans = orphan_branches(gemba_config, identity.ref, folder.resolve())
    manifest = harness.Manifest(
        path=relative,
        task=identity.task,
        launched_at=identity.launched_at,
        notes=count_files(folder / harness.NOTES_DIR),
        assets=count_files(folder / harness.ASSETS_DIR),
        commits=int(commits[0]) if commits else 0,
        worktrees=sum(1 for state in states if state.kind != "not a worktree"),
        uncommitted=None if status is None else harness.uncommitted_paths(status),
    )
    print(harness.render_manifest(manifest))
    found = [(orphan.repo, orphan.branch, orphan.unpushed) for orphan in orphans]
    problems = harness.removal_problems(Path.cwd().resolve(), folder.resolve(), status, states, found, args.force)
    if problems:
        return refuse_removal(problems)
    if not args.yes:
        print(harness.NOT_REMOVED)
        return 0

    if problem := delete_run(folder, relative, names, states, orphans, args.force):
        again = f"run gemba harness remove {task.ref} --yes again to remove what is left"
        return fail("remove", f"{relative} was not removed completely: {problem}; {again}")
    try:
        shutil.rmtree(folder)
    except OSError as exc:
        return fail("remove", f"{relative} was not removed completely: {exc}; delete what is left by hand")
    print(harness.REMOVED)
    return 0


def delete_run(
    folder: Path,
    relative: str,
    names: list[str],
    states: list[worktree.State],
    orphans: list[Orphan],
    force: bool,
) -> str | None:
    """Remove every worktree of the harness, then delete every branch of the run left without one.

    None when everything is deleted; otherwise what failed, followed by what was deleted before it.
    """
    done = []
    for name, state in zip(names, states, strict=True):
        if state.kind == "not a worktree":
            continue
        path = f"{relative}/{state.path}"
        if problem := worktree_command.delete(worktree.worktree_path(folder, name), path, state.branch, force):
            return "; ".join([problem, *done])
        done.append(f"{path} was removed")
    for orphan in orphans:
        # A record left by a worktree folder deleted by hand keeps its branch checked out until pruned.
        if problem := git(orphan.repository, "worktree", "prune") or git(
            orphan.repository, "branch", "--quiet", "-D", orphan.branch
        ):
            return "; ".join([problem, *done])
        done.append(f"branch {orphan.branch} of {orphan.repo} was deleted")
    return None


@dataclass(frozen=True)
class Orphan:
    """A branch of the run left in a repository of repos_dir without a worktree."""

    repo: str
    repository: Path
    branch: str
    unpushed: int


def orphan_branches(gemba_config: config.Config, ref: str, harness_root: Path) -> list[Orphan]:
    """The branches of the run of `ref` left without a worktree in the repositories at the root of repos_dir.

    A branch is the run's when it is named after the run, or when it is recorded for a
    worktree under `harness_root` whose folder is gone. None is found without repos_dir.
    """
    if gemba_config.repos_dir is None:
        return []
    repos = worktree.repos_dir(gemba_config.root, gemba_config.repos_dir)
    named = None
    if gemba_config.organization is not None:
        named = worktree.branch_name(gemba_config.branch_prefix, gemba_config.organization, ref)
    orphans = []
    for repo in worktree_command.repositories(repos) or []:
        repository = (repos / repo).resolve()
        records = worktree.parse_worktrees(git_lines(repository, "worktree", "list", "--porcelain") or [])
        held = {record.branch for record in records if not record.prunable}
        branches = {
            record.branch
            for record in records
            if record.prunable and record.branch and Path(record.path).is_relative_to(harness_root)
        }
        if named is not None and named not in held:
            branches.add(named)
        for branch in sorted(branches):
            if not worktree_command.has_branch(repository, branch):
                continue
            count = git_lines(repository, "rev-list", "--count", branch, "--not", "--remotes")
            if count:
                orphans.append(Orphan(repo, repository, branch, int(count[0])))
    return orphans


def refuse_removal(problems: list[str]) -> int:
    return fail("remove", f"{harness.REMOVAL_REFUSED}\n" + "\n".join(f"- {problem}" for problem in problems))


def count_files(folder: Path) -> int:
    """The number of files at any depth under `folder`; none when it does not exist."""
    return sum(1 for path in folder.rglob("*") if path.is_file()) if folder.is_dir() else 0


def add_location(parser: argparse.ArgumentParser) -> None:
    """The options every verb acting on an existing harness takes."""
    parser.add_argument(
        "--harness", type=Path, help=f"harness root (default: walk up to the nearest {harness.CONFIG_FILENAME})"
    )
    # Accepted like on every command; the harness is found from --harness or the working directory.
    parser.add_argument("--root", type=Path, help=argparse.SUPPRESS)


def locate(given: Path | None) -> Path:
    """The harness root named by `--harness`, or the nearest one at or above the working directory."""
    if given is None:
        return harness.find_root(Path.cwd())
    folder = given.resolve()
    if not (folder / harness.CONFIG_FILENAME).is_file():
        raise harness.HarnessError(f"{given} is not a harness: it holds no {harness.CONFIG_FILENAME}")
    return folder


def commit(folder: Path, message: str) -> str | None:
    """Commit the notes and assets of the harness; None when it succeeds, git's message otherwise."""
    return git(folder, "add", "-A", "--", harness.NOTES_DIR, harness.ASSETS_DIR) or git(
        folder, "commit", "--quiet", "-m", message
    )


def write_layout(gemba_config: config.Config, task: tasks.Task, folder: Path) -> None:
    """Every piece of the harness except its config, each written only when it is missing."""
    assert gemba_config.agent_providers is not None
    for name in (harness.NOTES_DIR, harness.ASSETS_DIR, harness.WORKTREES_DIR):
        (folder / name).mkdir(parents=True, exist_ok=True)
    write_new(folder / harness.GITIGNORE, harness.GITIGNORE_TEXT)
    link = folder / harness.TASK_LINK
    if not link.is_symlink() and not link.exists():
        link.symlink_to(harness.task_link_target(task.path))
    guide = harness.render_guide(
        skills.guide_asset(),
        config.guide(gemba_config.processes),
        config.guide(gemba_config.workstreams[task.workstream].processes),
    )
    for provider in gemba_config.agent_providers:
        write_new(folder / skills.PROVIDERS[provider].guide, guide)
    for action in skills.plan(folder, gemba_config.agent_providers, version("gemba-cli"), "harness"):
        if action.state == "missing":
            write_new(folder / action.path, action.content)


def write_new(path: Path, content: str) -> None:
    """Write `content` at `path` unless a file is already there."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def has_commit(folder: Path) -> bool:
    """Whether the harness has a git repository of its own holding at least one commit."""
    if not (folder / ".git").exists():
        return False
    return git(folder, "rev-parse", "--verify", "--quiet", "HEAD") is None


def git(folder: Path, *arguments: str) -> str | None:
    """Run git in the harness; None when it succeeds, the failed command and git's message otherwise."""
    command = ["git", "-C", str(folder), *arguments]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except OSError as exc:
        return f"git could not be run: {exc}"
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        return f"git {' '.join(arguments)} failed: {message}" if message else f"git {' '.join(arguments)} failed"
    return None


def git_lines(folder: Path, *arguments: str) -> list[str] | None:
    """The output lines of a git command that only reads the harness repository, or None when it fails.

    Optional locks are off, so that reading never rewrites the index. A folder without
    a `.git` of its own is never read, since git would read the repository around it.
    """
    if not (folder / ".git").exists():
        return None
    command = ["git", "--no-optional-locks", "-C", str(folder), *arguments]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout.splitlines() if result.returncode == 0 else None


def git_failure(problem: str, ref: str) -> str:
    hint = ""
    if "user.email" in problem or "identity" in problem.lower():
        hint = "\nset your git identity with git config --global user.name and user.email"
    return f"{problem}{hint}\nthe files written are kept; run gemba harness launch {ref} again to finish the harness"


def open_ide(gemba_config: config.Config, folder: Path, no_open: bool) -> int:
    """Start the IDE command of the config on the harness without waiting for it, and say so."""
    if no_open or gemba_config.ide is None:
        return 0
    try:
        command = [*shlex.split(gemba_config.ide), str(folder)]
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except (OSError, ValueError) as exc:
        return fail(
            "launch", f"the harness is ready but the IDE command '{gemba_config.ide}' could not be started: {exc}"
        )
    print(f"opening: {' '.join(command)}")
    return 0


def usage(parser: argparse.ArgumentParser) -> int:
    parser.print_help(sys.stderr)
    return 1


def fail(verb: str, message: str) -> int:
    # What was printed before, such as the manifest of remove, comes first in a combined capture.
    sys.stdout.flush()
    print(f"gemba harness {verb}: {message}", file=sys.stderr)
    return 1
