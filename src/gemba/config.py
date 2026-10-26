"""Gemba config: discovery, loading and validation of its two files; field declarations are delegated to `metadata`.

The shared config, `gemba.yaml`, is committed with the obeya; the personal config,
`gemba.local.yaml`, is private to the clone and read beside it when it exists.
"""

import dataclasses
import re
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from gemba import metadata, platform, skills, team
from gemba.metadata import Field
from gemba.team import Member
from gemba.worktree import DEFAULT_BRANCH_PREFIX

CONFIG_FILENAME = "gemba.yaml"
# The personal config: beside the shared one at the root, private to the clone and ignored by git.
LOCAL_FILENAME = "gemba.local.yaml"

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
# The files each top-level key may be declared in: a key declared in another file is refused, naming the file it
# belongs in, and a key not listed here is ignored in both. The personal `workstreams` gives a workstream of the
# shared catalogue process blocks only.
LAYERS: dict[str, tuple[str, ...]] = {
    "workstreams": (CONFIG_FILENAME, LOCAL_FILENAME),
    "metadata": (CONFIG_FILENAME,),
    "default_workstream": (CONFIG_FILENAME,),
    "obeya": (CONFIG_FILENAME,),
    "team": (CONFIG_FILENAME,),
    "agent_providers": (CONFIG_FILENAME, LOCAL_FILENAME),
    "git_hooks": (CONFIG_FILENAME, LOCAL_FILENAME),
    "ide": (LOCAL_FILENAME,),
    "repos_dir": (LOCAL_FILENAME,),
    "branch_prefix": (LOCAL_FILENAME,),
    "me": (LOCAL_FILENAME,),
    **dict.fromkeys(PROCESSES, (CONFIG_FILENAME, LOCAL_FILENAME)),
}
# Top-level keys of an earlier version, each mapped to the key that replaced it: refused in either file, naming
# the new key and its file, and left out of parsing.
RENAMED_KEYS: dict[str, str] = {"organization": "obeya"}
# The keys that define a workstream of the catalogue, which only the shared config declares.
DEFINITION_KEYS = ("prefix", "description", "metadata")
# What each file is called in a refusal that sends a key to it.
LAYER_NAMES = {CONFIG_FILENAME: "the shared config", LOCAL_FILENAME: "the personal config"}


class ConfigError(Exception):
    """The gemba config is missing or invalid; nothing may be written.

    An invalid config carries its problems, each with the path of its file, and reads as
    `invalid gemba config:` followed by one `- <path>: <problem>` line per problem.
    """

    def __init__(self, message: str = "", problems: Sequence[tuple[Path, str]] = ()) -> None:
        self.problems = tuple(problems)
        if self.problems:
            message = "\n".join(["invalid gemba config:", *(f"- {path}: {problem}" for path, problem in self.problems)])
        super().__init__(message)


@dataclass(frozen=True)
class Workstream:
    id: str
    prefix: str
    description: str
    metadata: tuple[Field, ...]
    processes: dict[str, object]


@dataclass(frozen=True)
class Block:
    """The effective block of a process or of a verb of a group for one workstream, every level combined."""

    context: str | None
    rules: tuple[str, ...]


