"""`gemba init`: make a folder a tasks repo, writing only what is missing."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from gemba import config, repo, skills


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "init",
        help="make a folder a tasks repo",
        description=(
            f"Make the folder a tasks repo: {config.CONFIG_FILENAME} with the one workstream default, the "
            f"{repo.GITKEEP} file, the {repo.IGNORED_LINE} line of {repo.GITIGNORE} and the tasks repo skills "
            "under the skills folder of every agent provider. Only what is missing is written: an existing "
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
        errors.append(repo.nested_problem(target, found))
    if target.exists() and not target.is_dir():
        errors.append(f"{target} is not a folder")
    selected = list(skills.PROVIDERS)
    if args.providers is not None and exists:
        errors.append(repo.conflict_problem())
    elif args.providers is not None:
        selected = [provider.strip() for provider in args.providers.split(",")]
        errors.extend(repo.providers_problem(selected))
    if errors:
        return fail("nothing written:\n" + "\n".join(f"- {error}" for error in errors))

    providers: tuple[str, ...] = tuple(selected)
    if exists:
        try:
            gemba_config = config.load(root=target)
        except config.ConfigError as exc:
            return fail(str(exc))
        if gemba_config.agent_providers is None:
            return fail(repo.no_providers_problem())
        providers = gemba_config.agent_providers

    target.mkdir(parents=True, exist_ok=True)
    if exists:
        report("kept", config.CONFIG_FILENAME)
    else:
        config_path.write_text(repo.render_config(providers), encoding="utf-8", newline="\n")
        report("written", config.CONFIG_FILENAME)

    gitignore = target / repo.GITIGNORE
    existing = gitignore.read_bytes().decode("utf-8", errors="surrogateescape") if gitignore.is_file() else None
    text = repo.gitignore_text(existing)
    if text is not None:
        gitignore.write_bytes(text.encode("utf-8", errors="surrogateescape"))
    report("kept" if text is None else "written" if existing is None else "updated", repo.GITIGNORE)

    gitkeep = target / repo.GITKEEP
    if gitkeep.is_file():
        report("kept", repo.GITKEEP)
    else:
        gitkeep.parent.mkdir(parents=True, exist_ok=True)
        gitkeep.touch()
        report("written", repo.GITKEEP)

    # A skill on disk is kept whatever its state: refreshing it is the work of gemba skills update.
    for action in skills.plan(target, providers, version("gemba-cli"), "repo"):
        if action.state == "missing":
            path = target / action.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(action.content, encoding="utf-8", newline="\n")
            report("written", action.path)
        else:
            report("kept", action.path)

    print(repo.NEXT_STEP)
    return 0


def report(outcome: str, path: str) -> None:
    print(f"{outcome} {path}")


def fail(message: str) -> int:
    print(f"gemba init: {message}", file=sys.stderr)
    return 1
