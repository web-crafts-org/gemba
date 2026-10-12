"""Gemba config: discovery, loading and validation; field declarations are delegated to `metadata`."""

import re
import shlex
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from gemba import metadata, platform, skills
from gemba.metadata import Field
from gemba.worktree import DEFAULT_BRANCH_PREFIX

CONFIG_FILENAME = "gemba.yaml"

WORKSTREAM_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PREFIX_PATTERN = re.compile(r"^[A-Z]+$")
# Processes whose block is validated, at the top level and in every workstream, each with the
# verbs of its group, or None for a process that is one verb; any other block is left to later sprints.
PROCESSES: dict[str, tuple[str, ...] | None] = {
    "create": None,
    "list": None,
    "record": None,
    "report": None,
    "mark": None,
    "archive": None,
    "set": None,
    "harness": ("launch", "note", "resolve", "remove"),
    "worktree": ("add", "list", "remove"),
}
# Key of the harness block that is not a verb: the text launch renders into the guide.
GUIDE_KEY = "guide"
# Keys a group block takes besides its verbs; only the harness renders a guide.
GROUP_KEYS: dict[str, tuple[str, ...]] = {"harness": (GUIDE_KEY,)}


class ConfigError(Exception):
    """The gemba config is missing or invalid; nothing may be written."""


@dataclass(frozen=True)
class Workstream:
    id: str
    prefix: str
    description: str
    metadata: tuple[Field, ...]
    processes: dict[str, object]


@dataclass(frozen=True)
class Block:
    """The effective block of a process or of a verb of a group for one workstream, both levels combined."""

    context: str | None
    rules: tuple[str, ...]


@dataclass(frozen=True)
class Guide:
    """The two `harness.guide` texts of one workstream, as launch renders them under their own headings."""

    organization: str | None
    workstream: str | None


@dataclass(frozen=True)
class Ide:
    """The command that opens a folder in the IDE: the executable, its arguments, and the declaration as written."""

    command: str
    args: tuple[str, ...]
    declared: str | dict[str, object]

    @property
    def line(self) -> str:
        """The command line as declared, before the harness path: what launch prints and names."""
        return " ".join([self.command, *self.args])


@dataclass(frozen=True)
class Config:
    root: Path
    default_workstream: str
    workstreams: dict[str, Workstream]
    metadata: tuple[Field, ...]
    agent_providers: tuple[str, ...] | None = None
    ide: Ide | None = None
    organization: str | None = None
    repos_dir: str | None = None
    branch_prefix: str = DEFAULT_BRANCH_PREFIX
    # The base blocks: the top-level entries named after a process, shared by every workstream.
    processes: dict[str, object] = field(default_factory=dict)

    def effective_schema(self, workstream_id: str) -> list[Field]:
        """Union by name of the base and workstream fields; the workstream declaration wins."""
        return metadata.effective(self.metadata, self.workstreams[workstream_id].metadata)

    def types(self) -> dict[str, str]:
        """Every field name declared anywhere in the config, base list first, mapped to its one type."""
        return metadata.types(self.metadata, _lists(self.workstreams))

    def effective_block(self, workstream_id: str, process: str, verb: str | None = None) -> Block:
        """The base block followed by the workstream's: both contexts one empty line apart, every base rule first.

        `verb` names the verb of a group and must be None for a process that is one verb. A
        context that is blank counts as not declared.
        """
        verbs = PROCESSES[process]
        if (verbs is None) != (verb is None) or (verbs is not None and verb not in verbs):
            raise ValueError(f"'{process}' has no block for verb {verb!r}")
        levels = [
            _block(self.processes, process, verb),
            _block(self.workstreams[workstream_id].processes, process, verb),
        ]
        contexts = [text for level in levels if isinstance(text := level.get("context"), str) and text.strip()]
        rules = [rule for level in levels for rule in _rules(level)]
        return Block(context=_joined(contexts), rules=tuple(rules))

    def effective_guide(self, workstream_id: str) -> Guide:
        """The base `harness.guide` and the workstream's, each None when its level declares none."""
        return Guide(organization=guide(self.processes), workstream=guide(self.workstreams[workstream_id].processes))

    def effective_processes(self, workstream_id: str) -> dict[str, object]:
        """Every process and every verb of a group with its effective block, and the harness guide, as plain data."""
        entries: dict[str, object] = {}
        for process, verbs in PROCESSES.items():
            if verbs is None:
                entries[process] = _plain(self.effective_block(workstream_id, process))
                continue
            entry: dict[str, object] = {}
            if GUIDE_KEY in GROUP_KEYS.get(process, ()):
                texts = self.effective_guide(workstream_id)
                entry[GUIDE_KEY] = {"organization": texts.organization, "workstream": texts.workstream}
            for verb in verbs:
                entry[verb] = _plain(self.effective_block(workstream_id, process, verb))
            entries[process] = entry
        return entries


