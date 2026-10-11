"""Built-in skills: the agent provider table, the skill registry, rendering and inspection."""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml

Target = Literal["repo", "harness"]
Scope = Literal["repo", "harness", "both"]
State = Literal["missing", "unchanged", "outdated", "edited"]
Outcome = Literal["written", "updated", "kept", "overwritten"]


@dataclass(frozen=True)
class Provider:
    """Where an agent provider reads its skills and its guide, relative to the target root."""

    skills_dir: str
    guide: str


@dataclass(frozen=True)
class Skill:
    """A built-in skill and the targets it is written into: the tasks repo, a harness or both."""

    name: str
    scope: Scope

    def belongs_to(self, target: Target) -> bool:
        return self.scope in (target, "both")


# Every agent provider the CLI knows.
PROVIDERS = {
    "claude": Provider(skills_dir=".claude/skills", guide="CLAUDE.md"),
    "agents": Provider(skills_dir=".agents/skills", guide="AGENTS.md"),
}

# Every built-in skill, in writing order; each one ships as assets/skills/<name>/SKILL.md.
SKILLS = (
    Skill("gemba-create", "repo"),
    Skill("gemba-list", "repo"),
    Skill("gemba-harness", "both"),
    Skill("gemba-record", "harness"),
    Skill("gemba-report", "repo"),
    Skill("gemba-mark", "both"),
    Skill("gemba-archive", "repo"),
    Skill("gemba-set", "both"),
    Skill("gemba-worktree", "harness"),
    Skill("gemba-init", "repo"),
    Skill("gemba-config", "repo"),
)

SKILL_FILE = "SKILL.md"
FRONTMATTER_DELIMITER = "---"
METADATA_KEY = "metadata"


@dataclass(frozen=True)
class Action:
    """One registered skill under one provider: its path, the state on disk and what to write."""

    path: str  # relative to the target root, POSIX separators
    state: State
    content: str

    def outcome(self, force: bool) -> Outcome:
        """What `update` does with the file: an edited skill is kept unless `force` is set."""
        if self.state == "missing":
            return "written"
        if self.state == "outdated":
            return "updated"
        if self.state == "edited" and force:
            return "overwritten"
        return "kept"


def asset(name: str) -> str:
    """The text of a registered skill as the package ships it."""
    if name not in (skill.name for skill in SKILLS):
        raise ValueError(f"'{name}' is not a registered skill")
    return (resources.files("gemba") / "assets" / "skills" / name / SKILL_FILE).read_text(encoding="utf-8")


def guide_asset() -> str:
    """The text of the harness guide as the package ships it."""
    return (resources.files("gemba") / "assets" / "harness" / "guide.md").read_text(encoding="utf-8")


def render(name: str, version: str) -> str:
    """The `SKILL.md` that package `version` writes for a registered skill."""
    return stamp(asset(name), version)


def stamp(text: str, version: str) -> str:
    """`text` with the provenance map appended to its frontmatter."""
    parts = normalize(text).split("\n")
    end = _frontmatter_end(parts)
    if end is None:
        raise ValueError("a skill must start with a YAML frontmatter")
    if _metadata_span(parts, end) is not None:
        raise ValueError("a skill asset must not carry a metadata map")
    provenance = [f"{METADATA_KEY}:", f'  generatedBy: "{version}"', f'  contentHash: "{content_hash(text)}"']
    return "\n".join(parts[:end] + provenance + parts[end:])


def normalize(text: str) -> str:
    """`text` with every line ending turned into `\\n`."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def content(text: str) -> str:
    """What a `contentHash` covers: `text` with normalized line endings and no metadata map."""
    stripped, _block = _split(normalize(text))
    return stripped


def content_hash(text: str) -> str:
    """SHA-256 of the content of `text`, as hexadecimal digits."""
    return _digest(content(text))


def inspect(path: Path, rendered: str) -> State:
    """Classify the skill file at `path` against `rendered`, the text the package writes now."""
    if not path.is_file():
        return "missing"
    text = normalize(path.read_bytes().decode("utf-8", errors="replace"))
    stripped, block = _split(text)
    metadata = _parse_metadata(block)
    if metadata is None or metadata.get("contentHash") != _digest(stripped):
        return "edited"
    generator = metadata.get("generatedBy")
    if isinstance(generator, str) and text == stamp(content(rendered), generator):
        return "unchanged"
    return "outdated"


def plan(root: Path, providers: Sequence[str], version: str, scope: Target) -> list[Action]:
    """One action per declared provider and skill whose scope includes the target, in declaration and registry order."""
    names = [skill.name for skill in SKILLS if skill.belongs_to(scope)]
    rendered = {name: render(name, version) for name in names}
    actions = []
    for provider in providers:
        for name in names:
            relative = PurePosixPath(PROVIDERS[provider].skills_dir, name, SKILL_FILE)
            state = inspect(root / relative, rendered[name])
            actions.append(Action(path=relative.as_posix(), state=state, content=rendered[name]))
    return actions


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split(text: str) -> tuple[str, str | None]:
    """`text` without the metadata map of its frontmatter, and the map's lines, or None without one."""
    parts = text.split("\n")
    end = _frontmatter_end(parts)
    span = None if end is None else _metadata_span(parts, end)
    if span is None:
        return text, None
    start, stop = span
    return "\n".join(parts[:start] + parts[stop:]), "\n".join(parts[start:stop])


def _frontmatter_end(parts: list[str]) -> int | None:
    """Index of the line that closes the frontmatter, or None when the text has no frontmatter."""
    if parts[0] != FRONTMATTER_DELIMITER:
        return None
    for index in range(1, len(parts)):
        if parts[index] == FRONTMATTER_DELIMITER:
            return index
    return None


def _metadata_span(parts: list[str], end: int) -> tuple[int, int] | None:
    """Line range of the top-level metadata key and its indented lines, inside the frontmatter."""
    for start in range(1, end):
        if parts[start].startswith(f"{METADATA_KEY}:"):
            stop = start + 1
            while stop < end and parts[stop][:1] in (" ", "\t"):
                stop += 1
            return start, stop
    return None


def _parse_metadata(block: str | None) -> dict[object, object] | None:
    if block is None:
        return None
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return None
    metadata = data.get(METADATA_KEY) if isinstance(data, dict) else None
    return metadata if isinstance(metadata, dict) else None
