"""`gemba archive`: move tasks that went cold into the archive folder of their workstream."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path, PurePosixPath

from gemba import config, harness, tasks, team


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "archive",
        help="move tasks into the archive folder of their workstream",
        description=(
            f"Move the file of each task, unchanged, into {tasks.TASKS_DIR}/<workstream>/{tasks.ARCHIVE_DIR}/, or "
            f"{tasks.TASKS_DIR}/<member>/<workstream>/{tasks.ARCHIVE_DIR}/ in an obeya with a team, whatever its "
            "status. Each ref is handled on its own and gets one line, archived or not archived; "
            "the exit code is 1 when any ref was refused. A task whose harness folder exists is refused. "
            "Nothing is committed."
        ),
    )
    parser.add_argument(
        "refs", nargs="+", metavar="ref", help="ref of a task, such as SUP-1; give several to archive them"
    )
    parser.add_argument("--root", type=Path, help="obeya root (default: walk up to the nearest gemba.yaml)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        print(f"gemba archive: {exc}", file=sys.stderr)
        return 1

    root = gemba_config.root
    refused = False
    for ref in args.refs:
        try:
            task = tasks.find_by_ref(root, gemba_config.workstreams, ref, gemba_config.members)
        except tasks.TaskError as exc:
            problem = f"cannot be resolved: {exc}"
        else:
            if task is None:
                problem = f"is the ref of no task under {tasks.TASKS_DIR}/, archives included"
            else:
                folder = harness.harness_path(root, task.workstream, PurePosixPath(task.path).stem)
                destination = tasks.archive_destination(task)
                problem = tasks.archive_problem(
                    task,
                    folder.relative_to(root).as_posix() if folder.exists() else None,
                    (root / destination).exists(),
                )
                guard = team.write_problems(gemba_config.team, gemba_config.me, task, config.LOCAL_FILENAME)
                if problem is None and not guard:
                    (root / destination).parent.mkdir(parents=True, exist_ok=True)
                    (root / task.path).rename(root / destination)
                    print(f"archived: {destination}")
                    continue
                # Each refusal of the guard is phrased after the ref, as the line of a ref is.
                refusals = [f"{ref} {problem}"] if problem else []
                refusals += [line if line.startswith(f"{ref} ") else f"{ref}: {line}" for line in guard]
                refused = True
                print(f"not archived: {'; '.join(refusals)}")
                continue
        refused = True
        print(f"not archived: {ref} {problem}")
    return 1 if refused else 0
