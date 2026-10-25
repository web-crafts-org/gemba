# Spec Delta

## MODIFIED Requirements

### Requirement: Init scaffolds a tasks repo
`gemba init [path]` SHALL make `path`, or the working directory when `path` is
omitted, a tasks repo, creating the folder when it does not exist. It SHALL write a
`gemba.yaml` that every command accepts: `default_workstream: default`, a workstream
catalogue holding the one workstream `default`, with the prefix `TASK` and a
description that names it as the place of work that fits no other workstream, and
`agent_providers` listing the providers selected as the next requirement says. It
SHALL write the `tasks/` folder, kept by an empty `.gitkeep`, a `.gitignore` holding
the lines `harnesses/` and `gemba.local.yaml`, so that neither the harnesses nor the
personal config reach the history of the tasks repo, a `.gitattributes` holding the
lines `*.md text eol=lf` and `*.yaml text eol=lf`, so that the files gemba owns keep
LF on every platform whatever `core.autocrlf` says, and every registered skill whose
scope includes the tasks repo under the skills folder of each selected provider, with
the content and the provenance that `gemba skills update` writes. It SHALL NOT write a
`gemba.local.yaml`. It SHALL print one line per path it wrote, `written` followed by
the path relative to the new root, in the order written, the config, the
`.gitignore`, the `.gitattributes` and the `tasks/` folder before the skills, and a
final line naming the next step, the guided configuration through the agent, and
SHALL exit 0. The command SHALL ask nothing on the terminal.

#### Scenario: Tasks repo scaffolded in the working directory
- **WHEN** `gemba init` runs in an empty folder with no `--providers`
- **THEN** the folder holds `gemba.yaml` with the `default` workstream as the default and `agent_providers` listing every known provider, `.gitignore` with `harnesses/` and `gemba.local.yaml`, `.gitattributes` with the two `eol=lf` lines, `tasks/.gitkeep` and the tasks-repo skills under `.claude/skills/` and `.agents/skills/`, and no `gemba.local.yaml`; the output lists each path as `written` and ends with the next step, and the command exits 0
- **Cases**: modifies `tests/cases/init/tasks-repo-scaffolded.yaml` (the `.gitignore` holds the second line and `gemba.local.yaml` is absent)

#### Scenario: Tasks repo scaffolded at a given path
- **WHEN** `gemba init acme-tasks` runs and `acme-tasks` does not exist
- **THEN** the folder is created, holds the same files, and nothing is written in the working directory itself
- **Cases**: modifies `tests/cases/init/scaffolded-at-a-path.yaml` (the `.gitignore` holds the second line)

#### Scenario: Scaffolded config accepted by every command
- **WHEN** a task is created in the `default` workstream right after `gemba init`
- **THEN** the task file appears under `tasks/default/` with the ref `TASK-1`
- **Cases**: keeps `tests/cases/init/scaffolded-config-accepted.yaml`

### Requirement: Init converges
Run on a folder that already holds `gemba.yaml`, or that holds part of the layout,
`gemba init` SHALL write only what is missing and SHALL report what it found: an
existing `gemba.yaml` is never rewritten and is reported as `kept`; a `.gitignore`
that lacks one or both of its two lines gets the missing lines appended, in their
order, and is reported as `updated`, one that has both is `kept`; a `.gitattributes`
that lacks one of its two lines gets the missing lines appended and is reported as
`updated`, one that has both is `kept`; a missing `tasks/.gitkeep` is written; a skill
already on disk is `kept` whatever its state, since refreshing it is the work of
`gemba skills update`. The providers SHALL be read from the shared config, which the
command validates, with the personal config beside it when there is one, before
writing anything: an invalid config, or a shared config that declares no
`agent_providers`, whatever the personal config declares, SHALL be refused with its
problems and nothing written. `--providers` SHALL be refused when `gemba.yaml`
exists, since the command never edits it. Running the command twice SHALL leave the
tree identical after the second run.

