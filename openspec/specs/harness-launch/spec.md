# harness-launch Specification

## Purpose

Launching a task creates its harness, the folder of one run where the user and the
agent work: its own git repository, the root the IDE opens, with the identity of the
run, a link to the task, a guide and the skills the agent needs inside.

## Requirements

### Requirement: Launch creates the harness of a task
`gemba harness launch <ref>` SHALL resolve the task with that ref anywhere under
`tasks/`, archives included, and SHALL create its harness at
`harnesses/<workstream>/<stem>/` under the tasks repo root, where `<stem>` is the task
filename without `.md`. The command SHALL refuse, writing nothing, when no task has that
ref, when the task is archived, or when its status is `done`, saying in that case that
`gemba mark` moves it to `open` or `in-progress` first. The harness SHALL hold:
`harness.yaml`; `task.md`; the guide under the filename of every declared agent
provider; the harness-scoped skills under the skills folder of every declared agent
provider; empty `notes/`, `assets/` and `worktrees/` folders; and a `.gitignore` that
excludes `worktrees/`. The command SHALL print the harness path relative to the tasks
repo root. A folder already present at the harness path without a `harness.yaml` SHALL
be completed, never emptied: existing files are left as they are.

#### Scenario: Harness layout created
- **WHEN** `gemba harness launch SUP-1` runs for an open task `tasks/support/2026-09-30-SUP-1-login-fails.md` in a tasks repo declaring `agent_providers: [claude, agents]`
- **THEN** `harnesses/support/2026-09-30-SUP-1-login-fails/` holds `harness.yaml`, `task.md`, `CLAUDE.md`, `AGENTS.md`, `.claude/skills/gemba-harness/SKILL.md`, `.agents/skills/gemba-harness/SKILL.md`, `notes/`, `assets/`, `worktrees/` and a `.gitignore` containing `worktrees/`, the command prints `harnesses/support/2026-09-30-SUP-1-login-fails` and exits 0

#### Scenario: Unknown ref refused
- **WHEN** no task under `tasks/` has the ref given
- **THEN** the command exits 1, reports that no task has that ref, and writes nothing

#### Scenario: Archived or done task refused
- **WHEN** the task with that ref is under an `archive/` folder, or its status is `done`
- **THEN** the command exits 1, reports why the task cannot be launched, names `gemba mark` for the `done` case, and writes nothing

#### Scenario: No providers declared
- **WHEN** the gemba config declares no `agent_providers`
- **THEN** the command exits 1, reports that no agent providers are declared, names the known providers, and writes nothing

### Requirement: The harness config is the identity of the run
`harness.yaml` at the harness root SHALL be written by `launch` only and SHALL hold, in
this order: `task`, the task file path relative to the tasks repo root; `ref`;
`workstream`; `agent_providers`, the providers the harness carries a guide and skills
for, as declared in the gemba config at launch; `launched_at`, the launch date as an
ISO date; and `gemba_version`, the version of the package that wrote it. No gemba
command SHALL modify it afterwards, and agents SHALL NOT edit it. A command that acts
on a harness SHALL resolve the harness root as the nearest folder at or above the
working directory that holds `harness.yaml`, or as the folder given with `--harness`,
and SHALL refuse when neither yields a harness.

#### Scenario: Harness config written
- **WHEN** `SUP-1` of workstream `support` is launched on 2026-09-30 by package version V with `agent_providers: [claude, agents]`
- **THEN** `harness.yaml` is exactly `task: tasks/support/2026-09-30-SUP-1-login-fails.md`, `ref: SUP-1`, `workstream: support`, `agent_providers: [claude, agents]`, `launched_at: 2026-09-30`, `gemba_version: "V"`, one key per line in that order

#### Scenario: Harness resolved from the working directory
- **WHEN** a harness verb other than `launch` runs from a folder inside a harness without `--harness`
- **THEN** it acts on the harness whose `harness.yaml` is the nearest at or above that folder

#### Scenario: No harness found
- **WHEN** a harness verb other than `launch` runs outside any harness and without `--harness`
- **THEN** it exits 1, reports that no harness was found, and writes nothing

### Requirement: The task is reachable from inside the harness
`launch` SHALL create `task.md` at the harness root as a relative symbolic link to the
task file, so that the task can be read from inside the harness without leaving it.
Commands SHALL resolve the task from `harness.yaml`, never through the link.

#### Scenario: Task linked
- **WHEN** `SUP-1` of workstream `support` is launched
- **THEN** `task.md` in the harness is a symbolic link whose target is `../../../tasks/support/2026-09-30-SUP-1-login-fails.md` and reading it yields the task file

#### Scenario: Agent reads the task through the link
- **WHEN** the agent inside a harness needs the task
- **THEN** it reads `task.md` and does not browse `tasks/` above the harness