@dataclass(frozen=True)
class Guide:
    """The `harness.guide` texts of one workstream, as launch renders them under their own headings.

    `obeya` and `workstream` come from the shared config; `user` joins the base text
    of the personal config and the workstream's.
    """

    obeya: str | None
    workstream: str | None
    user: str | None = None


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
    # The providers of the shared config, which the skills of the obeya are written for.
    agent_providers: tuple[str, ...] | None = None
    ide: Ide | None = None
    obeya: str | None = None
    repos_dir: str | None = None
    branch_prefix: str = DEFAULT_BRANCH_PREFIX
    # The base blocks: the top-level entries named after a process, shared by every workstream.
    processes: dict[str, object] = field(default_factory=dict)
    # The providers of the personal config, which replace the shared ones for a launch from this clone only.
    personal_providers: tuple[str, ...] | None = None
    # The base blocks of the personal config, which follow the shared blocks in every effective block.
    personal_processes: dict[str, object] = field(default_factory=dict)
    # The process blocks the personal config gives workstreams of the catalogue, by workstream identifier.
    personal_workstreams: dict[str, dict[str, object]] = field(default_factory=dict)
    # Whether the root holds a personal config, an empty one included.
    personal: bool = False
    # The members of the team by folder name, in config order, or None in an obeya without a team.
    team: dict[str, Member] | None = None
    # The member the clone belongs to, as the personal config declares it, or None.
    me: str | None = None
    # Whether gemba's git hooks are on for the clone: the personal value when declared, else the shared one, else off.
    git_hooks: bool = False

    @property
    def members(self) -> tuple[str, ...] | None:
        """The folder names of the members of the team in config order, or None in an obeya without a team."""
        return None if self.team is None else tuple(self.team)

    @property
    def harness_providers(self) -> tuple[str, ...] | None:
        """The providers a launch writes the harness for: the personal list when declared, else the shared one."""
        return self.personal_providers if self.personal_providers is not None else self.agent_providers

    def effective_schema(self, workstream_id: str) -> list[Field]:
        """Union by name of the base and workstream fields; the workstream declaration wins."""
        return metadata.effective(self.metadata, self.workstreams[workstream_id].metadata)

    def types(self) -> dict[str, str]:
        """Every field name declared anywhere in the config, base list first, mapped to its one type."""
        return metadata.types(self.metadata, _lists(self.workstreams))

    def effective_block(self, workstream_id: str, process: str, verb: str | None = None) -> Block:
        """The four levels of a block in order, every context one empty line apart and every rule in that order.

        The levels are the shared base block, the workstream's block in the shared config, the
        personal base block and the workstream's block in the personal config, so a later rule
        wins a contradiction. `verb` names the verb of a group and must be None for a process
        that is one verb. A context that is blank counts as not declared.
        """
        verbs = PROCESSES[process]
        if (verbs is None) != (verb is None) or (verbs is not None and verb not in verbs):
            raise ValueError(f"'{process}' has no block for verb {verb!r}")
        levels = [
            _block(self.processes, process, verb),
            _block(self.workstreams[workstream_id].processes, process, verb),
            _block(self.personal_processes, process, verb),
            _block(self.personal_workstreams.get(workstream_id, {}), process, verb),
        ]
        contexts = [text for level in levels if isinstance(text := level.get("context"), str) and text.strip()]
        rules = [rule for level in levels for rule in _rules(level)]
        return Block(context=_joined(contexts), rules=tuple(rules))

    def effective_guide(self, workstream_id: str) -> Guide:
        """The shared base and workstream `harness.guide` texts and the personal ones joined, each None when absent."""
        personal = [guide(self.personal_processes), guide(self.personal_workstreams.get(workstream_id, {}))]
        return Guide(
            obeya=guide(self.processes),
            workstream=guide(self.workstreams[workstream_id].processes),
            user=_joined([text for text in personal if text is not None]),
        )

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
                entry[GUIDE_KEY] = {
                    "obeya": texts.obeya,
                    "workstream": texts.workstream,
                    "user": texts.user,
                }
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