#### Scenario: Second run changes nothing
- **WHEN** `gemba init` runs a second time with nothing changed in between
- **THEN** every path is reported as `kept`, the tree is identical and the command exits 0
- **Cases**: keeps `tests/cases/init/second-run-changes-nothing.yaml`

#### Scenario: Missing pieces completed
- **WHEN** `gemba init` runs in a folder holding a valid `gemba.yaml` with `agent_providers: [claude]`, a `.gitignore` with neither of its two lines, a `.gitattributes` holding only `*.md text eol=lf`, and no `tasks/` folder or skills
- **THEN** `gemba.yaml` is kept byte for byte, `harnesses/` and `gemba.local.yaml` are appended to `.gitignore` in that order, the `*.yaml` line is appended to `.gitattributes`, `tasks/.gitkeep` and the skills of `claude` are written, no `.agents/` folder appears, and the output reports `kept gemba.yaml`, `updated .gitignore`, `updated .gitattributes` and `written` for the rest
- **Cases**: modifies `tests/cases/init/missing-pieces-completed.yaml` (both lines are appended to `.gitignore`)

#### Scenario: Personal config ignored in an earlier tasks repo
- **WHEN** `gemba init` runs in a tasks repo made by an earlier version, whose `.gitignore` holds `harnesses/` alone and whose other files are all in place
- **THEN** `gemba.local.yaml` is appended to `.gitignore`, the output reports `updated .gitignore` and every other path as `kept`, and the command exits 0
- **Cases**: adds `tests/cases/init/personal-config-ignored-in-an-earlier-tasks-repo.yaml`

#### Scenario: Existing skill kept whatever its state
- **WHEN** `gemba init` runs in a tasks repo where one skill was edited by hand and another was written by an older version
- **THEN** both files are left byte for byte as they were and reported as `kept`
- **Cases**: keeps `tests/cases/init/existing-skill-kept.yaml`

#### Scenario: Providers flag refused with an existing config
- **WHEN** `gemba init --providers agents` runs in a folder that holds `gemba.yaml`
- **THEN** the command exits 1, says that the config already declares the providers and that `gemba.yaml` is edited by hand, and writes nothing
- **Cases**: keeps `tests/cases/init/providers-refused-with-existing-config.yaml`

#### Scenario: Invalid existing config refused
- **WHEN** `gemba init` runs in a folder whose `gemba.yaml` declares two workstreams with the same prefix, or declares no `agent_providers`, or whose `gemba.local.yaml` declares `organization`
- **THEN** the command exits 1, reports the problem as every command reports it, and writes nothing, not even `.gitignore` or `tasks/`
- **Cases**: modifies `tests/cases/init/invalid-config-refused.yaml` (a case whose personal config declares `organization` is added)

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

#### Scenario: Agent configures a new tasks repo
- **WHEN** the user asks the agent to configure gemba in a tasks repo that holds the scaffolded config
- **THEN** the agent asks the questions in the order above, one per message, proposes the workstreams and the fields from the answers, writes the IDE command and the folder of the repositories into `gemba.local.yaml` and the rest into `gemba.yaml`, verifies both with `gemba config check`, refreshes the skills when the providers changed, and reports the config without committing
- **Cases**: keeps the entry `repo-initialization: Agent configures a new tasks repo` of `tests/not-automated.yaml`

#### Scenario: Agent does not ask what has a default
- **WHEN** the agent runs the guided configuration
- **THEN** it never asks for the branch prefix or for the `context` and `rules` of a process, and names them at the end as edits the `gemba-config` skill makes later
- **Cases**: keeps the entry `repo-initialization: Agent does not ask what has a default` of `tests/not-automated.yaml`

#### Scenario: Guided configuration is used once
- **WHEN** the user asks to add a workstream or a field to a tasks repo already configured
- **THEN** the agent follows the `gemba-config` skill, not the guided configuration
- **Cases**: keeps the entry `repo-initialization: Guided configuration is used once` of `tests/not-automated.yaml`
