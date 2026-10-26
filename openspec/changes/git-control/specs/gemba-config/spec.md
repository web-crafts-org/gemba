# Spec Delta

## ADDED Requirements

### Requirement: The git hooks of a clone
Each file of the config MAY declare `git_hooks`, `true` or `false`: in `gemba.yaml`,
whether the team turns on gemba's git hooks; in `gemba.local.yaml`, whether this clone
does, which always wins over the team. Declared in neither, they are off. Any other value
SHALL be refused, naming the key and its file, and so SHALL the key in either file of an
obeya whose shared config declares no team.

#### Scenario: Hooks turned on by the team
- **WHEN** `gemba.yaml` declares a team and `git_hooks: true`, `gemba.local.yaml` declares `me: manuel` and no `git_hooks`, and `gemba config show` runs
- **THEN** the document holds `git_hooks: true`, and the exit code is 0
- **Cases**: adds `tests/cases/config/hooks-turned-on-by-the-team.yaml`

#### Scenario: Hooks turned off for a clone
- **WHEN** `gemba.yaml` declares a team and `git_hooks: true`, `gemba.local.yaml` declares `git_hooks: false`, and `gemba config show` runs
- **THEN** the document holds `git_hooks: false`
- **Cases**: adds `tests/cases/config/hooks-turned-off-for-a-clone.yaml`

#### Scenario: Hooks turned on for a clone
- **WHEN** `gemba.yaml` declares a team and no `git_hooks`, `gemba.local.yaml` declares `git_hooks: true`, and `gemba config check` runs
- **THEN** the output holds `git hooks: on`, and the exit code is 0
- **Cases**: adds `tests/cases/config/hooks-turned-on-for-a-clone.yaml`

#### Scenario: Hooks refused without a team
- **WHEN** `gemba.yaml` declares no team and either file declares `git_hooks: true`
- **THEN** any process that reads the config refuses to proceed, saying under the path of each file that declares it that `git_hooks` needs a team in `gemba.yaml`, and writes nothing
- **Cases**: adds `tests/cases/config/hooks-refused-without-a-team.yaml`

#### Scenario: Malformed hooks key refused
- **WHEN** `gemba.yaml` declares a team and `git_hooks: yes please`, or `gemba.local.yaml` declares `git_hooks: [pre-push]`
- **THEN** any process that reads the config refuses to proceed, names `git_hooks` and the file that declares it, and says it is `true` or `false`
- **Cases**: adds `tests/cases/config/malformed-hooks-key-refused.yaml`

## MODIFIED Requirements

### Requirement: Keys of each layer
Each top-level key SHALL have a layer: only the shared config holds `metadata`,
`default_workstream`, `obeya`, `team` and the workstream catalogue; only the personal
config holds `ide`, `repos_dir`, `branch_prefix` and `me`; both may hold
`agent_providers`, `git_hooks` and process blocks, also under `workstreams`. A key in
the wrong file SHALL be refused, naming the file it goes in.
`organization` SHALL be refused in either file as renamed `obeya`. Other keys SHALL be
ignored.

#### Scenario: Personal keys refused in the shared config
- **WHEN** `gemba.yaml` declares `ide: "code -n"`, `repos_dir: ~/projects` and `branch_prefix: nk`, as a config written for an earlier version may
- **THEN** any process that reads the config refuses to proceed with one message that names `ide`, `repos_dir` and `branch_prefix` and says each goes in `gemba.local.yaml`, and writes nothing
- **Cases**: keeps `tests/cases/config/personal-keys-refused-in-the-shared-config.yaml`

#### Scenario: Shared keys refused in the personal config
- **WHEN** `gemba.local.yaml` declares `obeya: nakatomi`, `default_workstream: support` and a top-level `metadata` list
- **THEN** any process that reads the config refuses to proceed with one message that names the three keys and says each goes in `gemba.yaml`, and writes nothing
- **Cases**: keeps `tests/cases/config/shared-keys-refused-in-the-personal-config.yaml`

#### Scenario: Former organization key refused
- **WHEN** `gemba.yaml` declares `organization: nakatomi`, as a config written for an earlier version does, or `gemba.local.yaml` declares `organization`
- **THEN** any process that reads the config refuses to proceed with one message that names `organization` under the path of each file that declares it and says it was renamed `obeya`, which belongs in `gemba.yaml`, and writes nothing
- **Cases**: keeps `tests/cases/config/former-organization-key-refused.yaml`

#### Scenario: Unknown keys ignored in both files
- **WHEN** `gemba.yaml` declares a top-level key `reviewers` and `gemba.local.yaml` a top-level key `theme`, neither known to gemba, and a task is created
- **THEN** the create process proceeds exactly as if neither key were there
- **Cases**: keeps `tests/cases/config/unknown-keys-ignored-in-both-files.yaml`

#### Scenario: Team keys refused in the wrong file
- **WHEN** `gemba.yaml` declares `me: manuel` and `gemba.local.yaml` declares a `team`
- **THEN** any process that reads the config refuses to proceed with one message that says `me` goes in `gemba.local.yaml` and `team` in `gemba.yaml`, each under the path of the file that declares it, and writes nothing
- **Cases**: keeps `tests/cases/config/team-keys-refused-in-the-wrong-file.yaml`

### Requirement: Agent providers of each file
Each file of the config MAY declare a top-level `agent_providers` list. The shared
list names the providers of the people who share the obeya: its skills are written for
them, and a harness is launched for them unless the personal config declares a list,
which then replaces it for the harnesses launched from that clone and for nothing
else. A process that does not need the providers SHALL proceed when no list is
declared; one that needs them reports the absence.

#### Scenario: Known providers accepted
- **WHEN** the config declares `agent_providers: [claude, agents]`
- **THEN** every process that reads the config accepts it and the skills process writes for both providers
- **Cases**: modifies `tests/cases/skills/one-folder-per-declared-provider.yaml` (the output of its second document lists `gemba-sync`)

#### Scenario: Providers absent for a process that does not need them
- **WHEN** the config has no `agent_providers` key and a task is created
- **THEN** the create process proceeds exactly as before
- **Cases**: keeps `tests/cases/config/providers-absent-for-create.yaml`

#### Scenario: Providers declared in both files
- **WHEN** `gemba.yaml` declares `agent_providers: [claude, agents]` and `gemba.local.yaml` declares `agent_providers: [claude]`
- **THEN** every process that reads the config accepts it, and `gemba config show` prints `agent_providers` as `[claude, agents]` and `harness_providers` as `[claude]`
- **Cases**: keeps `tests/cases/config/providers-declared-in-both-files.yaml`
