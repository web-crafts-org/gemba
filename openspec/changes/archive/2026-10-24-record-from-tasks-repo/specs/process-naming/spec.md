# Spec Delta

## MODIFIED Requirements

### Requirement: Every other object is a group
A process whose steps act on an object other than a task or the tasks repo, such as
the harness of a launched task or the skills the CLI writes, SHALL expose its
subcommands under a group named after that object, as in `gemba harness <verb>` and
`gemba skills <verb>`. A verb SHALL NOT exist both bare and inside a group with
different meanings.

#### Scenario: Harness subcommands are grouped
- **WHEN** a process launches the harness of a task, files a note in it or resolves an approved note
- **THEN** its subcommands are `gemba harness launch`, `gemba harness note` and `gemba harness resolve`, and `gemba <verb>` keeps its meaning for tasks
- **Cases**: keeps the entry `process-naming: Harness subcommands are grouped` of `tests/not-automated.yaml`

#### Scenario: Skills subcommands are grouped
- **WHEN** the CLI writes or checks the skills of the tasks repo
- **THEN** its subcommands are `gemba skills <verb>`, as in `gemba skills update`
- **Cases**: modifies `tests/cases/skills/every-registered-skill-is-written.yaml` (its second document's output lists `gemba-record`)