def _block(processes: Mapping[str, object], process: str, verb: str | None) -> Mapping[str, object]:
    """The block of a process, or of a verb of a group, at one level, empty when that level declares none."""
    block = processes.get(process)
    if verb is not None:
        block = block.get(verb) if isinstance(block, dict) else None
    return block if isinstance(block, dict) else {}


def _rules(block: Mapping[str, object]) -> list[str]:
    rules = block.get("rules")
    return [rule for rule in rules if isinstance(rule, str)] if isinstance(rules, list) else []


def _joined(contexts: list[str]) -> str | None:
    """The contexts of both levels with one empty line between them, the one given alone, or None."""
    if not contexts:
        return None
    if len(contexts) == 1:
        return contexts[0]
    base, own = contexts
    return base.rstrip("\n") + "\n\n" + own.lstrip("\n")


def _plain(block: Block) -> dict[str, object]:
    return {"context": block.context, "rules": list(block.rules)}


def guide(processes: Mapping[str, object]) -> str | None:
    """The `harness.guide` text of one level, the top level or a workstream, or None when it declares none."""
    block = processes.get("harness")
    text = block.get(GUIDE_KEY) if isinstance(block, dict) else None
    return text if isinstance(text, str) else None


def find_root(start: Path | str) -> Path:
    """Return the nearest folder at or above `start` that contains the gemba config."""
    start = Path(start).resolve()
    for folder in (start, *start.parents):
        if (folder / CONFIG_FILENAME).is_file():
            return folder
    raise ConfigError(f"no gemba config found: no {CONFIG_FILENAME} in {start} or any parent folder")


def load(root: Path | str | None = None, cwd: Path | str | None = None) -> Config:
    """Load and validate the config at `root`, or discover it by walking up from `cwd`."""
    if root is None:
        root = find_root(cwd or Path.cwd())
    else:
        root = Path(root).resolve()
        if not (root / CONFIG_FILENAME).is_file():
            raise ConfigError(f"no gemba config found: no {CONFIG_FILENAME} in {root}")

    path = root / CONFIG_FILENAME
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: malformed YAML: {exc}") from exc

    try:
        return _parse(root, data)
    except ConfigError as exc:
        raise ConfigError(f"invalid gemba config {path}: {exc}") from None