### Requirement: The guide and the skills are written per provider
`launch` SHALL write the guide under the filename of each provider in
`agent_providers` of the gemba config (`CLAUDE.md` for `claude`, `AGENTS.md` for
`agents`), with the same content for every provider, and SHALL write the skills whose
scope includes the harness under the skills folder of each of those providers, with
the provenance that `gemba skills update` writes. A provider the config does not list
SHALL get neither.

#### Scenario: Guide per declared provider
- **WHEN** the config declares `agent_providers: [claude]` only
- **THEN** the harness holds `CLAUDE.md` and `.claude/skills/gemba-harness/SKILL.md`, and neither `AGENTS.md` nor `.agents/` exists

#### Scenario: Harness skills carry their provenance
- **WHEN** a harness is launched by package version V
- **THEN** each skill written in it holds `metadata.generatedBy: "V"` and `metadata.contentHash`, like a skill written by `gemba skills update`

### Requirement: The harness is a local git repository
`launch` SHALL initialize a git repository at the harness root with branch `main` and
no remote, and SHALL commit everything it wrote as the first commit. The tasks repo
SHALL ignore `harnesses/` as a whole, so the harness repository never reaches the tasks
repo history.

#### Scenario: Harness repository initialized
- **WHEN** a harness is launched
- **THEN** the harness holds a `.git/` folder whose `HEAD` points at `refs/heads/main`, and the repository history has exactly one commit, which includes `harness.yaml`, the guide, the skills, `.gitignore` and `task.md`

#### Scenario: Harnesses ignored by the tasks repo
- **WHEN** the tasks repo is at this change or later
- **THEN** its `.gitignore` lists `harnesses/` and no `runs/` folder is tracked

### Requirement: Launching marks the start of work
On every launch, whether it creates the harness or finds it already there, `launch`
SHALL move the task's `status` from `open` to `in-progress` and its `updated_at` to
today, through the same rule table `gemba mark` applies, rewriting only the
frontmatter and leaving the body byte for byte, and SHALL report the transition. A
task that is `in-progress` or `blocked` SHALL be left as it is and the command SHALL
say so. `updated_at` SHALL never move backwards.

#### Scenario: Open task started
- **WHEN** an `open` task with `updated_at: 2026-09-30` is launched on a later day
- **THEN** its frontmatter reads `status: in-progress` and `updated_at` is today, its body is unchanged, and the output reports the transition

#### Scenario: Task already in progress or blocked
- **WHEN** an `in-progress` or `blocked` task is launched
- **THEN** its frontmatter is unchanged and the output says the status was left as it was

#### Scenario: Reopened task started on relaunch
- **WHEN** a launched task is marked `open` and `gemba harness launch` runs again for it
- **THEN** the harness is left as it was, the task's frontmatter reads `status: in-progress` with `updated_at` today, and the output reports `status: open -> in-progress`

### Requirement: Launch opens the IDE
When the gemba config declares `ide`, `launch` SHALL split it as a shell would, append
the absolute harness path as the last argument, start it without waiting for it to
finish, and print the command line it started. With `--no-open` it SHALL start nothing
and print no such line. Without `ide` in the config it SHALL start nothing and print
the harness path only.

#### Scenario: IDE opened
- **WHEN** the config declares `ide: "code -n"` and a task is launched without `--no-open`
- **THEN** the output holds a line with `code -n` followed by the absolute harness path

#### Scenario: Open skipped
- **WHEN** a task is launched with `--no-open`
- **THEN** no IDE command line appears in the output and the harness is created as usual

#### Scenario: No IDE declared
- **WHEN** the config has no `ide` key and a task is launched without `--no-open`
- **THEN** no IDE command line appears in the output and the harness path is printed

### Requirement: Relaunch opens an existing harness
When the harness of the task already holds a `harness.yaml` and a commit, `launch`
SHALL write nothing in the harness, leave its repository as it is, say that the
harness already exists, apply the status rule above to the task, and open the IDE as
above.

#### Scenario: Relaunch
- **WHEN** `gemba harness launch SUP-1 --no-open` runs twice
- **THEN** the second run reports that the harness already exists and that the status was left as it was, the tree is identical to the one after the first run, and the exit code is 0

### Requirement: Launch by the agent
The `gemba-harness` skill SHALL have the agent, from anywhere inside the tasks repo,
identify the task to launch by its ref, asking the user when the request names a task
ambiguously, run `gemba harness launch <ref>`, relay the printed path, the status
transition and whether the IDE was opened, and stop. The skill SHALL NOT have the agent
create any file of the harness by hand.

#### Scenario: Agent launches a task
- **WHEN** the user asks to launch, start or open the harness of a task
- **THEN** the agent runs the command with the task's ref and relays its output
