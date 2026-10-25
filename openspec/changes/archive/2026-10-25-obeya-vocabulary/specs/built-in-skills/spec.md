# Spec Delta

## MODIFIED Requirements

### Requirement: Skills are assets of the package
Every skill of Gemba SHALL ship inside the gemba CLI package, and the package SHALL
hold a registry naming each built-in skill with its scope: the obeya, a harness,
or both. `gemba skills update` SHALL write exactly the registered skills whose scope
includes its target and SHALL NOT create, modify or delete any other folder or file
under a provider's skills folder, so that skills of other tools that share the folder
are left as they are. At this change `gemba-create`, `gemba-list`, `gemba-report`,
`gemba-archive`, `gemba-init`, `gemba-config` and `gemba-migrate` belong to the obeya, `gemba-worktree` to the harness, and `gemba-harness`, `gemba-record`,
`gemba-mark` and `gemba-set` to both. `gemba init` SHALL write the obeya skills through the same
registry, so a skill added to it reaches a new obeya with no other change.

#### Scenario: Every registered skill is written
- **WHEN** `gemba skills update` runs in an obeya that declares one provider and has no skills folder
- **THEN** one `SKILL.md` per registered skill whose scope includes the obeya appears under that provider's skills folder, each in a folder named after the skill, `gemba-record`, `gemba-init`, `gemba-config` and `gemba-migrate` included, and the command exits 0
- **Cases**: keeps `tests/cases/skills/every-registered-skill-is-written.yaml`

#### Scenario: Unregistered skills are not touched
- **WHEN** the provider's skills folder already holds a skill that is not registered, such as one of another tool
- **THEN** `gemba skills update` leaves that skill byte for byte as it was and does not mention it
- **Cases**: keeps `tests/cases/skills/unregistered-skills-are-not-touched.yaml`

#### Scenario: Harness-scoped skills only
- **WHEN** `gemba skills update` targets a harness
- **THEN** only the skills whose scope includes the harness are written or reported, `gemba-harness`, `gemba-record`, `gemba-mark`, `gemba-set` and `gemba-worktree` at this change, and no `gemba-create`, `gemba-list`, `gemba-report`, `gemba-archive`, `gemba-init`, `gemba-config` or `gemba-migrate` folder is created there
- **Cases**: keeps `tests/cases/skills/harness-scoped-skills-only.yaml`

### Requirement: Skills are written per agent provider
`gemba skills update` SHALL write the skills under the skills folder of every provider
of its target, relative to the target root: the `claude` provider under
`.claude/skills/` and the `agents` provider under `.agents/skills/`. The provider table
of the CLI SHALL also name the guide filename of each provider, `CLAUDE.md` for `claude`
and `AGENTS.md` for `agents`, which `launch` uses. A provider the target does not list
SHALL get nothing. When the obeya is the target and the config declares no
`agent_providers`, the command SHALL refuse, name the known providers, and write
nothing.

#### Scenario: One skills folder per declared provider
- **WHEN** the config declares `agent_providers: [claude, agents]`
- **THEN** every registered skill of the target's scope is written under both `.claude/skills/` and `.agents/skills/` with the same content
- **Cases**: keeps `tests/cases/skills/one-folder-per-declared-provider.yaml`

#### Scenario: Undeclared provider gets nothing
- **WHEN** the config declares `agent_providers: [claude]` only
- **THEN** the skills are written under `.claude/skills/` and no `.agents/` folder is created
- **Cases**: keeps `tests/cases/skills/undeclared-provider-gets-nothing.yaml`

#### Scenario: No providers declared
- **WHEN** the config has no `agent_providers` key
- **THEN** `gemba skills update` exits 1, reports that no agent providers are declared, names the known providers, and writes nothing
- **Cases**: keeps `tests/cases/skills/no-providers-declared.yaml`

#### Scenario: Guide filename per provider
- **WHEN** a harness is launched for `agent_providers: [claude, agents]`
- **THEN** the guide is written as `CLAUDE.md` and as `AGENTS.md`
- **Cases**: keeps `tests/cases/harness/same-guide-for-every-provider.yaml`

