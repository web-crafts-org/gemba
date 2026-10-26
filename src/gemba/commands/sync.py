"""`gemba sync`: compare the branch of an obeya with a team with its upstream as last fetched, and report what a pull
would bring, what a push would send and the verdict of the push; it fetches, pulls, pushes and writes nothing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gemba import config, sync, team
from gemba.commands import obeya_git


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "sync",
        help="check the obeya of a team against its upstream before a pull and a push",
        description=(
            "Compare the branch checked out with its upstream as last fetched, in an obeya with a team: what a pull "
            "would bring to the tasks of the member of the clone, with its patch, and to the shared and private "
            "files; what a push would send, with every problem the pre-push hook reports and the shared files to "
            "confirm; the uncommitted changes, each as the member's own, another member's, private or shared; and "
            "whether the git hooks of the clone agree with git_hooks. The last line is the verdict of a push: "
            "nothing to push, ready, needs confirmation with the command that confirms it, or refused. It runs no "
            "fetch, no pull and no push, writes nothing, and exits 0 whatever the verdict."
        ),
    )
    parser.add_argument("--root", type=Path, help="obeya root (default: walk up to the nearest gemba.yaml)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail(str(exc))
    root = gemba_config.root
    problems = []
    if gemba_config.team is None:
        problems.append(f"sync needs a team: {config.CONFIG_FILENAME} declares none")
    elif gemba_config.me is None:
        problems.extend(team.write_problems(gemba_config.team, None, None, config.LOCAL_FILENAME))
    try:
        branch, upstream = None, None
        if not obeya_git.has_repository(root):
            problems.append(f"{root} is not a git repository: sync compares a branch of the obeya with its upstream")
        elif (branch := obeya_git.branch(root)) is None:
            problems.append("HEAD is detached: sync compares a branch of the obeya with its upstream")
        elif (upstream := obeya_git.upstream(root)) is None:
            problems.append(f"branch {branch} has no upstream")
        if problems:
            return fail("\n".join(problems) if len(problems) == 1 else "sync not done:\n" + _listed(problems))
        assert branch is not None and upstream is not None, "every failed check above appended a problem"
        return report(gemba_config, root, branch, upstream)
    except obeya_git.GitError as exc:
        return fail(str(exc))


def report(gemba_config: config.Config, root: Path, branch: str, upstream: str) -> int:
    """Print what comes in, what goes out and the verdict of a push, read from the clone as it is."""
    context = sync.context_of(gemba_config)
    assert context is not None, "run refuses an obeya without a team and a clone without me"
    tip = obeya_git.commit_id(root, "HEAD")
    remote = obeya_git.commit_id(root, "@{upstream}")
    if tip is None or remote is None:
        return fail(f"branch {branch} or its upstream {upstream} names no commit")

    coming = obeya_git.read_range(root, remote, [tip])
    own = [path for path in coming.net if sync.classify(path, context.me, context.members).kind == "own"]
    patch = obeya_git.patch(root, coming.bases[0] if coming.bases else None, remote, own)
    brought = sync.incoming(coming.net, coming.commits, coming.merges, patch, context, pulled=False)

    going = obeya_git.read_range(root, tip, [remote])
    files, paths = obeya_git.own_files(root, tip, context.me, going.net)
    verdict = sync.outgoing(going.net, going.commits, going.merges, files, paths, context, confirmed=False)

    hooks = sync.hooks_line(gemba_config.git_hooks, obeya_git.hook_states(root))
    lines = sync.report(
        branch,
        upstream,
        len(coming.every),
        brought,
        going.every,
        verdict,
        tip,
        obeya_git.uncommitted(root),
        context,
        hooks,
    )
    print("\n".join(lines))
    return 0


def _listed(problems: list[str]) -> str:
    return "\n".join(f"- {problem}" for problem in problems)


def fail(message: str) -> int:
    print(f"gemba sync: {message}", file=sys.stderr)
    return 1
