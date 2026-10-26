"""`gemba hook pre-push`, `post-merge` and `post-rewrite`: the checks git runs inside a push and a pull of an obeya with
a team, from the hook scripts `gemba init` writes; they only report, as a lint does, and write nothing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gemba import config, platform, sync, team
from gemba.commands import obeya_git

# The id git gives for a ref that does not exist: a new branch on the remote, or a branch the push deletes.
ZERO = frozenset("0")


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "hook",
        help="the checks git runs from the hooks of an obeya with a team",
        description=(
            "The checks git runs inside a push and a pull of an obeya with a team, from the hook scripts gemba init "
            "writes when git_hooks turns them on; a person or an agent never needs to run them. Each verb finds the "
            "obeya by walking up from the working folder, reads git without writing to it, and prints nothing in an "
            "obeya without a team."
        ),
    )
    parser.set_defaults(handler=lambda _args: usage(parser))
    verbs = parser.add_subparsers(dest="verb", metavar="<verb>")

    pre_push = verbs.add_parser(
        "pre-push",
        help="check every pushed ref against who owns each path",
        description=(
            "Read one '<local ref> <local id> <remote ref> <remote id>' line per pushed ref on the standard input, "
            "as git gives it, and check what each push changes in the end: another member's folder and the private "
            "files never go out, the member's own task files must read as tasks with their initials and no ref "
            "twice, and the shared files go out once confirmed with git -c gemba.shared=<id of the commit pushed> "
            "push. Every problem is printed at once and the command exits 1, so that git refuses the push; "
            "git push --no-verify skips the checks."
        ),
    )
    pre_push.add_argument("remote", help="the name of the remote, or its URL, as git passes it")
    pre_push.add_argument("url", nargs="?", help="the URL of the remote, as git passes it")
    pre_push.set_defaults(handler=run_pre_push)

    post_merge = verbs.add_parser(
        "post-merge",
        help="show what a pull that merged changed in the member's own tasks and the shared files",
        description=(
            "Show, on the standard error, what the merge or fast-forward of a pull changed in the end: the patch of "
            "the member's own tasks, the shared files and the private ones, each with the commits behind it. It "
            "always exits 0."
        ),
    )
    post_merge.add_argument("squash", nargs="?", help="1 for a squash merge, as git passes it")
    post_merge.set_defaults(handler=run_post_merge)

    post_rewrite = verbs.add_parser(
        "post-rewrite",
        help="show what a rebasing pull brought into the member's own tasks and the shared files",
        description=(
            "After a rebase, show on the standard error what the commits the local ones were rebased onto changed, "
            "as post-merge does; after an amend, nothing. It always exits 0."
        ),
    )
    post_rewrite.add_argument("command", nargs="?", help="rebase or amend, as git passes it")
    post_rewrite.set_defaults(handler=run_post_rewrite)


def run_pre_push(args: argparse.Namespace) -> int:
    loaded = load("pre-push")
    if not isinstance(loaded, config.Config):
        return loaded
    root = loaded.root
    try:
        pushed = refs(platform.decode(sys.stdin.buffer.read()))
    except (UnicodeDecodeError, ValueError) as exc:
        return fail("pre-push", f"the pushed refs cannot be read: {exc}", 1)
    context = sync.context_of(loaded)
    output: list[str] = []
    try:
        for remote_ref, local_id, remote_id in pushed:
            known = None if set(remote_id) == ZERO else obeya_git.commit_id(root, remote_id)
            excluded = [known] if known is not None else obeya_git.remote_tips(root, args.remote)
            outgoing = obeya_git.read_range(root, local_id, excluded)
            if not outgoing.every:
                continue
            if context is None:
                missing = team.write_problems(loaded.team, None, None, config.LOCAL_FILENAME)
                output.extend(sync.refusal(remote_ref, missing))
                continue
            files, paths = obeya_git.own_files(root, local_id, context.me, outgoing.net)
            confirmed = sync.confirmed(obeya_git.shared_values(root), local_id)
            verdict = sync.outgoing(outgoing.net, outgoing.commits, outgoing.merges, files, paths, context, confirmed)
            if lines := verdict.lines(local_id):
                output.extend(sync.refusal(remote_ref, lines))
    except obeya_git.GitError as exc:
        return fail("pre-push", str(exc), 1)
    if not output:
        return 0
    print("\n".join([*output, sync.REFUSAL_FOOTER]), file=sys.stderr)
    return 1


def run_post_merge(_args: argparse.Namespace) -> int:
    loaded = load("post-merge")
    if not isinstance(loaded, config.Config):
        return loaded
    try:
        tip, before = obeya_git.commit_id(loaded.root, "HEAD"), obeya_git.commit_id(loaded.root, "ORIG_HEAD")
        if tip is None or before is None:
            return 0
        return show("post-merge", loaded, tip, before)
    except obeya_git.GitError as exc:
        return fail("post-merge", str(exc), 0)


def run_post_rewrite(args: argparse.Namespace) -> int:
    if args.command != "rebase":
        return 0
    loaded = load("post-rewrite")
    if not isinstance(loaded, config.Config):
        return loaded
    try:
        rewritten = platform.decode(sys.stdin.buffer.read()).split("\n", 1)[0].split()
    except UnicodeDecodeError:
        rewritten = []
    root = loaded.root
    try:
        new = rewritten[1] if len(rewritten) > 1 and obeya_git.COMMIT_ID.match(rewritten[1]) else None
        onto = obeya_git.commit_id(root, "HEAD" if new is None else f"{new}^1")
        before = obeya_git.commit_id(root, "ORIG_HEAD")
        if onto is None or before is None:
            return 0
        return show("post-rewrite", loaded, onto, before)
    except obeya_git.GitError as exc:
        return fail("post-rewrite", str(exc), 0)


def show(verb: str, gemba_config: config.Config, tip: str, before: str) -> int:
    """Print what the commits reachable from `tip` and not from `before` changed, when it lists a path."""
    context = sync.context_of(gemba_config)
    if context is None:
        return 0
    root = gemba_config.root
    came = obeya_git.read_range(root, tip, [before])
    own = [path for path in came.net if sync.classify(path, context.me, context.members).kind == "own"]
    patch = obeya_git.patch(root, came.bases[0] if came.bases else None, tip, own)
    report = sync.incoming(came.net, came.commits, came.merges, patch, context, pulled=True)
    if report.listed:
        print("\n".join([sync.came_in(verb, len(came.every)), *report.lines]), file=sys.stderr)
    return 0


def load(verb: str) -> config.Config | int:
    """The config of the obeya git runs the hook in, or the exit code of a hook that has nothing to check.

    No config, a config without a team, or a folder that is not the obeya's repository
    passes silently; a config that cannot be read is reported, refusing a push only.
    """
    try:
        root = config.find_root(Path.cwd())
    except config.ConfigError:
        return 0
    try:
        gemba_config = config.load(root=root)
    except config.ConfigError as exc:
        return fail(verb, str(exc), 1 if verb == "pre-push" else 0)
    if gemba_config.team is None or not obeya_git.has_repository(root):
        return 0
    return gemba_config


def refs(text: str) -> list[tuple[str, str, str]]:
    """The remote ref, the local id and the remote id of every pushed ref that sends a commit, branch deletions left
    out; an id that is not a full commit id is refused before it reaches git."""
    pushed = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 4:
            raise ValueError(f"'{line}' is not '<local ref> <local id> <remote ref> <remote id>'")
        _local_ref, local_id, remote_ref, remote_id = fields
        if not obeya_git.COMMIT_ID.match(local_id) or not obeya_git.COMMIT_ID.match(remote_id):
            raise ValueError(f"'{line}' does not name commits by their full ids")
        if set(local_id) != ZERO:
            pushed.append((remote_ref, local_id, remote_id))
    return pushed


def usage(parser: argparse.ArgumentParser) -> int:
    parser.print_help(sys.stderr)
    return 1


def fail(verb: str, message: str, code: int) -> int:
    print(f"gemba hook {verb}: {message}", file=sys.stderr)
    return code
