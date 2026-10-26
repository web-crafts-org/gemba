"""The layout of an obeya as `gemba init` creates it, and the rules of its convergence and its refusals, the git
hooks of a team included."""

import re
from collections.abc import Sequence
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Literal

from gemba import config, skills, tasks

GITIGNORE = ".gitignore"
# The lines of the .gitignore that keep out of the obeya the harnesses, each a git repository of its own, the
# personal config, private to the clone, and the draft of an update that a refused record leaves at the root. The first
# two are unanchored, since each only exists at the root. The third is anchored: a person may keep an update.md of
# their own elsewhere in the obeya, and only the draft at the root must stay out of the history.
IGNORED_LINES = ("harnesses/", config.LOCAL_FILENAME, "/update.md")
GITATTRIBUTES = ".gitattributes"
# The lines of the .gitattributes that keep LF in the files gemba owns, whatever core.autocrlf says; the scope
# is those files, not `*`, so that an asset a person keeps in the obeya is never renormalized.
GITATTRIBUTES_LINES = ("*.md text eol=lf", "*.yaml text eol=lf")
# The token of the config template that the selected providers replace, as a flow list.
TEMPLATE_PROVIDERS_TOKEN = "__PROVIDERS__"
GITKEEP = PurePosixPath(tasks.TASKS_DIR, tasks.GITKEEP).as_posix()
# The last line of the output of init, whatever it wrote.
NEXT_STEP = "next step: open this obeya with your agent and ask it to configure gemba (the gemba-init skill)"
# The git hooks of a team, in the order init reports them: each script runs `gemba hook` with its own name.
HOOKS = ("pre-push", "post-merge", "post-rewrite")
# The second line of every hook script gemba writes, by which init tells its own scripts from those of another tool.
HOOK_MARKER = "# Written by gemba init for the git hooks of a team (git_hooks); gemba init removes it."
# What a file of the hooks folder is to init: none, the script of this version, a script of an earlier version, a
# script of another tool that runs `gemba hook` with its name, or a script of another tool.
HookState = Literal["missing", "current", "earlier", "chained", "other"]
# What init does with a hook, or `refused` when it may neither write it nor keep it.
HookAction = Literal["written", "updated", "kept", "removed", "refused"]


def render_config(providers: Sequence[str]) -> str:
    """The `gemba.yaml` init writes: the template asset with `providers` as a flow list."""
    template = (resources.files("gemba") / "assets" / "init" / config.CONFIG_FILENAME).read_text(encoding="utf-8")
    return template.replace(TEMPLATE_PROVIDERS_TOKEN, f"[{', '.join(providers)}]")


def gitignore_text(existing: str | None) -> str | None:
    """The `.gitignore` to write given the one on disk, or None when it already holds every line.

    With no file, the lines; with a file that lacks any of them, the file with the missing
    lines appended after a final newline, in their order.
    """
    return _completed(existing, IGNORED_LINES)


def gitattributes_text(existing: str | None) -> str | None:
    """The `.gitattributes` to write given the one on disk, or None when it already holds both lines.

    With no file, the two lines; with a file that lacks one or both, the file with the missing
    lines appended after a final newline, in their order.
    """
    return _completed(existing, GITATTRIBUTES_LINES)


def _completed(existing: str | None, lines: Sequence[str]) -> str | None:
    """`existing` with every one of `lines` it lacks appended in order, `lines` alone for no file, or None."""
    if existing is None:
        return "".join(f"{line}\n" for line in lines)
    present = {line.strip() for line in existing.splitlines()}
    missing = [line for line in lines if line not in present]
    if not missing:
        return None
    separator = "\n" if existing and not existing.endswith("\n") else ""
    return f"{existing}{separator}" + "".join(f"{line}\n" for line in missing)


def hook_script(name: str) -> str:
    """The script init writes for the hook `name`: it hands git's arguments and standard input to `gemba hook`.

    Without `gemba` on PATH, the script says how to install it and how to skip the checks,
    then refuses the push for `pre-push` and lets git go on for the other two.
    """
    status = 1 if name == "pre-push" else 0
    return (
        "#!/bin/sh\n"
        f"{HOOK_MARKER}\n"
        "if ! command -v gemba >/dev/null 2>&1; then\n"
        f'  echo "gemba hook {name}: gemba is not on PATH: install it with uv tool install gemba-cli; '
        'git push --no-verify skips these checks" >&2\n'
        f"  exit {status}\n"
        "fi\n"
        f'exec gemba hook {name} "$@"\n'
    )


def hook_state(name: str, text: str | None) -> HookState:
    """What the file of the hook `name` is, given its text, or None when there is no such file."""
    if text is None:
        return "missing"
    if text == hook_script(name):
        return "current"
    lines = text.split("\n")
    if len(lines) > 1 and lines[1].strip() == HOOK_MARKER:
        return "earlier"
    if re.search(rf"^[^#\n]*\bgemba hook {re.escape(name)}(?![\w-])", text, re.MULTILINE):
        return "chained"
    return "other"


def hook_action(state: HookState, on: bool, redirected: bool) -> HookAction | None:
    """What init does with a hook in `state`, when the hooks are `on` or off for the clone, or None to leave it out.

    `redirected` says that `core.hooksPath` is set: init then writes and removes no hook, so
    while the hooks are on a hook there that does not run `gemba hook` is refused.
    """
    if not on:
        return "removed" if state in ("current", "earlier") and not redirected else None
    if state in ("current", "chained"):
        return "kept"
    if redirected or state == "other":
        return "refused"
    return "written" if state == "missing" else "updated"


def hook_problem(location: str, name: str, hooks_path: str | None = None) -> str:
    """Why init refuses the hook `name` at `location`, and the two ways out; `hooks_path` is the value of
    `core.hooksPath` when it is set."""
    ways_out = (
        f'run gemba hook {name} "$@" from {"it" if hooks_path is None else location}, '
        f"or turn the hooks off for this clone with git_hooks: false in {config.LOCAL_FILENAME}"
    )
    if hooks_path is None:
        return f"{location} is a hook gemba did not write: {ways_out}"
    return f"core.hooksPath is set to {hooks_path}, where gemba writes no hook: {ways_out}"


def nested_problem(target: Path, found_root: Path) -> str:
    """Why `target` may not become an obeya: a strict ancestor, `found_root`, already is one."""
    return f"{target} is inside the obeya {found_root}: an obeya is never created inside another one"


def providers_problem(given: Sequence[str]) -> list[str]:
    """Every unknown identifier of `--providers` and every identifier it repeats, each once."""
    problems = []
    seen: set[str] = set()
    reported: set[str] = set()
    for provider in given:
        if provider in reported:
            continue
        if provider not in skills.PROVIDERS:
            problems.append(f"unknown provider '{provider}' {_known()}")
            reported.add(provider)
        elif provider in seen:
            problems.append(f"provider '{provider}' is listed more than once {_known()}")
            reported.add(provider)
        seen.add(provider)
    return problems


def conflict_problem() -> str:
    """Why `--providers` is refused once the obeya holds a config."""
    return (
        f"--providers is refused: {config.CONFIG_FILENAME} already declares the agent providers and is edited by "
        "hand, never by gemba init"
    )


def no_providers_problem() -> str:
    """Why the skills of an existing config that declares no providers cannot be written."""
    return f"no agent providers declared: add agent_providers to {config.CONFIG_FILENAME} {_known()}"


def _known() -> str:
    return f"(known providers: {', '.join(skills.PROVIDERS)})"
