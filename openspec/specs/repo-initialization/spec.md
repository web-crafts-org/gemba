# repo-initialization Specification

## Purpose

How an obeya is started: what `gemba init` writes so that every command runs from
the first second, how it converges when run again, what it refuses, and how the
`gemba-init` skill guides a person through the first configuration of the result.

## Requirements

### Requirement: Init scaffolds a tasks repo
`gemba init [path]` SHALL make `path`, or the working directory when `path` is
omitted, a tasks repo, creating the folder when it does not exist. It SHALL write a
`gemba.yaml` that every command accepts: `default_workstream: default`, a workstream
catalogue holding the one workstream `default`, with the prefix `TASK` and a
description that names it as the place of work that fits no other workstream, and
`agent_providers` listing the providers selected as the next requirement says. It
SHALL write the `tasks/` folder, kept by an empty `.gitkeep`, a `.gitignore` holding
the lines `harnesses/`, `gemba.local.yaml` and `/update.md`, so that neither the
harnesses, nor the personal config, nor the draft of an update left at the root by a
refused record reach the history of the tasks repo, a `.gitattributes` holding the
lines `*.md text eol=lf` and `*.yaml text eol=lf`, so that the files gemba owns keep
LF on every platform whatever `core.autocrlf` says, and every registered skill whose
scope includes the tasks repo under the skills folder of each selected provider, with
the content and the provenance that `gemba skills update` writes. It SHALL NOT write a
`gemba.local.yaml`. It SHALL print one line per path it wrote, `written` followed by
the path relative to the new root, in the order written, the config, the
`.gitignore`, the `.gitattributes` and the `tasks/` folder before the skills, and a
final line naming the next step, the guided configuration through the agent, and
SHALL exit 0. The command SHALL ask nothing on the terminal.

#### Scenario: Obeya scaffolded in the working directory
- **WHEN** `gemba init` runs in an empty folder with no `--providers`
- **THEN** the folder holds `gemba.yaml` with the `default` workstream as the default and `agent_providers` listing every known provider, `.gitignore` with `harnesses/`, `gemba.local.yaml` and `/update.md`, `.gitattributes` with the two `eol=lf` lines, `tasks/.gitkeep` and the tasks-repo skills under `.claude/skills/` and `.agents/skills/`, `gemba-record` and `gemba-migrate` among them, and no `gemba.local.yaml`; the output lists each path as `written` and ends with the next step, and the command exits 0

#### Scenario: Obeya scaffolded at a given path
- **WHEN** `gemba init acme-tasks` runs and `acme-tasks` does not exist
- **THEN** the folder is created, holds the same files, and nothing is written in the working directory itself

#### Scenario: Scaffolded config accepted by every command
- **WHEN** a task is created in the `default` workstream right after `gemba init`
- **THEN** the task file appears under `tasks/default/` with the ref `TASK-1`

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

### Requirement: Init converges
Run on a folder that already holds `gemba.yaml`, or that holds part of the layout,
`gemba init` SHALL write only what is missing and SHALL report what it found: an
existing `gemba.yaml` is never rewritten and is reported as `kept`; a `.gitignore`
that lacks any of its three lines gets the missing lines appended, in their order, and
is reported as `updated`, one that has all three is `kept`; a `.gitattributes` that
lacks one of its two lines gets the missing lines appended and is reported as
`updated`, one that has both is `kept`; a missing `tasks/.gitkeep` is written; a skill
already on disk is `kept` whatever its state, since refreshing it is the work of
`gemba skills update`, and a registered skill missing from disk is written. The
providers SHALL be read from the shared config, which the command validates, with the
personal config beside it when there is one, before writing anything: an invalid
config, or a shared config that declares no `agent_providers`, whatever the personal
config declares, SHALL be refused with its problems and nothing written.
`--providers` SHALL be refused when `gemba.yaml` exists, since the command never edits
it. Running the command twice SHALL leave the tree identical after the second run.

#### Scenario: Second run changes nothing
- **WHEN** `gemba init` runs a second time with nothing changed in between
- **THEN** every path is reported as `kept`, the tree is identical and the command exits 0

