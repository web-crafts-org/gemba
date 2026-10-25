# repo-initialization Specification

## Purpose

How an obeya is started: what `gemba init` writes so that every command runs from
the first second, how it converges when run again, what it refuses, and how the
`gemba-init` skill guides a person through the first configuration of the result.

## Requirements

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

#### Scenario: Scaffolded config accepted by every command
- **WHEN** a task is created in the `default` workstream right after `gemba init`
- **THEN** the task file appears under `tasks/default/` with the ref `TASK-1`

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

### Requirement: Providers of the scaffold
`--providers` SHALL take a comma-separated list of provider identifiers the CLI knows.
When it is absent, the scaffold SHALL select every known provider in the order the CLI
lists them. The written config SHALL declare exactly the selected providers in the
order given, and the skills SHALL be written for those providers only. An unknown or
repeated identifier SHALL be refused: the command exits 1, names the identifier and the
known providers, and writes nothing.

#### Scenario: Providers selected
- **WHEN** `gemba init --providers claude` runs in an empty folder
- **THEN** `gemba.yaml` declares `agent_providers: [claude]`, the skills appear under `.claude/skills/` and no `.agents/` folder is created

#### Scenario: Unknown or repeated provider refused
- **WHEN** `gemba init --providers claude,cursor` or `gemba init --providers claude,claude` runs
- **THEN** the command exits 1, names `cursor` or the repeated `claude` and the known providers, and the folder is untouched

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

#### Scenario: Missing pieces completed
- **WHEN** `gemba init` runs in a folder holding a valid `gemba.yaml` with `agent_providers: [claude]`, a `.gitignore` with none of its three lines, a `.gitattributes` holding only `*.md text eol=lf`, and no `tasks/` folder or skills
- **THEN** `gemba.yaml` is kept byte for byte, `harnesses/`, `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the `*.yaml` line is appended to `.gitattributes`, `tasks/.gitkeep` and the skills of `claude` are written, no `.agents/` folder appears, and the output reports `kept gemba.yaml`, `updated .gitignore`, `updated .gitattributes` and `written` for the rest

#### Scenario: Personal config ignored in an earlier obeya
- **WHEN** `gemba init` runs in an obeya made by an earlier version, whose `.gitignore` holds `harnesses/` alone and whose other files are all in place
- **THEN** `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0

#### Scenario: Draft ignored in an earlier obeya
- **WHEN** `gemba init` runs in an obeya whose `.gitignore` holds `harnesses/` and `gemba.local.yaml` and whose other files are all in place, as the version before this change left it
- **THEN** `/update.md` is appended to `.gitignore`, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0

#### Scenario: Existing skill kept whatever its state
- **WHEN** `gemba init` runs in an obeya where one skill was edited by hand and another was written by an older version
- **THEN** both files are left byte for byte as they were and reported as `kept`

### Requirement: Init refuses an existing config it cannot use
`gemba init` SHALL read the providers from the shared config, validated with the
personal config beside it, before writing anything: an invalid config, or a shared
config that declares no `agent_providers`, whatever the personal one declares, SHALL
be refused with its problems, nothing written. `--providers` SHALL be refused when
`gemba.yaml` exists, since the command never edits it.

#### Scenario: Providers flag refused with an existing config
- **WHEN** `gemba init --providers agents` runs in a folder that holds `gemba.yaml`
- **THEN** the command exits 1, says that the config already declares the providers and that `gemba.yaml` is edited by hand, and writes nothing

#### Scenario: Invalid existing config refused
- **WHEN** `gemba init` runs in a folder whose `gemba.yaml` declares two workstreams with the same prefix, or declares no `agent_providers`, or whose `gemba.local.yaml` declares `obeya`
- **THEN** the command exits 1, reports the problem as every command reports it, and writes nothing, not even `.gitignore` or `tasks/`

### Requirement: Init refuses a nested obeya
When a strict ancestor of the folder to initialize holds `gemba.yaml`, `gemba init`
SHALL exit 1, name the obeya found, and write nothing, so that no obeya is
ever created inside another one, a harness included.

#### Scenario: Nested obeya refused
- **WHEN** `gemba init` runs from a subfolder of an obeya, or `gemba init sub` runs at its root
- **THEN** the command exits 1, names the root of the obeya found, and the tree is untouched

### Requirement: Init runs no git
`gemba init` SHALL NOT run git: it creates no repository and no commit. Making the
obeya a git repository, and committing what `init` wrote, is the person's step.

#### Scenario: No repository created
- **WHEN** `gemba init` runs in an empty folder
- **THEN** no `.git` folder exists afterwards

### Requirement: The init skill configures a new obeya once
The `gemba-init` skill SHALL be the one process an agent follows to configure an obeya
that `gemba init` just created, and its description SHALL make an agent choose it when
the user asks to configure, set up or customize gemba for the first time. It SHALL be
used for that first configuration only: any later edit follows the `gemba-config`
skill.

#### Scenario: Guided configuration is used once
- **WHEN** the user asks to add a workstream or a field to an obeya already configured
- **THEN** the agent follows the `gemba-config` skill, not the guided configuration

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

### Requirement: What the guided configuration leaves for later
The agent SHALL NOT ask for what has a default or comes from use, the branch prefix
and the `context` and `rules` of the processes, and SHALL name them at the end as
later edits of the `gemba-config` skill.

#### Scenario: Agent does not ask what has a default
- **WHEN** the agent runs the guided configuration
- **THEN** it never asks for the branch prefix or for the `context` and `rules` of a process, and names them at the end as edits the `gemba-config` skill makes later

### Requirement: The guided configuration writes both files
The agent SHALL then write the answers through the `gemba-config` skill, the IDE
command and the repositories folder into `gemba.local.yaml`, which it creates, and
every other answer into `gemba.yaml`; check them and refresh the skills; and report
the resulting config, saying that `gemba.local.yaml` stays on this machine and that
git ignores it, without committing.

#### Scenario: Agent configures a new obeya
- **WHEN** the user asks the agent to configure gemba in an obeya that holds the scaffolded config
- **THEN** the agent asks the questions in the order above, one per message, proposes the workstreams and the fields from the answers, writes the IDE command and the folder of the repositories into `gemba.local.yaml` and the rest into `gemba.yaml`, verifies both with `gemba config check`, refreshes the skills when the providers changed, and reports the config without committing
