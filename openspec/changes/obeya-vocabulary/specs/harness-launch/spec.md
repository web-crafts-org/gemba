# Spec Delta

## MODIFIED Requirements

### Requirement: Launch creates the harness of a task
`gemba harness launch <ref>` SHALL resolve the task with that ref anywhere under
`tasks/`, archives included, and SHALL create its harness at
`harnesses/<workstream>/<stem>/` under the obeya root, where `<stem>` is the task
filename without `.md`. The command SHALL refuse, writing nothing, when no task has that
ref, when the task is archived, or when its status is `done`, saying in that case that
`gemba mark` moves it to `open` or `in-progress` first. The harness SHALL hold:
`harness.yaml`; `task.md`; the guide under the filename of every declared agent
provider; the harness-scoped skills under the skills folder of every declared agent
provider; empty `notes/`, `assets/` and `worktrees/` folders; and a `.gitignore` that
excludes `worktrees/`. The command SHALL print the harness path relative to the obeya root. A folder already present at the harness path without a `harness.yaml` SHALL
be completed, never emptied: existing files are left as they are.

#### Scenario: Harness layout created
- **WHEN** `gemba harness launch SUP-1` runs for an open task `tasks/support/2026-09-30-SUP-1-login-fails.md` in an obeya declaring `agent_providers: [claude, agents]`
- **THEN** `harnesses/support/2026-09-30-SUP-1-login-fails/` holds `harness.yaml`, `task.md`, `CLAUDE.md`, `AGENTS.md`, `.claude/skills/gemba-harness/SKILL.md`, `.agents/skills/gemba-harness/SKILL.md`, `notes/`, `assets/`, `worktrees/` and a `.gitignore` containing `worktrees/`, the command prints `harnesses/support/2026-09-30-SUP-1-login-fails` and exits 0
- **Cases**: keeps `tests/cases/harness/harness-layout-created.yaml`

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

### Requirement: The harness config is the identity of the run
`harness.yaml` at the harness root SHALL be written by `launch` only and SHALL hold, in
this order: `task`, the task file path relative to the obeya root; `ref`;
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
not a provider of the launch SHALL get neither. The skills of the obeya SHALL NOT
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
- **THEN** the harness holds `CLAUDE.md` and `.claude/skills/gemba-harness/SKILL.md`, neither `AGENTS.md` nor `.agents/` exists in it, its `harness.yaml` reads `agent_providers: [claude]`, and the skills folders of the obeya are as they were
- **Cases**: keeps `tests/cases/harness/harness-launched-for-the-personal-providers.yaml`

### Requirement: The harness is a local git repository
`launch` SHALL initialize a git repository at the harness root with branch `main` and
no remote, and SHALL commit everything it wrote as the first commit. The obeya
SHALL ignore `harnesses/` as a whole, so the harness repository never reaches the obeya history.

#### Scenario: Harness repository initialized
- **WHEN** a harness is launched
- **THEN** the harness holds a `.git/` folder whose `HEAD` points at `refs/heads/main`, and the repository history has exactly one commit, which includes `harness.yaml`, the guide, the skills, `.gitignore` and `task.md`
- **Cases**: keeps `tests/cases/harness/harness-repository-initialized.yaml`

#### Scenario: Harnesses ignored by the tasks repo
- **WHEN** the obeya is at this change or later
- **THEN** its `.gitignore` lists `harnesses/` and no `runs/` folder is tracked
- **Cases**: modifies the entry `harness-launch: Harnesses ignored by the tasks repo` of `tests/not-automated.yaml` (now `harness-launch: Harnesses ignored by the obeya`)

### Requirement: Launch by the agent
The `gemba-harness` skill SHALL have the agent, from anywhere inside the obeya,
identify the task to launch by its ref, asking the user when the request names a task
ambiguously, run `gemba harness launch <ref>`, relay the printed path, the status
transition and whether the IDE was opened, and stop. The skill SHALL NOT have the agent
create any file of the harness by hand.

#### Scenario: Agent launches a task
- **WHEN** the user asks to launch, start or open the harness of a task
- **THEN** the agent runs the command with the task's ref and relays its output
- **Cases**: keeps the entry `harness-launch: Agent launches a task` of `tests/not-automated.yaml`