#### Scenario: Missing pieces completed
- **WHEN** `gemba init` runs in a folder holding a valid `gemba.yaml` with `agent_providers: [claude]`, a `.gitignore` with none of its three lines, a `.gitattributes` holding only `*.md text eol=lf`, and no `tasks/` folder or skills
- **THEN** `gemba.yaml` is kept byte for byte, `harnesses/`, `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the `*.yaml` line is appended to `.gitattributes`, `tasks/.gitkeep` and the skills of `claude` are written, no `.agents/` folder appears, and the output reports `kept gemba.yaml`, `updated .gitignore`, `updated .gitattributes` and `written` for the rest

#### Scenario: Personal config ignored in an earlier obeya
- **WHEN** `gemba init` runs in a tasks repo made by an earlier version, whose `.gitignore` holds `harnesses/` alone and whose other files are all in place
- **THEN** `gemba.local.yaml` and `/update.md` are appended to `.gitignore` in that order, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0

#### Scenario: Draft ignored in an earlier obeya
- **WHEN** `gemba init` runs in a tasks repo whose `.gitignore` holds `harnesses/` and `gemba.local.yaml` and whose other files are all in place, as the version before this change left it
- **THEN** `/update.md` is appended to `.gitignore`, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0

#### Scenario: Existing skill kept whatever its state
- **WHEN** `gemba init` runs in a tasks repo where one skill was edited by hand and another was written by an older version
- **THEN** both files are left byte for byte as they were and reported as `kept`

#### Scenario: Providers flag refused with an existing config
- **WHEN** `gemba init --providers agents` runs in a folder that holds `gemba.yaml`
- **THEN** the command exits 1, says that the config already declares the providers and that `gemba.yaml` is edited by hand, and writes nothing

#### Scenario: Invalid existing config refused
- **WHEN** `gemba init` runs in a folder whose `gemba.yaml` declares two workstreams with the same prefix, or declares no `agent_providers`, or whose `gemba.local.yaml` declares `organization`
- **THEN** the command exits 1, reports the problem as every command reports it, and writes nothing, not even `.gitignore` or `tasks/`

### Requirement: Init refuses a nested tasks repo
When a strict ancestor of the folder to initialize holds `gemba.yaml`, `gemba init`
SHALL exit 1, name the tasks repo found, and write nothing, so that no tasks repo is
ever created inside another one, a harness included.

#### Scenario: Nested obeya refused
- **WHEN** `gemba init` runs from a subfolder of a tasks repo, or `gemba init sub` runs at its root
- **THEN** the command exits 1, names the root of the tasks repo found, and the tree is untouched

### Requirement: Init runs no git
`gemba init` SHALL NOT run git: it creates no repository and no commit. Making the
tasks repo a git repository, and committing what `init` wrote, is the person's step.

#### Scenario: No repository created
- **WHEN** `gemba init` runs in an empty folder
- **THEN** no `.git` folder exists afterwards

### Requirement: Guided initial configuration
The `gemba-init` skill SHALL be the one process an agent follows to configure a tasks
repo that `gemba init` just created, and its description SHALL carry the phrases that
make an agent choose it when the user asks to configure, set up or customize gemba
for the first time. Following it, the agent SHALL ask one question at a time, in this
order, and skip what the user already said: the name of the organization; the kinds of
work the person does, from which the agent proposes the workstreams, each with a
kebab-case identifier, a prefix of uppercase letters and a description written so that
an agent can tell which work belongs there; which workstream is the default, the
`default` workstream of the scaffold being replaced by the ones the person names
unless they want a catch-all; what the person needs to record per task, from which the
agent proposes the metadata fields, each with one of the four types and whether it is
required; the agent providers, confirming or trimming the ones the scaffold declared;
the command that opens the IDE; and the folder of the repositories, only when the work
involves code. The agent SHALL NOT ask for what has a default or comes from use: the
branch prefix and the `context` and `rules` of the processes, which it mentions at the
end as later edits. It SHALL then write the answers through the `gemba-config` skill,
the IDE command and the folder of the repositories into `gemba.local.yaml`, which it
creates, and every other answer into `gemba.yaml`; check them and refresh the skills;
report the resulting config, saying that `gemba.local.yaml` stays on this machine and
that git ignores it; and SHALL NOT commit. This skill SHALL be used for the first
configuration only: any later edit is the `gemba-config` skill.

#### Scenario: Agent configures a new obeya
- **WHEN** the user asks the agent to configure gemba in a tasks repo that holds the scaffolded config
- **THEN** the agent asks the questions in the order above, one per message, proposes the workstreams and the fields from the answers, writes the IDE command and the folder of the repositories into `gemba.local.yaml` and the rest into `gemba.yaml`, verifies both with `gemba config check`, refreshes the skills when the providers changed, and reports the config without committing

#### Scenario: Agent does not ask what has a default
- **WHEN** the agent runs the guided configuration
- **THEN** it never asks for the branch prefix or for the `context` and `rules` of a process, and names them at the end as edits the `gemba-config` skill makes later

#### Scenario: Guided configuration is used once
- **WHEN** the user asks to add a workstream or a field to a tasks repo already configured
- **THEN** the agent follows the `gemba-config` skill, not the guided configuration