def _joined(texts: list[str]) -> str | None:
    """The texts in order with one empty line between each two, the one given alone, or None."""
    if not texts:
        return None
    joined = texts[0]
    for text in texts[1:]:
        joined = joined.rstrip("\n") + "\n\n" + text.lstrip("\n")
    return joined


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
    """Load and validate the config at `root`, or discover it by walking up from `cwd`.

    The personal config is read at that root when it exists, an empty file as one that
    declares nothing; it is never discovered on its own. Every problem of both files is
    reported in one refusal, each with the path of its file.
    """
    if root is None:
        root = find_root(cwd or Path.cwd())
    else:
        root = Path(root).resolve()
        if not (root / CONFIG_FILENAME).is_file():
            raise ConfigError(f"no gemba config found: no {CONFIG_FILENAME} in {root}")

    path, local_path = root / CONFIG_FILENAME, root / LOCAL_FILENAME
    shared_problems: list[str] = []
    personal_problems: list[str] = []
    data = _read(path, "with default_workstream and workstreams", shared_problems)
    local = _read(local_path, "", personal_problems) if local_path.is_file() else {}
    shared = _parse_shared(root, data, shared_problems) if data is not None else None
    catalogue = _catalogue(data) if data is not None else None
    members = _team_members(data) if data is not None else None
    personal = _parse_personal(local, catalogue, members, personal_problems) if local is not None else None

    problems = [(path, problem) for problem in shared_problems]
    problems += [(local_path, problem) for problem in personal_problems]
    if problems or shared is None or personal is None:
        raise ConfigError(problems=problems)
    return dataclasses.replace(
        shared,
        ide=personal.ide,
        repos_dir=personal.repos_dir,
        branch_prefix=personal.branch_prefix,
        personal_providers=personal.providers,
        personal_processes=personal.processes,
        personal_workstreams=personal.workstreams,
        personal=local_path.is_file(),
        me=personal.me,
        git_hooks=personal.git_hooks if personal.git_hooks is not None else shared.git_hooks,
    )


@dataclass(frozen=True)
class _Personal:
    """What the personal config gives the config."""

    providers: tuple[str, ...] | None
    ide: Ide | None
    repos_dir: str | None
    branch_prefix: str
    processes: dict[str, object]
    workstreams: dict[str, dict[str, object]]
    me: str | None = None
    git_hooks: bool | None = None


