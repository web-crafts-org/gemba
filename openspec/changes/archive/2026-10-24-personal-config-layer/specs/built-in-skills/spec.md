# Spec Delta

## MODIFIED Requirements

### Requirement: Skills are written at the root the command runs in
`gemba skills update` SHALL resolve its target by walking up from the current working
directory: the nearest folder holding `harness.yaml` is a harness and the target is
that harness, with the providers recorded in its `harness.yaml`; otherwise the nearest
folder holding `gemba.yaml` is the tasks repo and the target is its root, with the
providers of the shared config, never those of the personal config, which choose the
providers of a launch only. A shared config that declares no `agent_providers` SHALL
be refused as the previous requirement says, whatever the personal config declares.
The command SHALL write the skills folders under the target and never under the
working directory, and SHALL refuse, writing nothing, when no gemba config is found.
`--root` SHALL name the target explicitly, tasks repo or harness.

#### Scenario: Run from a subfolder
- **WHEN** `gemba skills update` runs from a folder below the tasks repo root that is not inside a harness
- **THEN** the skills appear under the root, and nothing is written under the folder the command ran from
- **Cases**: keeps `tests/cases/skills/run-from-a-subfolder.yaml`

#### Scenario: Run from inside a harness
- **WHEN** `gemba skills update` runs from a folder inside a harness whose `harness.yaml` records `agent_providers: [claude]`
- **THEN** the harness-scoped skills are written or refreshed under the harness's `.claude/skills/`, nothing is written under `.agents/`, and nothing is written at the tasks repo root
- **Cases**: keeps `tests/cases/skills/run-from-inside-a-harness.yaml`

#### Scenario: No tasks repo
- **WHEN** no ancestor of the working directory holds `gemba.yaml`
- **THEN** the command exits 1, reports that no gemba config was found, and writes nothing
- **Cases**: keeps `tests/cases/skills/no-tasks-repo.yaml`

#### Scenario: Personal providers leave the tasks repo skills
- **WHEN** `gemba.yaml` declares `agent_providers: [claude]`, `gemba.local.yaml` declares `agent_providers: [agents]`, and `gemba skills update` runs at the tasks repo root
- **THEN** the tasks-repo skills are written under `.claude/skills/` and no `.agents/` folder is created
- **Cases**: adds `tests/cases/skills/personal-providers-leave-the-tasks-repo-skills.yaml`
