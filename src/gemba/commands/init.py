"""`gemba init`: make a folder an obeya, writing only what is missing."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path

from gemba import config, obeya, skills


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "init",
        help="make a folder an obeya",
        description=(
            f"Make the folder an obeya: {config.CONFIG_FILENAME} with the one workstream default, the "
            f"{obeya.GITKEEP} file, the {', '.join(obeya.IGNORED_LINES)} lines of {obeya.GITIGNORE}, the LF lines of "
            f"{obeya.GITATTRIBUTES} and the obeya skills under the skills folder of every agent provider. "
            "Only what is missing is written: an existing "
            f"{config.CONFIG_FILENAME} is never rewritten and gives the providers, and a skill already on disk is "
            "kept. Nothing is asked and no git is run."
        ),
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="folder to initialize, created when missing (default: the working one)"
    )
    parser.add_argument(
        "--providers",
        metavar="ID[,ID...]",
        help=f"comma-separated agent providers to declare in a new {config.CONFIG_FILENAME} "
        f"(default: every known provider, {', '.join(skills.PROVIDERS)})",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    config_path = target / config.CONFIG_FILENAME
    exists = config_path.is_file()

    errors = []
    try:
        found = config.find_root(target.parent)
    except config.ConfigError:
        pass
    else:
        errors.append(obeya.nested_problem(target, found))
    if target.exists() and not target.is_dir():
        errors.append(f"{target} is not a folder")
    selected = list(skills.PROVIDERS)
    if args.providers is not None and exists:
        errors.append(obeya.conflict_problem())
    elif args.providers is not None:
        selected = [provider.strip() for provider in args.providers.split(",")]
        errors.extend(obeya.providers_problem(selected))
    if errors:
        return fail("nothing written:\n" + "\n".join(f"- {error}" for error in errors))

    providers: tuple[str, ...] = tuple(selected)
    if exists:
        try:
            gemba_config = config.load(root=target)
        except config.ConfigError as exc:
            return fail(str(exc))
        if gemba_config.agent_providers is None:
            return fail(obeya.no_providers_problem())
        providers = gemba_config.agent_providers

    target.mkdir(parents=True, exist_ok=True)
    if exists:
        report("kept", config.CONFIG_FILENAME)
    else:
        config_path.write_text(obeya.render_config(providers), encoding="utf-8", newline="\n")
        report("written", config.CONFIG_FILENAME)

    converge(target / obeya.GITIGNORE, obeya.gitignore_text)
    converge(target / obeya.GITATTRIBUTES, obeya.gitattributes_text)

    gitkeep = target / obeya.GITKEEP
    if gitkeep.is_file():
        report("kept", obeya.GITKEEP)
    else:
        gitkeep.parent.mkdir(parents=True, exist_ok=True)
        gitkeep.touch()
        report("written", obeya.GITKEEP)

    # A skill on disk is kept whatever its state: refreshing it is the work of gemba skills update.
    for action in skills.plan(target, providers, version("gemba-cli"), "obeya"):
        if action.state == "missing":
            path = target / action.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(action.content, encoding="utf-8", newline="\n")
            report("written", action.path)
        else:
            report("kept", action.path)

    print(obeya.NEXT_STEP)
    return 0


def converge(path: Path, text_for: Callable[[str | None], str | None]) -> None:
    """Write the file at `path` as `text_for` renders it from the one on disk, and report what happened.

    The file is read and written with its bytes kept whatever they are, since a person edits it by hand.
    """
    existing = path.read_bytes().decode("utf-8", errors="surrogateescape") if path.is_file() else None
    text = text_for(existing)
    if text is not None:
        path.write_bytes(text.encode("utf-8", errors="surrogateescape"))
    report("kept" if text is None else "written" if existing is None else "updated", path.name)


def report(outcome: str, path: str) -> None:
    print(f"{outcome} {path}")


def fail(message: str) -> int:
    print(f"gemba init: {message}", file=sys.stderr)
    return 1
