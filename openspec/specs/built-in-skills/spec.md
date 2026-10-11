# built-in-skills Specification

## Purpose

The skills of Gemba are assets of the gemba CLI package, written into the tasks repo
by the CLI for every agent provider the gemba config declares, with the provenance
needed to tell an outdated copy from a hand edit.

## Requirements

### Requirement: Skills are assets of the package
Every skill of Gemba SHALL ship inside the gemba CLI package, and the package SHALL
hold a registry naming each built-in skill with its scope: the tasks repo, a harness,
or both. `gemba skills update` SHALL write exactly the registered skills whose scope
includes its target and SHALL NOT create, modify or delete any other folder or file
under a provider's skills folder, so that skills of other tools that share the folder
are left as they are. At this change `gemba-create`, `gemba-list`, `gemba-report`,
`gemba-archive`, `gemba-init` and `gemba-config` belong to the tasks repo,
`gemba-record` and `gemba-worktree` to the harness, and `gemba-harness`, `gemba-mark`
and `gemba-set` to both. `gemba init` SHALL write the tasks-repo skills through the
same registry, so a skill added to it reaches a new tasks repo with no other change.

#### Scenario: Every registered skill is written
- **WHEN** `gemba skills update` runs in a tasks repo that declares one provider and has no skills folder
- **THEN** one `SKILL.md` per registered skill whose scope includes the tasks repo appears under that provider's skills folder, each in a folder named after the skill, `gemba-init` and `gemba-config` included, and the command exits 0

#### Scenario: Unregistered skills are not touched
- **WHEN** the provider's skills folder already holds a skill that is not registered, such as one of another tool
- **THEN** `gemba skills update` leaves that skill byte for byte as it was and does not mention it

#### Scenario: Harness-scoped skills only
- **WHEN** `gemba skills update` targets a harness
- **THEN** only the skills whose scope includes the harness are written or reported, `gemba-harness`, `gemba-record`, `gemba-mark`, `gemba-set` and `gemba-worktree` at this change, and no `gemba-create`, `gemba-list`, `gemba-report`, `gemba-archive`, `gemba-init` or `gemba-config` folder is created there

### Requirement: Skills are written per agent provider
`gemba skills update` SHALL write the skills under the skills folder of every provider
of its target, relative to the target root: the `claude` provider under
`.claude/skills/` and the `agents` provider under `.agents/skills/`. The provider table
of the CLI SHALL also name the guide filename of each provider, `CLAUDE.md` for `claude`
and `AGENTS.md` for `agents`, which `launch` uses. A provider the target does not list
SHALL get nothing. When the tasks repo is the target and the config declares no
`agent_providers`, the command SHALL refuse, name the known providers, and write
nothing.

#### Scenario: One skills folder per declared provider
- **WHEN** the config declares `agent_providers: [claude, agents]`
- **THEN** every registered skill of the target's scope is written under both `.claude/skills/` and `.agents/skills/` with the same content

#### Scenario: Undeclared provider gets nothing
- **WHEN** the config declares `agent_providers: [claude]` only
- **THEN** the skills are written under `.claude/skills/` and no `.agents/` folder is created

#### Scenario: No providers declared
- **WHEN** the config has no `agent_providers` key
- **THEN** `gemba skills update` exits 1, reports that no agent providers are declared, names the known providers, and writes nothing

#### Scenario: Guide filename per provider
- **WHEN** a harness is launched for `agent_providers: [claude, agents]`
- **THEN** the guide is written as `CLAUDE.md` and as `AGENTS.md`

### Requirement: Skills are written at the root the command runs in
`gemba skills update` SHALL resolve its target by walking up from the current working
directory: the nearest folder holding `harness.yaml` is a harness and the target is
that harness, with the providers recorded in its `harness.yaml`; otherwise the nearest
folder holding `gemba.yaml` is the tasks repo and the target is its root, with the
providers of the gemba config. The command SHALL write the skills folders under the
target and never under the working directory, and SHALL refuse, writing nothing, when
no gemba config is found. `--root` SHALL name the target explicitly, tasks repo or
harness.

#### Scenario: Run from a subfolder
- **WHEN** `gemba skills update` runs from a folder below the tasks repo root that is not inside a harness
- **THEN** the skills appear under the root, and nothing is written under the folder the command ran from

#### Scenario: Run from inside a harness
- **WHEN** `gemba skills update` runs from a folder inside a harness whose `harness.yaml` records `agent_providers: [claude]`
- **THEN** the harness-scoped skills are written or refreshed under the harness's `.claude/skills/`, nothing is written under `.agents/`, and nothing is written at the tasks repo root

