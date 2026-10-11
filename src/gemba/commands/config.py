"""`gemba config check` and `gemba config show`: validate gemba.yaml, then summarize or resolve it."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gemba import config
from gemba.commands import selection


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "config",
        help="check the gemba config or show it resolved",
        description=(
            f"Read {config.CONFIG_FILENAME}, the config of the tasks repo, without ever writing it: the file is "
            "edited by hand."
        ),
    )
    parser.set_defaults(handler=lambda _args: usage(parser))
    verbs = parser.add_subparsers(dest="verb", metavar="<verb>")

    check = verbs.add_parser(
        "check",
        help="validate the config and summarize it",
        description=(
            f"Validate {config.CONFIG_FILENAME} as every command does before acting. A valid config is summarized "
            "with its workstreams and prefixes, its default workstream and its agent providers; an invalid one is "
            "reported with the path of the file and the first problem, and the command exits 1."
        ),
    )
    check.add_argument("--root", type=Path, help="tasks repo root (default: walk up to the nearest gemba.yaml)")
    check.set_defaults(handler=run_check)

    show = verbs.add_parser(
        "show",
        help="print the effective config as one JSON document",
        description=(
            f"Validate {config.CONFIG_FILENAME} as check does and print the effective config as one JSON object: "
            "the top-level keys, the defaults applied and null where nothing is declared, and `workstreams`, in "
            "catalogue order, each with its prefix, its description, its effective metadata schema and, under "
            "`processes`, the effective block of every process and verb, the base block followed by the "
            "workstream's."
        ),
    )
    show.add_argument("--workstream", metavar="ID", help="workstream identifier from gemba.yaml (default: every one)")
    show.add_argument("--root", type=Path, help="tasks repo root (default: walk up to the nearest gemba.yaml)")
    show.set_defaults(handler=run_show)


def run_check(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail("check", str(exc))

    workstreams = ", ".join(
        f"{workstream.id} ({workstream.prefix})" for workstream in gemba_config.workstreams.values()
    )
    providers = ", ".join(gemba_config.agent_providers) if gemba_config.agent_providers else "none declared"
    print(f"{config.CONFIG_FILENAME} is valid")
    print(f"workstreams: {workstreams}")
    print(f"default workstream: {gemba_config.default_workstream}")
    print(f"agent providers: {providers}")
    return 0


def run_show(args: argparse.Namespace) -> int:
    try:
        gemba_config = config.load(root=args.root)
    except config.ConfigError as exc:
        return fail("show", str(exc))

    if args.workstream is not None and args.workstream not in gemba_config.workstreams:
        return fail(
            "show",
            f"unknown workstream '{args.workstream}' (valid workstreams: {', '.join(gemba_config.workstreams)})",
        )
    shown = [args.workstream] if args.workstream is not None else list(gemba_config.workstreams)
    document = {
        "organization": gemba_config.organization,
        "branch_prefix": gemba_config.branch_prefix,
        "repos_dir": gemba_config.repos_dir,
        "ide": gemba_config.ide,
        "agent_providers": None if gemba_config.agent_providers is None else list(gemba_config.agent_providers),
        "default_workstream": gemba_config.default_workstream,
        "workstreams": [workstream(gemba_config, workstream_id) for workstream_id in shown],
    }
    print(selection.dump(document))
    return 0


def workstream(gemba_config: config.Config, workstream_id: str) -> dict[str, object]:
    """The entry of one workstream in the document of show."""
    declared = gemba_config.workstreams[workstream_id]
    return {
        "id": declared.id,
        "prefix": declared.prefix,
        "description": declared.description,
        "metadata": [
            {"name": field.name, "type": field.type, "required": field.required, "description": field.description}
            for field in gemba_config.effective_schema(workstream_id)
        ],
        "processes": gemba_config.effective_processes(workstream_id),
    }


def usage(parser: argparse.ArgumentParser) -> int:
    parser.print_help(sys.stderr)
    return 1


def fail(verb: str, message: str) -> int:
    print(f"gemba config {verb}: {message}", file=sys.stderr)
    return 1