### Requirement: Skills are written at the root the command runs in
`gemba skills update` SHALL resolve its target by walking up from the current working
directory: the nearest folder holding `harness.yaml` is a harness and the target is
that harness, with the providers recorded in its `harness.yaml`; otherwise the nearest
folder holding `gemba.yaml` is the obeya and the target is its root, with the
providers of the shared config, never those of the personal config, which choose the
providers of a launch only. A shared config that declares no `agent_providers` SHALL
be refused as the previous requirement says, whatever the personal config declares.
The command SHALL write the skills folders under the target and never under the
working directory, and SHALL refuse, writing nothing, when no gemba config is found.
`--root` SHALL name the target explicitly, obeya or harness.

#### Scenario: Run from a subfolder
- **WHEN** `gemba skills update` runs from a folder below the obeya root that is not inside a harness
- **THEN** the skills appear under the root, and nothing is written under the folder the command ran from
- **Cases**: modifies `tests/cases/skills/run-from-a-subfolder.yaml` (its name says obeya)

#### Scenario: Run from inside a harness
- **WHEN** `gemba skills update` runs from a folder inside a harness whose `harness.yaml` records `agent_providers: [claude]`
- **THEN** the harness-scoped skills are written or refreshed under the harness's `.claude/skills/`, nothing is written under `.agents/`, and nothing is written at the obeya root
- **Cases**: keeps `tests/cases/skills/run-from-inside-a-harness.yaml`

#### Scenario: No obeya
- **WHEN** no ancestor of the working directory holds `gemba.yaml`
- **THEN** the command exits 1, reports that no gemba config was found, and writes nothing
- **Cases**: modifies `tests/cases/skills/no-tasks-repo.yaml`, renamed `no-obeya.yaml` (it names its scenario by the new title)

#### Scenario: Personal providers leave the obeya skills
- **WHEN** `gemba.yaml` declares `agent_providers: [claude]`, `gemba.local.yaml` declares `agent_providers: [agents]`, and `gemba skills update` runs at the obeya root
- **THEN** the obeya skills are written under `.claude/skills/` and no `.agents/` folder is created
- **Cases**: modifies `tests/cases/skills/personal-providers-leave-the-tasks-repo-skills.yaml`, renamed `personal-providers-leave-the-obeya-skills.yaml` (its name says obeya; it names its scenario by the new title)

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
- **Cases**: modifies `tests/cases/skills/generated-skill-carries-its-provenance.yaml` (the skill text it expects says obeya)

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
`updated`, `kept`, `overwritten`) and the path relative to the obeya root, and
SHALL say on the `kept` line of an edited skill that `--force` overwrites it. Running
the command twice SHALL leave the tree identical after the second run.

#### Scenario: Missing skill is written
- **WHEN** a registered skill has no file under a declared provider
- **THEN** the file is written and the output reports `written` with its path
- **Cases**: keeps `tests/cases/skills/missing-skill-is-written.yaml`

#### Scenario: Unchanged skill is left alone
- **WHEN** `gemba skills update` runs a second time with nothing changed in between
- **THEN** the tree is identical to the one after the first run and every skill is reported as `kept`
- **Cases**: keeps `tests/cases/skills/unchanged-skill-is-left-alone.yaml`

#### Scenario: Outdated skill is refreshed
- **WHEN** a skill on disk differs from what the current package writes and its `contentHash` matches its own content
- **THEN** the file is rewritten with the current content and the output reports `updated`
- **Cases**: modifies `tests/cases/skills/outdated-skill-is-refreshed.yaml` (the skill text it expects says obeya)

#### Scenario: Edited skill is kept and reported
- **WHEN** a skill on disk has no `contentHash` or one that does not match its own content
- **THEN** the file is left byte for byte as it was, the output reports it as `kept` because it was edited by hand and says that `--force` overwrites it, and the command exits 0
- **Cases**: keeps `tests/cases/skills/edited-skill-is-kept-and-reported.yaml`

#### Scenario: Edited skill is overwritten on request
- **WHEN** `gemba skills update --force` runs with an edited skill on disk
- **THEN** the file is replaced with the current content and the output reports `overwritten`
- **Cases**: modifies `tests/cases/skills/edited-skill-is-overwritten-on-request.yaml` (the skill text it expects says obeya)