def _parse(root: Path, data: object) -> Config:
    if not isinstance(data, dict):
        raise ConfigError("the file must be a map with default_workstream and workstreams")

    base = _parse_fields(data.get("metadata"), metadata.BASE_LIST)
    _check_processes(data, "top level")

    catalogue = data.get("workstreams")
    if not isinstance(catalogue, dict) or not catalogue:
        raise ConfigError("workstreams must be a non-empty map keyed by workstream identifier")
    workstreams = {}
    owners = {}
    for workstream_id, block in catalogue.items():
        workstream = _parse_workstream(workstream_id, block)
        if workstream.prefix in owners:
            raise ConfigError(
                f"workstreams '{owners[workstream.prefix]}' and '{workstream_id}' "
                f"declare the same prefix '{workstream.prefix}'"
            )
        owners[workstream.prefix] = workstream_id
        workstreams[workstream_id] = workstream

    default = data.get("default_workstream")
    if default is None:
        raise ConfigError("default_workstream is missing")
    if default not in workstreams:
        raise ConfigError(
            f"default_workstream '{default}' is not in the workstream catalogue (valid: {', '.join(workstreams)})"
        )
    try:
        metadata.types(base, _lists(workstreams))
    except metadata.MetadataError as exc:
        raise ConfigError(str(exc)) from None

    return Config(
        root=root,
        default_workstream=default,
        workstreams=workstreams,
        metadata=base,
        agent_providers=_parse_providers(data.get("agent_providers")),
        ide=_parse_ide(data.get("ide")),
        organization=_parse_name("organization", data.get("organization")),
        repos_dir=_parse_repos_dir(data.get("repos_dir")),
        branch_prefix=_parse_name("branch_prefix", data.get("branch_prefix")) or DEFAULT_BRANCH_PREFIX,
        processes={key: value for key, value in data.items() if key in PROCESSES},
    )


def _parse_name(key: str, declaration: object) -> str | None:
    """A kebab-case name that becomes a segment of a branch, or None when the config declares none."""
    if declaration is None:
        return None
    if not isinstance(declaration, str) or not WORKSTREAM_ID_PATTERN.match(declaration):
        raise ConfigError(f"{key} must be kebab-case (lowercase letters, digits and single hyphens)")
    return declaration


def _parse_repos_dir(declaration: object) -> str | None:
    """The folder of the repositories a run may check out, as declared, or None when the config declares none."""
    if declaration is None:
        return None
    if not isinstance(declaration, str) or not declaration.strip():
        raise ConfigError(
            "repos_dir must be a non-empty string naming the folder of the repositories: "
            "absolute, starting with ~, or relative to the tasks repo root"
        )
    return declaration


def _parse_ide(declaration: object) -> Ide | None:
    """The command that opens a folder in the IDE, or None when the config declares none.

    A string is split as a POSIX shell would, on every platform, so a path holding spaces or
    backslashes goes between quotes; a map holds `command` and optionally `args`.
    """
    if declaration is None:
        return None
    shape = "ide must be a non-empty string, the command that opens a folder in the IDE, or a map with command and args"
    if isinstance(declaration, str):
        try:
            parts = shlex.split(declaration, posix=True)
        except ValueError as exc:
            raise ConfigError(f"{shape} (cannot split {declaration!r}: {exc})") from None
        if not parts or not parts[0]:
            raise ConfigError(shape)
        return Ide(command=parts[0], args=tuple(parts[1:]), declared=declaration)
    if not isinstance(declaration, dict):
        raise ConfigError(shape)
    command = declaration.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ConfigError("ide.command must be a non-empty string naming the executable that opens a folder in the IDE")
    args = declaration.get("args", [])
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise ConfigError("ide.args must be a list of strings, the arguments given before the harness path")
    declared = {str(key): value for key, value in declaration.items()}
    return Ide(command=command, args=tuple(args), declared=declared)


def _parse_providers(declaration: object) -> tuple[str, ...] | None:
    """The declared agent providers in order, or None when the config declares none."""
    if declaration is None:
        return None
    known = f"(known providers: {', '.join(skills.PROVIDERS)})"
    if not isinstance(declaration, list) or not declaration or not all(isinstance(item, str) for item in declaration):
        raise ConfigError(f"agent_providers must be a non-empty list of provider identifiers {known}")
    seen = set()
    for provider in declaration:
        if provider not in skills.PROVIDERS:
            raise ConfigError(f"agent_providers: unknown provider '{provider}' {known}")
        if provider in seen:
            raise ConfigError(f"agent_providers: provider '{provider}' is listed more than once {known}")
        seen.add(provider)
    return tuple(declaration)


