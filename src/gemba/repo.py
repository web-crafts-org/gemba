"""The layout of a tasks repo as `gemba init` creates it, and the rules of its convergence and its refusals."""

from collections.abc import Sequence
from importlib import resources
from pathlib import Path, PurePosixPath

from gemba import config, skills, tasks

GITIGNORE = ".gitignore"
# The lines of the .gitignore that keep out of the tasks repo the harnesses, each a git repository of its own, the
# personal config, private to the clone, and the draft of an update that a refused record leaves at the root. The first
# two are unanchored, since each only exists at the root. The third is anchored: a person may keep an update.md of
# their own elsewhere in the tasks repo, and only the draft at the root must stay out of the history.
IGNORED_LINES = ("harnesses/", config.LOCAL_FILENAME, "/update.md")
GITATTRIBUTES = ".gitattributes"
# The lines of the .gitattributes that keep LF in the files gemba owns, whatever core.autocrlf says; the scope
# is those files, not `*`, so that an asset a person keeps in the tasks repo is never renormalized.
GITATTRIBUTES_LINES = ("*.md text eol=lf", "*.yaml text eol=lf")
# The token of the config template that the selected providers replace, as a flow list.
TEMPLATE_PROVIDERS_TOKEN = "__PROVIDERS__"
GITKEEP = PurePosixPath(tasks.TASKS_DIR, tasks.GITKEEP).as_posix()
# The last line of the output of init, whatever it wrote.
NEXT_STEP = "next step: open this tasks repo with your agent and ask it to configure gemba (the gemba-init skill)"


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


def nested_problem(target: Path, found_root: Path) -> str:
    """Why `target` may not become a tasks repo: a strict ancestor, `found_root`, already is one."""
    return f"{target} is inside the tasks repo {found_root}: a tasks repo is never created inside another one"


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
    """Why `--providers` is refused once the tasks repo holds a config."""
    return (
        f"--providers is refused: {config.CONFIG_FILENAME} already declares the agent providers and is edited by "
        "hand, never by gemba init"
    )


def no_providers_problem() -> str:
    """Why the skills of an existing config that declares no providers cannot be written."""
    return f"no agent providers declared: add agent_providers to {config.CONFIG_FILENAME} {_known()}"


def _known() -> str:
    return f"(known providers: {', '.join(skills.PROVIDERS)})"
