"""`gemba config check` and `gemba config show`: validate both config files, then summarize or resolve them."""

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
            f"Read the config of the obeya, the shared {config.CONFIG_FILENAME} and the personal "
            f"{config.LOCAL_FILENAME} beside it, without ever writing them: both files are edited by hand."
        ),
    )
    parser.set_defaults(handler=lambda _args: usage(parser))
    verbs = parser.add_subparsers(dest="verb", metavar="<verb>")

    check = verbs.add_parser(
        "check",
        help="validate the config and summarize it",
        description=(
            f"Validate {config.CONFIG_FILENAME} and {config.LOCAL_FILENAME}, when it exists, as every command does "
            "before acting. A valid config is summarized with its workstreams and prefixes, its default workstream, "
            "the members of its team and the member of the clone when it declares a team, its agent providers and "
            "the providers the personal config declares for a launch; an invalid one is "
            "reported with every problem of both files, each with the path of its file, and the command exits 1."
        ),
    )
    check.add_argument("--root", type=Path, help="obeya root (default: walk up to the nearest gemba.yaml)")
    check.set_defaults(handler=run_check)

    show = verbs.add_parser(
        "show",
        help="print the effective config as one JSON document",
        description=(
            "Validate the config as check does and print the effective config, merged from both files, as one JSON "
            "object: the top-level keys, the defaults applied and null where nothing is declared, "
            "`harness_providers`, the providers a launch writes the harness for, in an obeya with a team `team`, "
            "each member with its initials and whether it is active, and `me`, and `workstreams`, in catalogue "
            "order, each with its prefix, its description, its effective metadata schema and, under `processes`, "
            "the effective block of every process and verb: the shared base block, the workstream's, then the "
            "personal ones."
        ),
    )
    show.add_argument("--workstream", metavar="ID", help="workstream identifier from gemba.yaml (default: every one)")
    show.add_argument("--root", type=Path, help="obeya root (default: walk up to the nearest gemba.yaml)")
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
    if gemba_config.personal:
        print(f"{config.LOCAL_FILENAME} is valid")
    print(f"workstreams: {workstreams}")
    print(f"default workstream: {gemba_config.default_workstream}")
    if gemba_config.team is not None:
        members = ", ".join(
            f"{member.id} ({member.initials})" if member.active else f"{member.id} ({member.initials}, inactive)"
            for member in gemba_config.team.values()
        )
        print(f"team: {members}")
        if gemba_config.me is not None:
            print(f"me: {gemba_config.me}")
    print(f"agent providers: {providers}")
    if gemba_config.personal_providers is not None:
        print(f"harness providers: {', '.join(gemba_config.personal_providers)}")
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
    document: dict[str, object] = {
        "obeya": gemba_config.obeya,
        "branch_prefix": gemba_config.branch_prefix,
        "repos_dir": gemba_config.repos_dir,
        "ide": None if gemba_config.ide is None else gemba_config.ide.declared,
        "agent_providers": None if gemba_config.agent_providers is None else list(gemba_config.agent_providers),
        "harness_providers": None if gemba_config.harness_providers is None else list(gemba_config.harness_providers),
        "default_workstream": gemba_config.default_workstream,
    }
    # Only an obeya with a team shows the team, as only its listing records carry an owner.
    if gemba_config.team is not None:
        document["team"] = {
            member.id: {"initials": member.initials, "active": member.active} for member in gemba_config.team.values()
        }
        document["me"] = gemba_config.me
    document["workstreams"] = [workstream(gemba_config, workstream_id) for workstream_id in shown]
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
