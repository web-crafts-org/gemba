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
the line `harnesses/`, a `.gitattributes` holding the lines `*.md text eol=lf` and
`*.yaml text eol=lf`, so that the files gemba owns keep LF on every platform whatever
`core.autocrlf` says, and every registered skill whose scope includes the tasks repo
under the skills folder of each selected provider, with the content and the
provenance that `gemba skills update` writes. It SHALL print one line per path it
wrote, `written` followed by the path relative to the new root, in the order written,
the config, the `.gitignore`, the `.gitattributes` and the `tasks/` folder before the
skills, and a final line naming the next step, the guided configuration through the
agent, and SHALL exit 0. The command SHALL ask nothing on the terminal.

#### Scenario: Tasks repo scaffolded in the working directory
- **WHEN** `gemba init` runs in an empty folder with no `--providers`
- **THEN** the folder holds `gemba.yaml` with the `default` workstream as the default and `agent_providers` listing every known provider, `.gitignore` with `harnesses/`, `.gitattributes` with the two `eol=lf` lines, `tasks/.gitkeep` and the tasks-repo skills under `.claude/skills/` and `.agents/skills/`, the output lists each path as `written` and ends with the next step, and the command exits 0
- **Cases**: modifies `tests/cases/init/tasks-repo-scaffolded.yaml`

#### Scenario: Tasks repo scaffolded at a given path
- **WHEN** `gemba init acme-tasks` runs and `acme-tasks` does not exist
- **THEN** the folder is created, holds the same files, and nothing is written in the working directory itself
- **Cases**: modifies `tests/cases/init/scaffolded-at-a-path.yaml`

#### Scenario: Scaffolded config accepted by every command
- **WHEN** a task is created in the `default` workstream right after `gemba init`
- **THEN** the task file appears under `tasks/default/` with the ref `TASK-1`
- **Cases**: keeps `tests/cases/init/scaffolded-config-accepted.yaml`

### Requirement: Init converges
Run on a folder that already holds `gemba.yaml`, or that holds part of the layout,
`gemba init` SHALL write only what is missing and SHALL report what it found: an
existing `gemba.yaml` is never rewritten and is reported as `kept`; a `.gitignore`
that lacks the `harnesses/` line gets the line appended and is reported as `updated`,
one that has it is `kept`; a `.gitattributes` that lacks one of its two lines gets the
missing lines appended and is reported as `updated`, one that has both is `kept`; a
missing `tasks/.gitkeep` is written; a skill already on disk is `kept` whatever its
state, since refreshing it is the work of `gemba skills update`. The providers SHALL
be read from the existing config, which the command validates before writing
anything: an invalid config, or one that declares no `agent_providers`, SHALL be
refused with its problem and nothing written. `--providers` SHALL be refused when
`gemba.yaml` exists, since the command never edits it. Running the command twice
SHALL leave the tree identical after the second run.

#### Scenario: Second run changes nothing
- **WHEN** `gemba init` runs a second time with nothing changed in between
- **THEN** every path is reported as `kept`, the tree is identical and the command exits 0
- **Cases**: modifies `tests/cases/init/second-run-changes-nothing.yaml` (the `.gitattributes` is among the paths reported `kept`)

#### Scenario: Missing pieces completed
- **WHEN** `gemba init` runs in a folder holding a valid `gemba.yaml` with `agent_providers: [claude]`, a `.gitignore` without the `harnesses/` line, a `.gitattributes` holding only `*.md text eol=lf`, and no `tasks/` folder or skills
- **THEN** `gemba.yaml` is kept byte for byte, the line is appended to `.gitignore`, the `*.yaml` line is appended to `.gitattributes`, `tasks/.gitkeep` and the skills of `claude` are written, no `.agents/` folder appears, and the output reports `kept gemba.yaml`, `updated .gitignore`, `updated .gitattributes` and `written` for the rest
- **Cases**: modifies `tests/cases/init/missing-pieces-completed.yaml`

#### Scenario: Existing skill kept whatever its state
- **WHEN** `gemba init` runs in a tasks repo where one skill was edited by hand and another was written by an older version
- **THEN** both files are left byte for byte as they were and reported as `kept`
- **Cases**: keeps `tests/cases/init/existing-skill-kept.yaml`

#### Scenario: Providers flag refused with an existing config
- **WHEN** `gemba init --providers agents` runs in a folder that holds `gemba.yaml`
- **THEN** the command exits 1, says that the config already declares the providers and that `gemba.yaml` is edited by hand, and writes nothing
- **Cases**: keeps `tests/cases/init/providers-refused-with-existing-config.yaml`

#### Scenario: Invalid existing config refused
- **WHEN** `gemba init` runs in a folder whose `gemba.yaml` declares two workstreams with the same prefix, or declares no `agent_providers`
- **THEN** the command exits 1, reports the problem as every command reports it, and writes nothing, not even `.gitignore` or `tasks/`
- **Cases**: keeps `tests/cases/init/invalid-config-refused.yaml`
