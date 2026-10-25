# Spec Delta

## MODIFIED Requirements

### Requirement: Agent providers
Each file of the config MAY declare a top-level `agent_providers` list. The list of
the shared config names the providers of the people who share the tasks repo: the
skills of the tasks repo are written for them, and a harness is launched for them
unless the personal config declares its own list. The list of the personal config
names the providers of the person and replaces the shared one for the harnesses
launched from that clone, and for nothing else. In either file, each entry SHALL be the
identifier of a provider the CLI knows (`claude` and `agents` in this change), the
list SHALL be non-empty when present, and no identifier SHALL appear twice. Any process
that reads the config SHALL refuse to proceed when a list is malformed, names an
unknown provider or repeats one, naming its file and the known providers in its error.
A process that does not need the providers SHALL proceed when no list is declared; a
process that needs them reports the absence itself.

#### Scenario: Known providers accepted
- **WHEN** the config declares `agent_providers: [claude, agents]`
- **THEN** every process that reads the config accepts it and the skills process writes for both providers
- **Cases**: modifies `tests/cases/skills/one-folder-per-declared-provider.yaml` (its second document's output lists `gemba-record`)

#### Scenario: Unknown provider refused
- **WHEN** the config declares `agent_providers: [claude, cursor]` and `cursor` is not a known provider
- **THEN** any process that reads the config refuses to proceed and names `cursor` and the known providers
- **Cases**: keeps `tests/cases/config/unknown-provider-refused.yaml`

#### Scenario: Repeated provider refused
- **WHEN** the config declares `agent_providers: [claude, claude]`
- **THEN** any process that reads the config refuses to proceed and names the repeated provider
- **Cases**: keeps `tests/cases/config/repeated-provider-refused.yaml`

#### Scenario: Malformed providers refused
- **WHEN** `agent_providers` is a string, an empty list, or a list holding something other than strings
- **THEN** any process that reads the config refuses to proceed and names `agent_providers`
- **Cases**: keeps `tests/cases/config/malformed-providers-refused.yaml`

#### Scenario: Providers absent for a process that does not need them
- **WHEN** the config has no `agent_providers` key and a task is created
- **THEN** the create process proceeds exactly as before
- **Cases**: keeps `tests/cases/config/providers-absent-for-create.yaml`

#### Scenario: Providers declared in both files
- **WHEN** `gemba.yaml` declares `agent_providers: [claude, agents]` and `gemba.local.yaml` declares `agent_providers: [claude]`
- **THEN** every process that reads the config accepts it, and `gemba config show` prints `agent_providers` as `[claude, agents]` and `harness_providers` as `[claude]`
- **Cases**: keeps `tests/cases/config/providers-declared-in-both-files.yaml`

#### Scenario: Unknown personal provider refused
- **WHEN** `gemba.local.yaml` declares `agent_providers: [cursor]`
- **THEN** any process that reads the config refuses to proceed and names `gemba.local.yaml`, `cursor` and the known providers
- **Cases**: keeps `tests/cases/config/unknown-personal-provider-refused.yaml`
