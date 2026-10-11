"""`gemba skills update`: write the built-in skills of the target, the tasks repo or a harness, per provider."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from gemba import config, harness, skills


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "skills",
        help="write the built-in skills into the tasks repo or a harness",
        description="Maintain the skills of Gemba in the skills folder of every agent provider of the target.",
    )
    parser.set_defaults(handler=lambda _args: usage(parser))
    verbs = parser.add_subparsers(dest="verb", metavar="<verb>")

    update = verbs.add_parser(
        "update",
        help="write missing skills and refresh outdated ones",
        description=(
            f"Write the built-in skills of the target under the skills folder of each of its agent providers. The "
            f"target is the nearest harness above the working directory, with the providers of its "
            f"{harness.CONFIG_FILENAME} and the harness skills, or else the tasks repo, with the providers of "
            "gemba.yaml and the tasks repo skills. A missing skill is written, one written by an older version is "
            "updated, one that matches is kept, and one edited by hand is kept and reported unless --force is given."
        ),
    )
    update.add_argument(
        "--check",
        action="store_true",
        help="print the state of every skill, write nothing, and exit 1 unless every skill is unchanged",
    )
    update.add_argument("--force", action="store_true", help="overwrite skills edited by hand")
    update.add_argument(
        "--root",
        type=Path,
        help=f"target root, a tasks repo or a harness (default: walk up to the nearest {harness.CONFIG_FILENAME} "
        f"or {config.CONFIG_FILENAME})",
    )
    update.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        root, providers, scope = target(args.root)
    except (config.ConfigError, harness.HarnessError) as exc:
        return fail(str(exc))

    actions = skills.plan(root, providers, version("gemba-cli"), scope)
    if args.check:
        for action in actions:
            print(f"{action.state} {action.path}")
        return 0 if all(action.state == "unchanged" for action in actions) else 1

    for action in actions:
        outcome = action.outcome(args.force)
        if outcome != "kept":
            path = root / action.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(action.content, encoding="utf-8", newline="\n")
        hint = " (edited by hand; --force overwrites it)" if action.state == "edited" and outcome == "kept" else ""
        print(f"{outcome} {action.path}{hint}")
    return 0


def target(given: Path | None) -> tuple[Path, tuple[str, ...], skills.Target]:
    """The root to write under, its agent providers and its kind: a harness first, else the tasks repo."""
    if given is not None and (given / harness.CONFIG_FILENAME).is_file():
        return harness_target(given.resolve())
    if given is None:
        try:
            found = harness.find_root(Path.cwd())
        except harness.HarnessError:
            pass
        else:
            return harness_target(found)
    gemba_config = config.load(root=given)
    if gemba_config.agent_providers is None:
        raise config.ConfigError(
            f"no agent providers declared: add agent_providers to {config.CONFIG_FILENAME} "
            f"(known providers: {', '.join(skills.PROVIDERS)})"
        )
    return gemba_config.root, gemba_config.agent_providers, "repo"


def harness_target(root: Path) -> tuple[Path, tuple[str, ...], skills.Target]:
    return root, harness.read_config(root, list(skills.PROVIDERS)).agent_providers, "harness"


def usage(parser: argparse.ArgumentParser) -> int:
    parser.print_help(sys.stderr)
    return 1


def fail(message: str) -> int:
    print(f"gemba skills update: {message}", file=sys.stderr)
    return 1