#### Scenario: No tasks repo
- **WHEN** no ancestor of the working directory holds `gemba.yaml`
- **THEN** the command exits 1, reports that no gemba config was found, and writes nothing

### Requirement: Written skill content and provenance
A written `SKILL.md` SHALL consist of a YAML frontmatter followed by the body of the
asset, unchanged. The frontmatter SHALL carry the skill's `name` (equal to its folder
name), its `description`, and a `metadata` map with `generatedBy`, the version of the
package that wrote the file, and `contentHash`, a digest of the file with its
`metadata` map removed, so that the provenance can be checked from the file alone.
The content SHALL be the same for every provider.

#### Scenario: Generated skill carries its provenance
- **WHEN** a skill is written by package version V
- **THEN** its frontmatter holds `name`, `description`, `metadata.generatedBy: "V"` and `metadata.contentHash`, and its body is the asset's body

### Requirement: Update is idempotent and respects hand edits
For each registered skill and each declared provider, `gemba skills update` SHALL
classify the file on disk as one of: **missing** (no file); **unchanged** (identical
to what the current package writes, ignoring `generatedBy`); **outdated** (different
from what the current package writes, while its `contentHash` matches its own
content, so it is an untouched older generation); **edited** (its `contentHash` is
absent or does not match its own content). The command SHALL write a missing skill,
rewrite an outdated one, leave an unchanged one as it is, and leave an edited one as
it is unless `--force` is passed, in which case it SHALL overwrite it. The command
SHALL print one line per skill and provider stating the action taken (`written`,
`updated`, `kept`, `overwritten`) and the path relative to the tasks repo root, and
SHALL say on the `kept` line of an edited skill that `--force` overwrites it. Running
the command twice SHALL leave the tree identical after the second run.

#### Scenario: Missing skill is written
- **WHEN** a registered skill has no file under a declared provider
- **THEN** the file is written and the output reports `written` with its path

#### Scenario: Unchanged skill is left alone
- **WHEN** `gemba skills update` runs a second time with nothing changed in between
- **THEN** the tree is identical to the one after the first run and every skill is reported as `kept`

#### Scenario: Outdated skill is refreshed
- **WHEN** a skill on disk differs from what the current package writes and its `contentHash` matches its own content
- **THEN** the file is rewritten with the current content and the output reports `updated`

#### Scenario: Edited skill is kept and reported
- **WHEN** a skill on disk has no `contentHash` or one that does not match its own content
- **THEN** the file is left byte for byte as it was, the output reports it as `kept` because it was edited by hand and says that `--force` overwrites it, and the command exits 0

#### Scenario: Edited skill is overwritten on request
- **WHEN** `gemba skills update --force` runs with an edited skill on disk
- **THEN** the file is replaced with the current content and the output reports `overwritten`

### Requirement: Check mode reports without writing
`gemba skills update --check` SHALL classify every skill as above, print one line per
skill and provider with its state (`missing`, `unchanged`, `outdated`, `edited`) and
its path, write nothing, and exit 0 when every skill is unchanged and 1 otherwise.

#### Scenario: Check finds everything current
- **WHEN** `--check` runs after an update with nothing changed in between
- **THEN** every skill is reported as `unchanged`, the tree is untouched and the exit code is 0

#### Scenario: Check finds work to do
- **WHEN** `--check` runs with one skill missing and one edited
- **THEN** both are reported with their state, the tree is untouched and the exit code is 1

### Requirement: Adding a skill is one asset and one declaration
Adding the skill of a new process to the package SHALL consist of one asset folder
holding its `SKILL.md` and one entry in the registry, with no change to the writing
mechanism, the provider table or the command.

#### Scenario: New process ships its skill
- **WHEN** a later change adds a process with a skill
- **THEN** it adds the asset folder and the registry entry, and `gemba skills update` writes the new skill for every declared provider without any other code change

### Requirement: Skills name the published package
Every skill SHALL state, as its prerequisite, that the `gemba` command must be on the
PATH, that it is installed with `uv tool install gemba-cli` and checked with
`gemba --version`, and SHALL have the agent stop and tell the user to install it with
that command when it is not found. No skill SHALL name a path of the product
repository or a development install.

#### Scenario: Command missing
- **WHEN** the agent follows a skill and `gemba` is not found on the PATH
- **THEN** the agent stops and tells the user to run `uv tool install gemba-cli`

#### Scenario: No development path in a skill
- **WHEN** the assets of every registered skill are read
- **THEN** each one names `uv tool install gemba-cli` and none names `./cli` or an editable install
