# Spec Delta

## MODIFIED Requirements

### Requirement: The guide and the skills are written per provider
The providers of a launch SHALL be the `agent_providers` of the personal config when
it declares them, else those of the shared config. `launch` SHALL write, for each of
them, the guide under its filename (`CLAUDE.md` for `claude`, `AGENTS.md` for
`agents`), the same for every provider, and the skills whose scope includes the
harness under its skills folder, with the provenance `gemba skills update` writes. Any
other provider SHALL get neither, and the skills of the obeya SHALL NOT be touched.

#### Scenario: Guide per declared provider
- **WHEN** the config declares `agent_providers: [claude]` only
- **THEN** the harness holds `CLAUDE.md` and `.claude/skills/gemba-harness/SKILL.md`, and neither `AGENTS.md` nor `.agents/` exists
- **Cases**: keeps `tests/cases/harness/guide-per-declared-provider.yaml`

#### Scenario: Harness skills carry their provenance
- **WHEN** a harness is launched by package version V
- **THEN** each skill written in it holds `metadata.generatedBy: "V"` and `metadata.contentHash`, like a skill written by `gemba skills update`
- **Cases**: keeps `tests/cases/harness/harness-skills-carry-their-provenance.yaml`

#### Scenario: Harness launched for the personal providers
- **WHEN** `gemba.yaml` declares `agent_providers: [claude, agents]`, `gemba.local.yaml` declares `agent_providers: [claude]`, and `SUP-1` is launched
- **THEN** the harness holds `CLAUDE.md` and `.claude/skills/gemba-harness/SKILL.md`, neither `AGENTS.md` nor `.agents/` exists in it, its `harness.yaml` reads `agent_providers: [claude]`, and the skills folders of the obeya are as they were
- **Cases**: keeps `tests/cases/harness/harness-launched-for-the-personal-providers.yaml`

## REMOVED Requirements

### Requirement: Launch creates the harness of a task
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Launch
finds a task it can launch" and "Launch creates the layout of the harness".

### Requirement: The harness config is the identity of the run
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The
harness config is written once" and "A command finds its harness".

### Requirement: Launch opens the IDE
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Launch
starts the IDE" and "Launch without opening the IDE".

## ADDED Requirements

### Requirement: Launch finds a task it can launch
`gemba harness launch <ref>` SHALL resolve the task with that ref anywhere under
`tasks/`, archives included. It SHALL refuse, writing nothing, when no task has that
ref, when the task is archived, when its status is `done`, saying then that
`gemba mark` moves it to `open` or `in-progress` first, and when no agent providers
are declared, naming the known ones.

#### Scenario: Unknown ref refused
- **WHEN** no task under `tasks/` has the ref given
- **THEN** the command exits 1, reports that no task has that ref, and writes nothing
- **Cases**: keeps `tests/cases/harness/unknown-ref-refused.yaml`

#### Scenario: Archived or done task refused
- **WHEN** the task with that ref is under an `archive/` folder, or its status is `done`
- **THEN** the command exits 1, reports why the task cannot be launched, names `gemba mark` for the `done` case, and writes nothing
- **Cases**: keeps `tests/cases/harness/archived-or-done-task-refused.yaml`

#### Scenario: No providers declared
- **WHEN** the gemba config declares no `agent_providers`
- **THEN** the command exits 1, reports that no agent providers are declared, names the known providers, and writes nothing
- **Cases**: keeps `tests/cases/harness/no-providers-declared.yaml`

### Requirement: Launch creates the layout of the harness
`launch` SHALL create the harness at `harnesses/<workstream>/<stem>/` under the obeya
root, `<stem>` being the task filename without `.md`, holding `harness.yaml`,
`task.md`, the guide and the harness skills of every provider of the launch, empty
`notes/`, `assets/` and `worktrees/` folders, and a `.gitignore` that excludes
`worktrees/`, and SHALL print its path relative to the obeya root. A folder already at
that path without `harness.yaml` SHALL be completed, never emptied.