def _read(path: Path, shape: str, problems: list[str]) -> dict[object, object] | None:
    """The document of the file at `path` as a map, an empty file as an empty one, or None when it is not one.

    A parse error, or a document that is not a map, is appended to `problems`; `shape`
    says what the map holds.
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        problems.append(f"malformed YAML: {exc}")
        return None
    if data is None:
        return {}
    if not isinstance(data, dict):
        problems.append(f"the file must be a map {shape}".rstrip())
        return None
    return data


def _misplaced(data: dict[object, object], filename: str) -> list[str]:
    """A problem for every top-level key of the file `filename` that belongs in the other file or was renamed."""
    problems = []
    for key in data:
        if isinstance(key, str) and key in RENAMED_KEYS:
            renamed = RENAMED_KEYS[key]
            home = LAYERS[renamed][0]
            problems.append(f"{key} was renamed {renamed}, which belongs in {home}, {LAYER_NAMES[home]}")
            continue
        files = LAYERS.get(key) if isinstance(key, str) else None
        if files is not None and filename not in files:
            home = files[0]
            problems.append(f"{key} belongs in {home}, {LAYER_NAMES[home]}: move it there")
    return problems


def _parse_shared(root: Path, data: dict[object, object], problems: list[str]) -> Config | None:
    """The config the shared file declares, every problem appended to `problems`, or None when it cannot be built.

    A check that needs another value runs only when that value is valid: the default
    against a catalogue that is a map, the prefixes and the types over the workstreams
    that parsed, the members and the layout of tasks/ against a catalogue that is a map.
    """
    problems.extend(_misplaced(data, CONFIG_FILENAME))
    base = _parse_fields(data.get("metadata"), metadata.BASE_LIST, problems)
    _check_processes(data, "top level", problems)

    catalogue = data.get("workstreams")
    workstreams: dict[str, Workstream] = {}
    if not isinstance(catalogue, dict) or not catalogue:
        problems.append("workstreams must be a non-empty map keyed by workstream identifier")
        catalogue = None
    else:
        owners: dict[str, str] = {}
        for workstream_id, block in catalogue.items():
            workstream = _parse_workstream(workstream_id, block, problems)
            if workstream is None:
                continue
            if workstream.prefix in owners:
                problems.append(
                    f"workstreams '{owners[workstream.prefix]}' and '{workstream.id}' "
                    f"declare the same prefix '{workstream.prefix}'"
                )
            else:
                owners[workstream.prefix] = workstream.id
            workstreams[workstream.id] = workstream

    default = data.get("default_workstream")
    if default is None:
        problems.append("default_workstream is missing")
    elif catalogue is not None and (not isinstance(default, str) or default not in catalogue):
        problems.append(
            f"default_workstream '{default}' is not in the workstream catalogue "
            f"(valid: {', '.join(map(str, catalogue))})"
        )
    problems.extend(metadata.type_problems(base, _lists(workstreams)))

    providers = _parse_providers(data.get("agent_providers"), problems)
    obeya = _parse_name("obeya", data.get("obeya"), problems)
    identifiers = None if catalogue is None else [str(key) for key in catalogue]
    members = _parse_team(data.get("team"), identifiers, problems)
    if members is not None and identifiers is not None and (problem := team.layout_problem(root, identifiers)):
        problems.append(problem)
    hooks = _parse_hooks(data.get("git_hooks"), data.get("team") is None, problems)
    if not isinstance(default, str):
        return None
    return Config(
        root=root,
        default_workstream=default,
        workstreams=workstreams,
        metadata=base,
        agent_providers=providers,
        obeya=obeya,
        processes={key: value for key, value in data.items() if isinstance(key, str) and key in PROCESSES},
        team=members,
        git_hooks=bool(hooks),
    )


def _catalogue(data: dict[object, object]) -> list[str] | None:
    """The workstream identifiers of the shared file, or None when its catalogue is not a non-empty map."""
    catalogue = data.get("workstreams")
    return [str(key) for key in catalogue] if isinstance(catalogue, dict) and catalogue else None


def _team_members(data: dict[object, object]) -> tuple[str, ...] | None:
    """The folder names the team of the shared file declares, even those of a member at fault, so that `me` naming
    one is not reported again; empty when the file declares no team, None when its team is not a non-empty map."""
    declared = data.get("team")
    if declared is None:
        return ()
    return tuple(str(key) for key in declared) if isinstance(declared, dict) and declared else None


def _parse_personal(
    data: dict[object, object], catalogue: list[str] | None, members: tuple[str, ...] | None, problems: list[str]
) -> _Personal:
    """What the personal file declares, every problem appended to `problems`.

    `catalogue` holds the workstream identifiers of the shared file, or is None when they
    are unknown, and then the personal workstreams are not checked against it. `members`
    holds the folder names of the team of the shared file, empty when it declares none,
    or is None when they are unknown, and then `me` is not checked against them.
    """
    problems.extend(_misplaced(data, LOCAL_FILENAME))
    _check_processes(data, "top level", problems)
    return _Personal(
        providers=_parse_providers(data.get("agent_providers"), problems),
        ide=_parse_ide(data.get("ide"), problems),
        repos_dir=_parse_repos_dir(data.get("repos_dir"), problems),
        branch_prefix=_parse_name("branch_prefix", data.get("branch_prefix"), problems) or DEFAULT_BRANCH_PREFIX,
        processes={key: value for key, value in data.items() if isinstance(key, str) and key in PROCESSES},
        workstreams=_parse_personal_workstreams(data.get("workstreams"), catalogue, problems),
        me=_parse_me(data.get("me"), members, problems),
        git_hooks=_parse_hooks(data.get("git_hooks"), members == (), problems),
    )


def _parse_team(declaration: object, workstream_ids: list[str] | None, problems: list[str]) -> dict[str, Member] | None:
    """The members of the team that parsed, by folder name, or None when the config declares no team or a team that
    is not a non-empty map; every problem is appended to `problems`.

    A folder name equal to a workstream identifier is checked only when `workstream_ids`
    is known, and repeated initials over the members whose initials parsed.
    """
    if declaration is None:
        return None
    if not isinstance(declaration, dict) or not declaration:
        problems.append("team must be a non-empty map keyed by the folder name of each member")
        return None
    members: dict[str, Member] = {}
    holders: dict[str, str] = {}
    for member_id, entry in declaration.items():
        where = f"team member '{member_id}'"
        found: list[str] = []
        if not isinstance(member_id, str) or not WORKSTREAM_ID_PATTERN.match(member_id):
            found.append(f"{where}: folder name must be kebab-case (lowercase letters, digits and single hyphens)")
        elif platform.is_reserved_name(member_id):
            found.append(f"{where}: folder name is reserved on Windows, where it could not be a folder name")
        elif workstream_ids is not None and member_id in workstream_ids:
            found.append(
                f"{where}: folder name is the identifier of a workstream, whose folder under tasks/ it would be "
                "taken for"
            )
        if not isinstance(entry, dict):
            problems.extend([*found, f"{where}: must be a map with initials and optionally active"])
            continue
        initials = entry.get("initials")
        if not isinstance(initials, str) or not team.INITIALS_PATTERN.match(initials):
            found.append(
                f"{where}: initials must be one or more uppercase ASCII letters (got {initials!r}; "
                "quote it if YAML reads it as another type)"
            )
        active = entry.get("active", True)
        if not isinstance(active, bool):
            found.append(f"{where}: active must be true or false (got {active!r})")
        found.extend(
            f"{where}: {key} is not a key of a member (allowed: {', '.join(team.MEMBER_KEYS)})"
            for key in entry
            if key not in team.MEMBER_KEYS
        )
        problems.extend(found)
        if isinstance(initials, str) and team.INITIALS_PATTERN.match(initials):
            if initials in holders:
                problems.append(
                    f"team members '{holders[initials]}' and '{member_id}' declare the same initials '{initials}'"
                )
            else:
                holders[initials] = str(member_id)
        if not found and isinstance(member_id, str) and isinstance(initials, str) and isinstance(active, bool):
            members[member_id] = Member(id=member_id, initials=initials, active=active)
    return members


def _parse_me(declaration: object, members: tuple[str, ...] | None, problems: list[str]) -> str | None:
    """The member the clone belongs to, or None when the personal config declares none or a bad one.

    `members` holds the folder names of the team, empty when the shared config declares
    none, or is None when they are unknown.
    """
    if declaration is None:
        return None
    if not isinstance(declaration, str) or not declaration:
        problems.append("me must be the folder name of a member of the team")
        return None
    if members == ():
        problems.append(f"me needs a team: {CONFIG_FILENAME} declares none")
        return None
    if members is not None and declaration not in members:
        problems.append(f"me names no member of the team: '{declaration}' (members: {', '.join(members)})")
        return None
    return declaration


def _parse_hooks(declaration: object, without_team: bool, problems: list[str]) -> bool | None:
    """Whether a file turns gemba's git hooks on, or None when it declares nothing or a bad value.

    `without_team` says that the shared config declares no team, where the key has no use.
    """
    if declaration is None:
        return None
    if not isinstance(declaration, bool):
        problems.append(f"git_hooks must be true or false (got {declaration!r})")
        return None
    if without_team:
        problems.append(f"git_hooks needs a team: {CONFIG_FILENAME} declares none")
        return None
    return declaration


def _parse_personal_workstreams(
    declaration: object, catalogue: list[str] | None, problems: list[str]
) -> dict[str, dict[str, object]]:
    """The process blocks the personal file gives each workstream of the catalogue, by identifier.

    An entry holds process blocks only: what defines a workstream belongs in the shared file.
    """
    if declaration is None:
        return {}
    if not isinstance(declaration, dict):
        problems.append(f"workstreams must be a map keyed by workstream identifiers of {CONFIG_FILENAME}")
        return {}
    blocks: dict[str, dict[str, object]] = {}
    for workstream_id, block in declaration.items():
        where = f"workstream '{workstream_id}'"
        if catalogue is not None and workstream_id not in catalogue:
            problems.append(
                f"{where} is not in the workstream catalogue of {CONFIG_FILENAME} (valid: {', '.join(catalogue)})"
            )
            continue
        if not isinstance(block, dict):
            problems.append(f"{where}: must be a map of process blocks")
            continue
        for key in DEFINITION_KEYS:
            if key in block:
                problems.append(
                    f"{where}: {key} belongs in {CONFIG_FILENAME}, {LAYER_NAMES[CONFIG_FILENAME]}: "
                    "a workstream of the personal config holds process blocks only"
                )
        _check_processes(block, where, problems)
        blocks[str(workstream_id)] = {key: value for key, value in block.items() if key in PROCESSES}
    return blocks


def _parse_name(key: str, declaration: object, problems: list[str]) -> str | None:
    """A kebab-case name that becomes a segment of a branch, or None when the config declares none or a bad one."""
    if declaration is None:
        return None
    if not isinstance(declaration, str) or not WORKSTREAM_ID_PATTERN.match(declaration):
        problems.append(f"{key} must be kebab-case (lowercase letters, digits and single hyphens)")
        return None
    return declaration


def _parse_repos_dir(declaration: object, problems: list[str]) -> str | None:
    """The folder of the repositories a run may check out, as declared, or None when the config declares none."""
    if declaration is None:
        return None
    if not isinstance(declaration, str) or not declaration.strip():
        problems.append(
            "repos_dir must be a non-empty string naming the folder of the repositories: "
            "absolute, starting with ~, or relative to the obeya root"
        )
        return None
    return declaration


def _parse_ide(declaration: object, problems: list[str]) -> Ide | None:
    """The command that opens a folder in the IDE, or None when the config declares none or a bad one.

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
            problems.append(f"{shape} (cannot split {declaration!r}: {exc})")
            return None
        if not parts or not parts[0]:
            problems.append(shape)
            return None
        return Ide(command=parts[0], args=tuple(parts[1:]), declared=declaration)
    if not isinstance(declaration, dict):
        problems.append(shape)
        return None
    command = declaration.get("command")
    args = declaration.get("args", [])
    valid = True
    if not isinstance(command, str) or not command.strip():
        problems.append("ide.command must be a non-empty string naming the executable that opens a folder in the IDE")
        valid = False
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        problems.append("ide.args must be a list of strings, the arguments given before the harness path")
        valid = False
    if not valid or not isinstance(command, str) or not isinstance(args, list):
        return None
    declared = {str(key): value for key, value in declaration.items()}
    return Ide(command=command, args=tuple(args), declared=declared)