def _parse_workstream(workstream_id: object, block: object) -> Workstream:
    where = f"workstream '{workstream_id}'"
    if not isinstance(workstream_id, str) or not WORKSTREAM_ID_PATTERN.match(workstream_id):
        raise ConfigError(f"{where}: identifier must be kebab-case (lowercase letters, digits and single hyphens)")
    if platform.is_reserved_name(workstream_id):
        raise ConfigError(f"{where}: identifier is reserved on Windows, where it could not be a folder name")
    if not isinstance(block, dict):
        raise ConfigError(f"{where}: must be a map with prefix and description")

    prefix = block.get("prefix")
    if not isinstance(prefix, str) or not PREFIX_PATTERN.match(prefix):
        raise ConfigError(
            f"{where}: prefix must be one or more uppercase ASCII letters (got {prefix!r}; "
            "quote it if YAML reads it as another type)"
        )

    description = block.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ConfigError(f"{where}: description is missing or empty")

    fields = _parse_fields(block.get("metadata"), _list_name(workstream_id))
    _check_processes(block, where)

    processes = {key: value for key, value in block.items() if key not in ("prefix", "description", "metadata")}
    return Workstream(
        id=workstream_id,
        prefix=prefix,
        description=description.strip(),
        metadata=fields,
        processes=processes,
    )


def _parse_fields(declarations: object, where: str) -> tuple[Field, ...]:
    try:
        return metadata.parse_fields(declarations, where)
    except metadata.MetadataError as exc:
        raise ConfigError(str(exc)) from None


def _list_name(workstream_id: str) -> str:
    """How a refusal names the metadata list of a workstream."""
    return f"workstream '{workstream_id}' metadata"


def _lists(workstreams: dict[str, Workstream]) -> dict[str, tuple[Field, ...]]:
    """The metadata list of every workstream, keyed by the name a refusal gives it."""
    return {_list_name(workstream.id): workstream.metadata for workstream in workstreams.values()}


def _check_processes(block: dict[object, object], where: str) -> None:
    """Every process block of one level, the top level or a workstream, each validated by its shape."""
    for process, verbs in PROCESSES.items():
        if verbs is None:
            _check_process_block(process, block.get(process), where)
        else:
            _check_group_block(process, verbs, GROUP_KEYS.get(process, ()), block.get(process), where)


def _check_group_block(group: str, verbs: tuple[str, ...], extra: tuple[str, ...], block: object, where: str) -> None:
    """A group block holds one verb block per verb and the `extra` keys it allows; any other key is refused."""
    if block is None:
        return
    allowed = (*extra, *verbs)
    if not isinstance(block, dict):
        raise ConfigError(f"{where}: {group} must be a map (allowed keys: {', '.join(allowed)})")
    for key, value in block.items():
        if key == GUIDE_KEY and key in extra:
            if not isinstance(value, str) or not value.strip():
                raise ConfigError(f"{where}: {group}.{GUIDE_KEY} must be a non-empty string")
        elif key in verbs:
            _check_process_block(f"{group}.{key}", value, where)
        else:
            raise ConfigError(f"{where}: {group}.{key} is not a key of {group} (allowed: {', '.join(allowed)})")


def _check_process_block(process: str, block: object, where: str) -> None:
    if block is None:
        return
    if not isinstance(block, dict):
        raise ConfigError(f"{where}: {process} must be a map with rules and context")
    rules = block.get("rules")
    if rules is not None and (
        not isinstance(rules, list) or not all(isinstance(rule, str) and rule.strip() for rule in rules)
    ):
        raise ConfigError(f"{where}: {process}.rules must be a list of non-empty strings")
    context = block.get("context")
    if context is not None and not isinstance(context, str):
        raise ConfigError(f"{where}: {process}.context must be a string")
