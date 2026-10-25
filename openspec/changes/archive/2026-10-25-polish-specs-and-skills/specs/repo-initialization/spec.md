# Spec Delta

## REMOVED Requirements

### Requirement: Init scaffolds an obeya
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Init
writes the config of a new obeya" and "Init writes the layout and the skills".

### Requirement: Init converges
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Init
completes what is missing" and "Init refuses an existing config it cannot use".

### Requirement: Guided initial configuration
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The init
skill configures a new obeya once", "The questions of the guided configuration", "What
the guided configuration leaves for later" and "The guided configuration writes both
files".

## ADDED Requirements

### Requirement: Init writes the config of a new obeya
`gemba init [path]` SHALL make `path`, or the working directory, an obeya, creating
the folder when missing, asking nothing on the terminal. It SHALL write a `gemba.yaml`
that every command accepts: `default_workstream: default`, a catalogue holding the one
workstream `default`, with the prefix `TASK` and a description naming it the place of
work no other workstream fits, and `agent_providers` with the providers selected as
the next requirement says. It SHALL NOT write a `gemba.local.yaml`.

#### Scenario: Obeya scaffolded at a given path
- **WHEN** `gemba init acme-tasks` runs and `acme-tasks` does not exist
- **THEN** the folder is created, holds the same files, and nothing is written in the working directory itself
- **Cases**: keeps `tests/cases/init/scaffolded-at-a-path.yaml`

#### Scenario: Scaffolded config accepted by every command
- **WHEN** a task is created in the `default` workstream right after `gemba init`
- **THEN** the task file appears under `tasks/default/` with the ref `TASK-1`
- **Cases**: keeps `tests/cases/init/scaffolded-config-accepted.yaml`

### Requirement: Init writes the layout and the skills
`init` SHALL also write `tasks/.gitkeep`; a `.gitignore` with `harnesses/`,
`gemba.local.yaml` and `/update.md`, the draft a refused record leaves; a
`.gitattributes` with `*.md text eol=lf` and `*.yaml text eol=lf`, so gemba's files
keep LF whatever `core.autocrlf` says; and the obeya skills of each selected provider,
as `gemba skills update` writes them. It SHALL print `written` and the path of each,
in that order, then the next step, the guided configuration through the agent, and
exit 0.

#### Scenario: Obeya scaffolded in the working directory
- **WHEN** `gemba init` runs in an empty folder with no `--providers`
- **THEN** the folder holds `gemba.yaml` with the `default` workstream as the default and `agent_providers` listing every known provider, `.gitignore` with `harnesses/`, `gemba.local.yaml` and `/update.md`, `.gitattributes` with the two `eol=lf` lines, `tasks/.gitkeep` and the obeya skills under `.claude/skills/` and `.agents/skills/`, `gemba-record` and `gemba-migrate` among them, and no `gemba.local.yaml`; the output lists each path as `written` and ends with the next step, and the command exits 0
- **Cases**: keeps `tests/cases/init/obeya-scaffolded.yaml`

### Requirement: Init completes what is missing
Run where `gemba.yaml` or part of the layout already exists, `gemba init` SHALL write
only what is missing and report each path: `gemba.yaml` is never rewritten, `kept`; a
`.gitignore` or `.gitattributes` lacking some of its lines gets them appended in
order, `updated`, else `kept`; a missing `tasks/.gitkeep` or registered skill is
written; a skill on disk is `kept` whatever its state, as refreshing it is the work of
`gemba skills update`. A second run SHALL leave the tree identical.

#### Scenario: Second run changes nothing
- **WHEN** `gemba init` runs a second time with nothing changed in between
- **THEN** every path is reported as `kept`, the tree is identical and the command exits 0
- **Cases**: keeps `tests/cases/init/second-run-changes-nothing.yaml`

#### Scenario: Missing pieces completed
- **WHEN** `gemba init` runs in a folder holding a valid `gemba.yaml` with `agent_providers: [claude]`, a `.gitignore` with none of its three lines, a `.gitattributes` holding only `*.md text eol=lf`, and no `tasks/` folder or skills
- **THEN** `gemba.yaml` is kept byte for byte, `harnesses/`, `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the `*.yaml` line is appended to `.gitattributes`, `tasks/.gitkeep` and the skills of `claude` are written, no `.agents/` folder appears, and the output reports `kept gemba.yaml`, `updated .gitignore`, `updated .gitattributes` and `written` for the rest
- **Cases**: keeps `tests/cases/init/missing-pieces-completed.yaml`

#### Scenario: Personal config ignored in an earlier obeya
- **WHEN** `gemba init` runs in an obeya made by an earlier version, whose `.gitignore` holds `harnesses/` alone and whose other files are all in place
- **THEN** `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0
- **Cases**: keeps `tests/cases/init/personal-config-ignored-in-an-earlier-obeya.yaml`