def _parse_providers(declaration: object, problems: list[str]) -> tuple[str, ...] | None:
    """The declared agent providers in order, or None when the config declares none or a bad list.

    Every unknown provider and every repeated one is a problem of its own, each named once.
    """
    if declaration is None:
        return None
    known = f"(known providers: {', '.join(skills.PROVIDERS)})"
    if not isinstance(declaration, list) or not declaration or not all(isinstance(item, str) for item in declaration):
        problems.append(f"agent_providers must be a non-empty list of provider identifiers {known}")
        return None
    names: list[str] = list(declaration)
    unknown = [name for name in dict.fromkeys(names) if name not in skills.PROVIDERS]
    repeated = [name for name in dict.fromkeys(names) if name in skills.PROVIDERS and names.count(name) > 1]
    problems.extend(f"agent_providers: unknown provider '{name}' {known}" for name in unknown)
    problems.extend(f"agent_providers: provider '{name}' is listed more than once {known}" for name in repeated)
    return None if unknown or repeated else tuple(names)


def _parse_workstream(workstream_id: object, block: object, problems: list[str]) -> Workstream | None:
    """One workstream of the catalogue, or None when it has a problem, each appended to `problems`."""
    where = f"workstream '{workstream_id}'"
    found: list[str] = []
    if not isinstance(workstream_id, str) or not WORKSTREAM_ID_PATTERN.match(workstream_id):
        found.append(f"{where}: identifier must be kebab-case (lowercase letters, digits and single hyphens)")
    elif platform.is_reserved_name(workstream_id):
        found.append(f"{where}: identifier is reserved on Windows, where it could not be a folder name")
    if not isinstance(block, dict):
        problems.extend([*found, f"{where}: must be a map with prefix and description"])
        return None

    prefix = block.get("prefix")
    if not isinstance(prefix, str) or not PREFIX_PATTERN.match(prefix):
        found.append(
            f"{where}: prefix must be one or more uppercase ASCII letters (got {prefix!r}; "
            "quote it if YAML reads it as another type)"
        )
    description = block.get("description")
    if not isinstance(description, str) or not description.strip():
        found.append(f"{where}: description is missing or empty")
    fields = _parse_fields(block.get("metadata"), _list_name(workstream_id), found)
    _check_processes(block, where, found)

    problems.extend(found)
    if found or not isinstance(workstream_id, str) or not isinstance(prefix, str) or not isinstance(description, str):
        return None
    processes = {key: value for key, value in block.items() if key not in DEFINITION_KEYS}
    return Workstream(
        id=workstream_id,
        prefix=prefix,
        description=description.strip(),
        metadata=fields,
        processes=processes,
    )


