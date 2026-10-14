# Spec Delta

## MODIFIED Requirements

### Requirement: IDE command
The config MAY declare a top-level `ide`, the command that opens a folder in the
organization's IDE, to which `launch` appends the harness path as the last argument.
It SHALL be either a non-empty string, split into a command and its arguments as a
POSIX shell would, so that a path holding spaces or backslashes goes between quotes,
or a map holding `command`, a non-empty string naming the executable, and optionally
`args`, a list of strings. The string `"code -n"` and the map `{command: code,
args: [-n]}` SHALL mean the same. Any process that reads the config SHALL refuse to
proceed when `ide` is present and is neither form: an empty string, a list, a map
without `command`, a `command` that is not a non-empty string, or `args` that is not
a list of strings. A process that does not open the IDE SHALL proceed when the key is
absent.

#### Scenario: IDE command accepted
- **WHEN** the config declares `ide: "code -n"`
- **THEN** every process that reads the config accepts it and `launch` starts `code -n <harness path>`
- **Cases**: keeps its cases in `tests/cases/harness/ide-opened.yaml`

#### Scenario: Structured IDE command accepted
- **WHEN** the config declares `ide: { command: code, args: [-n] }`
- **THEN** every process that reads the config accepts it, `gemba config show` prints it as declared, and `launch` starts `code -n <harness path>` and prints `opening: code -n` followed by the path
- **Cases**: adds `tests/cases/config/structured-ide-command-accepted.yaml`

#### Scenario: Malformed IDE command refused
- **WHEN** `ide` is an empty string, a list, a map without `command`, a map whose `command` is empty or not a string, or a map whose `args` is not a list of strings
- **THEN** any process that reads the config refuses to proceed and names `ide`
- **Cases**: modifies `tests/cases/config/malformed-ide-command-refused.yaml` (the malformed maps are added)

#### Scenario: IDE absent for a process that does not open it
- **WHEN** the config has no `ide` key and a task is created
- **THEN** the create process proceeds exactly as before
- **Cases**: keeps `tests/cases/config/ide-absent-for-create.yaml`

### Requirement: Workstream catalogue
The config SHALL declare its workstreams under a top-level `workstreams` map keyed by
workstream identifier. Each identifier SHALL be kebab-case (lowercase letters, digits
and single hyphens) and SHALL NOT be a reserved device name of Windows (`con`, `prn`,
`aux`, `nul`, `com0` to `com9`, `lpt0` to `lpt9`), because it is also the folder name
under `tasks/` on every platform. Each workstream block SHALL contain a `prefix` (one
or more uppercase ASCII letters, unique across the catalogue) and a non-empty
`description` that tells an agent which work belongs there. A workstream block MAY
contain a `metadata` list and a `create` block as defined below.

#### Scenario: Valid catalogue
- **WHEN** the config declares `code-reviews` with `prefix: CR` and `description: Review a merge request before it is merged`
- **THEN** processes accept `code-reviews` as a workstream, use `CR` for its refs and use the description to decide placement
- **Cases**: keeps `tests/cases/create/valid-catalogue.yaml`

#### Scenario: Duplicate prefix
- **WHEN** two workstreams declare the same `prefix`
- **THEN** any process that reads the config refuses to proceed and names both workstreams in its error
- **Cases**: keeps `tests/cases/create/duplicate-prefix.yaml`

#### Scenario: Invalid identifier or prefix
- **WHEN** a workstream identifier is not kebab-case, or a prefix is empty or contains characters other than uppercase ASCII letters
- **THEN** any process that reads the config refuses to proceed and names the offending workstream
- **Cases**: keeps `tests/cases/create/invalid-identifier-or-prefix.yaml`

#### Scenario: Reserved device name refused
- **WHEN** a workstream identifier is `nul`, `con`, `aux`, `prn`, `com1` or `lpt1`
- **THEN** any process that reads the config refuses to proceed, names the workstream and says the name is reserved on Windows, on every platform
- **Cases**: adds `tests/cases/config/reserved-workstream-identifier-refused.yaml`

#### Scenario: Missing description
- **WHEN** a workstream block has no `description` or an empty one
- **THEN** any process that reads the config refuses to proceed and names the workstream
- **Cases**: keeps `tests/cases/create/missing-description.yaml`
