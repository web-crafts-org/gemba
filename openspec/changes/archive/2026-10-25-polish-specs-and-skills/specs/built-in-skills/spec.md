# Spec Delta

## MODIFIED Requirements

### Requirement: Skills are assets of the package
Every skill SHALL ship in the gemba CLI package, in a registry that gives each its
scope: the obeya (`gemba-create`, `gemba-list`, `gemba-report`, `gemba-archive`,
`gemba-init`, `gemba-config`, `gemba-migrate`), a harness (`gemba-worktree`), or both
(`gemba-harness`, `gemba-record`, `gemba-mark`, `gemba-set`). `gemba skills update`
and `gemba init` SHALL write exactly the registered skills whose scope includes their
target, and nothing else under a provider's skills folder.

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
of its target, relative to the target root: `.claude/skills/` for `claude` and
`.agents/skills/` for `agents`. Each provider SHALL also name the guide filename
`launch` writes, `CLAUDE.md` for `claude` and `AGENTS.md` for `agents`. A provider the
target does not list SHALL get nothing. When the obeya declares no `agent_providers`,
the command SHALL refuse, name the known providers, and write nothing.

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
`gemba skills update` SHALL take as target the nearest folder up from the working
directory that holds `harness.yaml`, with the providers it records, or else the
nearest that holds `gemba.yaml`, with the providers of the shared config alone,
whatever the personal config declares; `--root` SHALL name the target instead. It
SHALL write under the target, never under the working directory, and SHALL refuse,
writing nothing, when no gemba config is found.

#### Scenario: Run from a subfolder
- **WHEN** `gemba skills update` runs from a folder below the obeya root that is not inside a harness
- **THEN** the skills appear under the root, and nothing is written under the folder the command ran from
- **Cases**: keeps `tests/cases/skills/run-from-a-subfolder.yaml`

#### Scenario: Run from inside a harness
- **WHEN** `gemba skills update` runs from a folder inside a harness whose `harness.yaml` records `agent_providers: [claude]`
- **THEN** the harness-scoped skills are written or refreshed under the harness's `.claude/skills/`, nothing is written under `.agents/`, and nothing is written at the obeya root
- **Cases**: keeps `tests/cases/skills/run-from-inside-a-harness.yaml`

#### Scenario: No obeya
- **WHEN** no ancestor of the working directory holds `gemba.yaml`
- **THEN** the command exits 1, reports that no gemba config was found, and writes nothing
- **Cases**: keeps `tests/cases/skills/no-obeya.yaml`

#### Scenario: Personal providers leave the obeya skills
- **WHEN** `gemba.yaml` declares `agent_providers: [claude]`, `gemba.local.yaml` declares `agent_providers: [agents]`, and `gemba skills update` runs at the obeya root
- **THEN** the obeya skills are written under `.claude/skills/` and no `.agents/` folder is created
- **Cases**: keeps `tests/cases/skills/personal-providers-leave-the-obeya-skills.yaml`

## REMOVED Requirements

### Requirement: Update is idempotent and respects hand edits
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Update
writes what is missing or outdated" and "Update keeps a skill edited by hand".

## ADDED Requirements

### Requirement: Update writes what is missing or outdated
For each registered skill and provider, `gemba skills update` SHALL write a missing
skill, rewrite an outdated one (it differs from what the package writes and its
`contentHash` matches its own content) and keep an unchanged one (identical to what
the package writes, `generatedBy` aside). It SHALL print one line per skill and
provider with its action, `written`, `updated`, `kept` or `overwritten`, and its path
relative to the obeya root. A second run SHALL leave the tree as the first left it.

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
- **Cases**: keeps `tests/cases/skills/outdated-skill-is-refreshed.yaml`

### Requirement: Update keeps a skill edited by hand
A skill whose `contentHash` is absent or does not match its own content is edited by
hand. `gemba skills update` SHALL leave it as it is and report it `kept`, saying that
`--force` overwrites it; with `--force` it SHALL overwrite it and report it
`overwritten`.

#### Scenario: Edited skill is kept and reported
- **WHEN** a skill on disk has no `contentHash` or one that does not match its own content
- **THEN** the file is left byte for byte as it was, the output reports it as `kept` because it was edited by hand and says that `--force` overwrites it, and the command exits 0
- **Cases**: keeps `tests/cases/skills/edited-skill-is-kept-and-reported.yaml`

#### Scenario: Edited skill is overwritten on request
- **WHEN** `gemba skills update --force` runs with an edited skill on disk
- **THEN** the file is replaced with the current content and the output reports `overwritten`
- **Cases**: keeps `tests/cases/skills/edited-skill-is-overwritten-on-request.yaml`