def _parse_fields(declarations: object, where: str, problems: list[str]) -> tuple[Field, ...]:
    """The fields of one declaration list that parsed, the problems of the others appended to `problems`."""
    fields, found = metadata.parse_fields(declarations, where)
    problems.extend(found)
    return fields


def _list_name(workstream_id: object) -> str:
    """How a refusal names the metadata list of a workstream."""
    return f"workstream '{workstream_id}' metadata"


def _lists(workstreams: dict[str, Workstream]) -> dict[str, tuple[Field, ...]]:
    """The metadata list of every workstream, keyed by the name a refusal gives it."""
    return {_list_name(workstream.id): workstream.metadata for workstream in workstreams.values()}


def _check_processes(block: dict[object, object], where: str, problems: list[str]) -> None:
    """Every process block of one level, the top level or a workstream, each validated by its shape."""
    for process, verbs in PROCESSES.items():
        if verbs is None:
            _check_process_block(process, block.get(process), where, problems)
        else:
            _check_group_block(process, verbs, GROUP_KEYS.get(process, ()), block.get(process), where, problems)


def _check_group_block(
    group: str, verbs: tuple[str, ...], extra: tuple[str, ...], block: object, where: str, problems: list[str]
) -> None:
    """A group block holds one verb block per verb and the `extra` keys it allows; any other key is refused."""
    if block is None:
        return
    allowed = (*extra, *verbs)
    if not isinstance(block, dict):
        problems.append(f"{where}: {group} must be a map (allowed keys: {', '.join(allowed)})")
        return
    for key, value in block.items():
        if key == GUIDE_KEY and key in extra:
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{where}: {group}.{GUIDE_KEY} must be a non-empty string")
        elif key in verbs:
            _check_process_block(f"{group}.{key}", value, where, problems)
        else:
            problems.append(f"{where}: {group}.{key} is not a key of {group} (allowed: {', '.join(allowed)})")


def _check_process_block(process: str, block: object, where: str, problems: list[str]) -> None:
    if block is None:
        return
    if not isinstance(block, dict):
        problems.append(f"{where}: {process} must be a map with rules and context")
        return
    rules = block.get("rules")
    if rules is not None and (
        not isinstance(rules, list) or not all(isinstance(rule, str) and rule.strip() for rule in rules)
    ):
        problems.append(f"{where}: {process}.rules must be a list of non-empty strings")
    context = block.get("context")
    if context is not None and not isinstance(context, str):
        problems.append(f"{where}: {process}.context must be a string")