#### Scenario: Harness layout created
- **WHEN** `gemba harness launch SUP-1` runs for an open task `tasks/support/2026-09-30-SUP-1-login-fails.md` in an obeya declaring `agent_providers: [claude, agents]`
- **THEN** `harnesses/support/2026-09-30-SUP-1-login-fails/` holds `harness.yaml`, `task.md`, `CLAUDE.md`, `AGENTS.md`, `.claude/skills/gemba-harness/SKILL.md`, `.agents/skills/gemba-harness/SKILL.md`, `notes/`, `assets/`, `worktrees/` and a `.gitignore` containing `worktrees/`, the command prints `harnesses/support/2026-09-30-SUP-1-login-fails` and exits 0
- **Cases**: keeps `tests/cases/harness/harness-layout-created.yaml`

### Requirement: The harness config is written once
`harness.yaml` at the harness root SHALL be written by `launch` only and hold, in this
order: `task`, the task file path relative to the obeya root; `ref`; `workstream`;
`agent_providers`, the providers of the launch; `launched_at`, the launch date as an
ISO date; and `gemba_version`, the version of the package that wrote it. No gemba
command SHALL modify it afterwards, and agents SHALL NOT edit it.

#### Scenario: Harness config written
- **WHEN** `SUP-1` of workstream `support` is launched on 2026-09-30 by package version V with `agent_providers: [claude, agents]`
- **THEN** `harness.yaml` is exactly `task: tasks/support/2026-09-30-SUP-1-login-fails.md`, `ref: SUP-1`, `workstream: support`, `agent_providers: [claude, agents]`, `launched_at: 2026-09-30`, `gemba_version: "V"`, one key per line in that order
- **Cases**: keeps `tests/cases/harness/harness-config-written.yaml`

### Requirement: A command finds its harness
A command that acts on a harness SHALL take as its root the folder given with
`--harness`, or else the nearest folder at or above the working directory that holds
`harness.yaml`, and SHALL refuse when neither yields a harness.

#### Scenario: Harness resolved from the working directory
- **WHEN** a harness verb other than `launch` runs from a folder inside a harness without `--harness`
- **THEN** it acts on the harness whose `harness.yaml` is the nearest at or above that folder
- **Cases**: keeps `tests/cases/harness/harness-resolved-from-the-working-directory.yaml`

#### Scenario: No harness found
- **WHEN** a harness verb other than `launch` runs outside any harness and without `--harness`
- **THEN** it exits 1, reports that no harness was found, and writes nothing
- **Cases**: keeps `tests/cases/harness/no-harness-found.yaml`

### Requirement: Launch starts the IDE
When the personal config declares `ide` and `--no-open` is not given, `launch` SHALL
resolve its command on PATH as the platform does (on Windows `code` finds `code.cmd`),
append the absolute harness path as the last argument, start it without waiting and
without a console or standard streams of its own, and print the command line as
declared followed by the path. When the command resolves to nothing, it SHALL say the
harness is ready, name the IDE command that could not be started, and exit 1.

#### Scenario: IDE opened
- **WHEN** the personal config declares `ide: "code -n"` and a task is launched without `--no-open`
- **THEN** the output holds a line with `code -n` followed by the absolute harness path
- **Cases**: keeps `tests/cases/harness/ide-opened.yaml`

#### Scenario: IDE command not found
- **WHEN** the personal config declares `ide: "no-such-ide -n"` and a task is launched without `--no-open`
- **THEN** the harness is created, the output says the harness is ready and that the IDE command `no-such-ide -n` could not be started, and the exit code is 1
- **Cases**: keeps `tests/cases/harness/ide-command-not-found.yaml`

### Requirement: Launch without opening the IDE
With `--no-open`, or when the personal config declares no `ide`, `launch` SHALL start
nothing and print no IDE command line, only the harness path.

#### Scenario: Open skipped
- **WHEN** a task is launched with `--no-open`
- **THEN** no IDE command line appears in the output and the harness is created as usual
- **Cases**: keeps `tests/cases/harness/open-skipped.yaml`

#### Scenario: No IDE declared
- **WHEN** the config has no `ide` key and a task is launched without `--no-open`
- **THEN** no IDE command line appears in the output and the harness path is printed
- **Cases**: keeps `tests/cases/harness/no-ide-declared.yaml`
