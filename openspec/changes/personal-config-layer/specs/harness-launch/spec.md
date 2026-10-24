# Spec Delta

## MODIFIED Requirements

### Requirement: The harness config is the identity of the run
`harness.yaml` at the harness root SHALL be written by `launch` only and SHALL hold, in
this order: `task`, the task file path relative to the tasks repo root; `ref`;
`workstream`; `agent_providers`, the providers the harness carries a guide and skills
for, the providers of the launch as the next requirement says; `launched_at`, the
launch date as an ISO date; and `gemba_version`, the version of the package that wrote
it. No gemba command SHALL modify it afterwards, and agents SHALL NOT edit it. A
command that acts on a harness SHALL resolve the harness root as the nearest folder at
or above the working directory that holds `harness.yaml`, or as the folder given with
`--harness`, and SHALL refuse when neither yields a harness.

#### Scenario: Harness config written
- **WHEN** `SUP-1` of workstream `support` is launched on 2026-09-30 by package version V with `agent_providers: [claude, agents]`
- **THEN** `harness.yaml` is exactly `task: tasks/support/2026-09-30-SUP-1-login-fails.md`, `ref: SUP-1`, `workstream: support`, `agent_providers: [claude, agents]`, `launched_at: 2026-09-30`, `gemba_version: "V"`, one key per line in that order
- **Cases**: keeps `tests/cases/harness/harness-config-written.yaml`

#### Scenario: Harness resolved from the working directory
- **WHEN** a harness verb other than `launch` runs from a folder inside a harness without `--harness`
- **THEN** it acts on the harness whose `harness.yaml` is the nearest at or above that folder
- **Cases**: keeps `tests/cases/harness/harness-resolved-from-the-working-directory.yaml`

#### Scenario: No harness found
- **WHEN** a harness verb other than `launch` runs outside any harness and without `--harness`
- **THEN** it exits 1, reports that no harness was found, and writes nothing
- **Cases**: keeps `tests/cases/harness/no-harness-found.yaml`

### Requirement: The guide and the skills are written per provider
The providers of a launch SHALL be the `agent_providers` of the personal config when
it declares them, and otherwise those of the shared config. `launch` SHALL write the
guide under the filename of each provider of the launch (`CLAUDE.md` for `claude`,
`AGENTS.md` for `agents`), with the same content for every provider, and SHALL write
the skills whose scope includes the harness under the skills folder of each of those
providers, with the provenance that `gemba skills update` writes. A provider that is
not a provider of the launch SHALL get neither. The skills of the tasks repo SHALL NOT
be touched by a launch.

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
- **THEN** the harness holds `CLAUDE.md` and `.claude/skills/gemba-harness/SKILL.md`, neither `AGENTS.md` nor `.agents/` exists in it, its `harness.yaml` reads `agent_providers: [claude]`, and the skills folders of the tasks repo are as they were
- **Cases**: adds `tests/cases/harness/harness-launched-for-the-personal-providers.yaml`

### Requirement: Launch opens the IDE
When the personal config declares `ide`, `launch` SHALL take its command and its
arguments as the config defines them, resolve the command to an executable on PATH
the way the platform does (so that on Windows `code` finds `code.cmd`), append the
absolute harness path as the last argument, start it without waiting for it to finish
and without a console or standard streams of its own, and print the command line as
declared followed by the path. When the command resolves to nothing on PATH, `launch`
SHALL report that the harness is ready and that the IDE command could not be started,
naming the command, and exit 1. With `--no-open` it SHALL start nothing and print no
such line. Without `ide` in the personal config it SHALL start nothing and print the
harness path only.

#### Scenario: IDE opened
- **WHEN** the personal config declares `ide: "code -n"` and a task is launched without `--no-open`
- **THEN** the output holds a line with `code -n` followed by the absolute harness path
- **Cases**: modifies `tests/cases/harness/ide-opened.yaml` (`ide` moves to the personal config)

#### Scenario: IDE command not found
- **WHEN** the personal config declares `ide: "no-such-ide -n"` and a task is launched without `--no-open`
- **THEN** the harness is created, the output says the harness is ready and that the IDE command `no-such-ide -n` could not be started, and the exit code is 1
- **Cases**: modifies `tests/cases/harness/ide-command-not-found.yaml` (`ide` moves to the personal config)

#### Scenario: Open skipped
- **WHEN** a task is launched with `--no-open`
- **THEN** no IDE command line appears in the output and the harness is created as usual
- **Cases**: modifies `tests/cases/harness/open-skipped.yaml` (`ide` moves to the personal config)

#### Scenario: No IDE declared
- **WHEN** the config has no `ide` key and a task is launched without `--no-open`
- **THEN** no IDE command line appears in the output and the harness path is printed
- **Cases**: keeps `tests/cases/harness/no-ide-declared.yaml`