#### Scenario: Draft ignored in an earlier obeya
- **WHEN** `gemba init` runs in an obeya whose `.gitignore` holds `harnesses/` and `gemba.local.yaml` and whose other files are all in place, as the version before this change left it
- **THEN** `/update.md` is appended to `.gitignore`, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0
- **Cases**: keeps `tests/cases/init/draft-ignored-in-an-earlier-obeya.yaml`

#### Scenario: Existing skill kept whatever its state
- **WHEN** `gemba init` runs in an obeya where one skill was edited by hand and another was written by an older version
- **THEN** both files are left byte for byte as they were and reported as `kept`
- **Cases**: keeps `tests/cases/init/existing-skill-kept.yaml`

### Requirement: Init refuses an existing config it cannot use
`gemba init` SHALL read the providers from the shared config, validated with the
personal config beside it, before writing anything: an invalid config, or a shared
config that declares no `agent_providers`, whatever the personal one declares, SHALL
be refused with its problems, nothing written. `--providers` SHALL be refused when
`gemba.yaml` exists, since the command never edits it.

#### Scenario: Providers flag refused with an existing config
- **WHEN** `gemba init --providers agents` runs in a folder that holds `gemba.yaml`
- **THEN** the command exits 1, says that the config already declares the providers and that `gemba.yaml` is edited by hand, and writes nothing
- **Cases**: keeps `tests/cases/init/providers-refused-with-existing-config.yaml`

#### Scenario: Invalid existing config refused
- **WHEN** `gemba init` runs in a folder whose `gemba.yaml` declares two workstreams with the same prefix, or declares no `agent_providers`, or whose `gemba.local.yaml` declares `obeya`
- **THEN** the command exits 1, reports the problem as every command reports it, and writes nothing, not even `.gitignore` or `tasks/`
- **Cases**: keeps `tests/cases/init/invalid-config-refused.yaml`

### Requirement: The init skill configures a new obeya once
The `gemba-init` skill SHALL be the one process an agent follows to configure an obeya
that `gemba init` just created, and its description SHALL make an agent choose it when
the user asks to configure, set up or customize gemba for the first time. It SHALL be
used for that first configuration only: any later edit follows the `gemba-config`
skill.

#### Scenario: Guided configuration is used once
- **WHEN** the user asks to add a workstream or a field to an obeya already configured
- **THEN** the agent follows the `gemba-config` skill, not the guided configuration
- **Cases**: keeps the entry `repo-initialization: Guided configuration is used once` of `tests/not-automated.yaml`

### Requirement: The questions of the guided configuration
Following the `gemba-init` skill, the agent SHALL ask one question at a time, in this
order, skipping what the user already said: what this obeya holds, after saying what
an obeya is, to propose its `obeya` name; the kinds of work, to propose workstreams,
each with an identifier, a prefix and a description; the default workstream; what to
record per task, to propose typed fields; the agent providers; the IDE command; and
the repositories folder, only for work with code.

#### Scenario: Obeya explained before its name
- **WHEN** the agent asks its first question of the guided configuration
- **THEN** it says what an obeya is, the room where one part of the person's work is kept in sight, drawn as they choose, such as the organization they work for, a project, a team inside a company or a whole company, asks what this one holds, and proposes the `obeya` name from the answer as a kebab-case name
- **Cases**: keeps the entry `repo-initialization: Obeya explained before its name` of `tests/not-automated.yaml`

### Requirement: What the guided configuration leaves for later
The agent SHALL NOT ask for what has a default or comes from use, the branch prefix
and the `context` and `rules` of the processes, and SHALL name them at the end as
later edits of the `gemba-config` skill.

#### Scenario: Agent does not ask what has a default
- **WHEN** the agent runs the guided configuration
- **THEN** it never asks for the branch prefix or for the `context` and `rules` of a process, and names them at the end as edits the `gemba-config` skill makes later
- **Cases**: keeps the entry `repo-initialization: Agent does not ask what has a default` of `tests/not-automated.yaml`

### Requirement: The guided configuration writes both files
The agent SHALL then write the answers through the `gemba-config` skill, the IDE
command and the repositories folder into `gemba.local.yaml`, which it creates, and
every other answer into `gemba.yaml`; check them and refresh the skills; and report
the resulting config, saying that `gemba.local.yaml` stays on this machine and that
git ignores it, without committing.

#### Scenario: Agent configures a new obeya
- **WHEN** the user asks the agent to configure gemba in an obeya that holds the scaffolded config
- **THEN** the agent asks the questions in the order above, one per message, proposes the workstreams and the fields from the answers, writes the IDE command and the folder of the repositories into `gemba.local.yaml` and the rest into `gemba.yaml`, verifies both with `gemba config check`, refreshes the skills when the providers changed, and reports the config without committing
- **Cases**: keeps the entry `repo-initialization: Agent configures a new obeya` of `tests/not-automated.yaml`
