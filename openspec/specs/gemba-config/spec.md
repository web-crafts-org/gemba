# gemba-config Specification

## Purpose

The gemba config is the single customization layer of Gemba: it holds
every organization-specific value (workstreams, metadata schema, per-process
customization) so that processes and their commands stay free of such values and can
later be extracted into a CLI unchanged.

## Requirements

### Requirement: Config file location and format
The tasks repo SHALL hold its customization in a single YAML file named `gemba.yaml`
at its root. Processes and commands SHALL locate it by walking up from the current
working directory to the nearest `gemba.yaml`, so they work from any folder inside the
tasks repo, including the harnesses.

#### Scenario: Command run from a subfolder
- **WHEN** a gemba command is started from any folder below the tasks repo root
- **THEN** it resolves the tasks repo root as the nearest ancestor folder containing `gemba.yaml` and reads that file

#### Scenario: No config found
- **WHEN** no ancestor folder of the current working directory contains `gemba.yaml`
- **THEN** the process stops, reports that no gemba config was found, and writes nothing

### Requirement: No organization-specific value outside the config
Every value that is specific to the organization using Gemba (workstream
identifiers, prefixes, descriptions, metadata fields, process rules) SHALL live in
`gemba.yaml` and nowhere else. Skills and commands SHALL obtain such values from the
config at runtime and SHALL NOT embed them.

#### Scenario: Workstream added by editing the config only
- **WHEN** a new workstream block is added to `gemba.yaml` and no skill or command file is modified
- **THEN** the create process accepts tasks for that workstream and places them in its folder

#### Scenario: Workstream removed from the config
- **WHEN** a workstream block is removed from `gemba.yaml`
- **THEN** the create process refuses that workstream identifier, while task files already stored in its folder are left untouched

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

#### Scenario: Duplicate prefix
- **WHEN** two workstreams declare the same `prefix`
- **THEN** any process that reads the config refuses to proceed and names both workstreams in its error

#### Scenario: Invalid identifier or prefix
- **WHEN** a workstream identifier is not kebab-case, or a prefix is empty or contains characters other than uppercase ASCII letters
- **THEN** any process that reads the config refuses to proceed and names the offending workstream

#### Scenario: Reserved device name refused
- **WHEN** a workstream identifier is `nul`, `con`, `aux`, `prn`, `com1` or `lpt1`
- **THEN** any process that reads the config refuses to proceed, names the workstream and says the name is reserved on Windows, on every platform

#### Scenario: Missing description
- **WHEN** a workstream block has no `description` or an empty one
- **THEN** any process that reads the config refuses to proceed and names the workstream

### Requirement: Default workstream
The config SHALL declare a top-level `default_workstream` naming one workstream of the
catalogue. It is the workstream for work that fits no other description.

#### Scenario: Default names an existing workstream
- **WHEN** `default_workstream: operations` and `operations` exists in the catalogue
- **THEN** processes use `operations` for work that matches no other workstream description

#### Scenario: Default names a missing workstream
- **WHEN** `default_workstream` is absent or names an identifier not present in the catalogue
- **THEN** any process that reads the config refuses to proceed and reports the invalid default

### Requirement: Metadata field declaration
A metadata field declaration SHALL be a map with a `name` (required, snake_case: lowercase
letters, digits and single underscores), a `type` (required, one of `text`, `number`,
`boolean` and `date`), an optional boolean `required` that defaults to `false`, and an
optional `description` used only when the name alone does not convey what value is
expected. The type tells every process how to read, write, compare and operate on a
value of the field; it says nothing of what the field means, which belongs to the
person who declared it. Declarations SHALL NOT carry allowed values or defaults, and any
key other than the four SHALL be refused. The names `workstream` and `status` SHALL be
refused, because the report groups every task by them.

#### Scenario: Minimal declaration
- **WHEN** a declaration is `{ name: client, type: text }`
- **THEN** the field `client` is an optional text field and has no description

#### Scenario: Required field with description
- **WHEN** a declaration is `{ name: merge_url, type: text, required: true, description: Link to the merge request, any provider }`
- **THEN** the field `merge_url` must be supplied when a task is created in that workstream, and the description is available to the agent when asking for it

#### Scenario: Invalid field name
- **WHEN** a declaration has no `name` or a name that is not snake_case
- **THEN** any process that reads the config refuses to proceed and reports the declaration

#### Scenario: Missing or unknown type
- **WHEN** a declaration has no `type`, or a type other than the four, such as `{ name: hours, type: integer }`
- **THEN** any process that reads the config refuses to proceed, names the field and lists the four types

#### Scenario: Unsupported declaration key
- **WHEN** a declaration carries a key other than `name`, `type`, `required` and `description`, such as `values: [acme, globex]`
- **THEN** any process that reads the config refuses to proceed, names the field and the key, and lists the allowed keys

#### Scenario: Reserved field name
- **WHEN** a declaration is named `status` or `workstream`
- **THEN** any process that reads the config refuses to proceed and says the name is reserved

### Requirement: Base metadata and effective schema
The config MAY declare a top-level `metadata` list of field declarations shared by every
workstream. The effective metadata schema of a workstream SHALL be the union by field
name of the base list and the workstream's own `metadata` list. When the same name
appears in both, the workstream declaration SHALL replace the base declaration
entirely (the most specific definition wins). A field name SHALL have one type across
the whole config: every list that declares a name, the base list and any workstream
list, SHALL give it the same type, so that a value of that field is read, compared and
added the same way in every workstream, and any process that reads the config SHALL
refuse a config where two declarations of one name differ in type, naming the field
and the two lists. Within a single list, a repeated name is an error.

#### Scenario: Union of base and workstream fields
- **WHEN** the base list declares `client` and `hours`, and workstream `support` declares `project`
- **THEN** the effective schema of `support` is `client`, `hours`, `project`

#### Scenario: Workstream overrides a base field
- **WHEN** the base list declares `{ name: client, type: text }` and workstream `support` declares `{ name: client, type: text, required: true }`
- **THEN** `client` is required for `support` and remains optional for workstreams that do not redeclare it

#### Scenario: No metadata declared anywhere
- **WHEN** neither the base list nor the workstream declares any field
- **THEN** the effective schema is empty and tasks in that workstream carry an empty `metadata` map

#### Scenario: Repeated name within one list
- **WHEN** the same field name appears twice in the base list or twice in one workstream list
- **THEN** any process that reads the config refuses to proceed and reports the duplicate

#### Scenario: One type per field name
- **WHEN** the base list declares `{ name: hours, type: number }` and workstream `support` declares `{ name: hours, type: text }`, or two workstreams declare `due` as a `date` and as a `text`
- **THEN** any process that reads the config refuses to proceed, names the field and the two lists that disagree

### Requirement: Per-process customization block
A workstream block MAY contain a block named after a Gemba process: `create`, `list`,
`record`, `report`, `mark`, `archive` and `set`, whose process is one verb, and
`harness` and `worktree`, whose process is a group. A verb block MAY contain `rules`,
a list of non-empty strings the agent must follow while running that verb for that
workstream, and `context`, a string of background the agent reads before running it.
The `harness` block MAY contain one verb block per verb of the group (`launch`,
`note`, `resolve`, `remove`), each with `rules` and `context` as above, and `guide`, a
non-empty string that `launch` renders into the guide of the harness; any other key
inside `harness` SHALL be refused. The `worktree` block MAY contain one verb block per
verb of the group (`add`, `list`, `remove`), each with `rules` and `context` as above;
any other key inside `worktree`, `guide` included, SHALL be refused. Any process that
reads the config SHALL validate the shape of every known process block, and a process
SHALL read only its own block, a verb of a group only its own verb block, and SHALL
ignore blocks it does not know, so that later changes can add processes without
invalidating existing configs.

#### Scenario: Create rules applied
- **WHEN** workstream `deployments` declares `create.rules` containing "environment is production or staging; ask if not stated"
- **THEN** an agent creating a task in `deployments` follows that rule before creating the file

#### Scenario: List rules applied
- **WHEN** workstream `support` declares `list.rules` containing "always mention the client next to the title"
- **THEN** an agent listing `support` tasks follows that rule when rendering the result

#### Scenario: Unknown process block ignored
- **WHEN** a workstream declares a block named `publish` and the create process runs
- **THEN** the create process behaves exactly as if the `publish` block were absent

#### Scenario: Malformed process block
- **WHEN** a workstream declares `list.rules` as a string instead of a list, or `list.context` as a list instead of a string
- **THEN** any process that reads the config refuses to proceed and names the workstream and the block

#### Scenario: Harness verb blocks accepted
- **WHEN** workstream `code-reviews` declares `harness.guide`, `harness.note.rules`, `harness.resolve.context` and `harness.remove.rules`
- **THEN** every process that reads the config accepts it, and launching a `code-reviews` task renders the guide text

#### Scenario: Malformed harness block
- **WHEN** a workstream declares `harness.guide` as a list, `harness.note.rules` as a string, or a key inside `harness` that is neither `guide` nor a verb of the group, such as `harness.rules`
- **THEN** any process that reads the config refuses to proceed and names the workstream and the offending key

#### Scenario: Worktree verb blocks accepted
- **WHEN** workstream `code-reviews` declares `worktree.add.rules`, `worktree.list.context` and `worktree.remove.rules`
- **THEN** every process that reads the config accepts it, and a task is created in `code-reviews` as before

#### Scenario: Malformed worktree block
- **WHEN** a workstream declares `worktree.add.rules` as a string, `worktree.guide`, or a key inside `worktree` that is not a verb of the group, such as `worktree.rules`
- **THEN** any process that reads the config refuses to proceed and names the workstream and the offending key

#### Scenario: Record and report blocks accepted
- **WHEN** workstream `support` declares `record.rules` and `report.context`
- **THEN** every process that reads the config accepts it, and a task is created in `support` as before

#### Scenario: Malformed record or report block
- **WHEN** a workstream declares `record.rules` as a string, or `report.context` as a list
- **THEN** any process that reads the config refuses to proceed and names the workstream and the block

#### Scenario: Mark and archive blocks accepted
- **WHEN** workstream `support` declares `mark.rules` and `archive.context`
- **THEN** every process that reads the config accepts it, and a task is created in `support` as before

#### Scenario: Malformed mark or archive block
- **WHEN** a workstream declares `mark.rules` as a string, or `archive.context` as a list
- **THEN** any process that reads the config refuses to proceed and names the workstream and the block

#### Scenario: Set block accepted
- **WHEN** workstream `support` declares `set.rules` and `set.context`
- **THEN** every process that reads the config accepts it, and a task is created in `support` as before

#### Scenario: Malformed set block
- **WHEN** a workstream declares `set.rules` as a string, or `set.context` as a list
- **THEN** any process that reads the config refuses to proceed and names the workstream and the block

### Requirement: Base process blocks and the effective block
The config MAY declare at its top level any process block a workstream block may
contain, `create`, `list`, `record`, `report`, `mark`, `archive`, `set`, `harness` and
`worktree`, with the same keys and the same shapes: these are the base blocks, shared
by every workstream. Any process that reads the config SHALL validate every base block
as it validates the block of a workstream, and SHALL refuse a malformed one, naming the
top level and the offending key. The effective block of a process, or of a verb of a
group, for a workstream SHALL combine the base block and the workstream's: its
`context` is the base context followed by the workstream's, or the one present when
only one is; its `rules` are every base rule followed by every rule of the workstream;
and the base `harness.guide` and the workstream's are rendered as the harness guide
specifies. The CLI SHALL compute the effective block and the effective metadata schema
of every workstream and print them through `gemba config show`, as the config
maintenance capability specifies, and a skill that has the agent read the block of a
process for a workstream, or the schema of a workstream, SHALL have it read from that
command rather than combine the two levels of the file itself. The agent SHALL follow
every rule of the effective block, and when a rule of the workstream contradicts a base
rule, the agent SHALL follow the rule of the workstream, the most specific one. When a
process runs over several workstreams, the base block SHALL apply once, alongside the
block of each workstream. A config with no base block SHALL behave exactly as before.

#### Scenario: Base blocks accepted
- **WHEN** the top level of the config declares `create.context`, `harness.guide`, `harness.note.rules` and `worktree.add.rules`, and no workstream declares a process block
- **THEN** every process that reads the config accepts it, a task is created as before, and launching a task renders the base guide text

#### Scenario: Malformed base block
- **WHEN** the top level of the config declares `list.rules` as a string, `harness.guide` as a list, or a key inside `harness` that is neither `guide` nor a verb of the group, such as `harness.rules`
- **THEN** any process that reads the config refuses to proceed, names the top level and the offending key, and writes nothing

#### Scenario: Base and workstream blocks followed together
- **WHEN** the top level declares `create.context` and `create.rules` containing "ask who requested the work if not stated", and workstream `deployments` declares `create.rules` containing "environment is production or staging; ask if not stated"
- **THEN** an agent creating a task in `deployments` reads the effective `create` block of `deployments` from `gemba config show`, the base context first and both rules, the base one first, and follows both before creating the file

#### Scenario: Workstream rule wins over a base rule
- **WHEN** the top level declares `worktree.add.rules` containing "start from the default branch of origin" and workstream `support` declares `worktree.add.rules` containing "start from the branch deployed to production"
- **THEN** an agent adding a worktree in a `support` harness reads both rules in that order from `gemba config show` and starts from the branch deployed to production

### Requirement: Config validation precedes any write
A process that reads the config SHALL validate the whole file against the rules above
before performing any action, and SHALL refuse with a message that names the first
invalid element when validation fails.

#### Scenario: Malformed YAML
- **WHEN** `gemba.yaml` cannot be parsed as YAML
- **THEN** the process stops, reports the parse error, and writes nothing

### Requirement: Agent providers
The config MAY declare a top-level `agent_providers` list naming the agent providers
of the organization. Each entry SHALL be the identifier of a provider the CLI knows
(`claude` and `agents` in this change), the list SHALL be non-empty when present, and
no identifier SHALL appear twice. Any process that reads the config SHALL refuse to
proceed when the list is malformed, names an unknown provider or repeats one, naming
the known providers in its error. A process that does not need the providers SHALL
proceed when the list is absent; a process that needs them reports the absence itself.

#### Scenario: Known providers accepted
- **WHEN** the config declares `agent_providers: [claude, agents]`
- **THEN** every process that reads the config accepts it and the skills process writes for both providers

#### Scenario: Unknown provider refused
- **WHEN** the config declares `agent_providers: [claude, cursor]` and `cursor` is not a known provider
- **THEN** any process that reads the config refuses to proceed and names `cursor` and the known providers

#### Scenario: Repeated provider refused
- **WHEN** the config declares `agent_providers: [claude, claude]`
- **THEN** any process that reads the config refuses to proceed and names the repeated provider

#### Scenario: Malformed providers refused
- **WHEN** `agent_providers` is a string, an empty list, or a list holding something other than strings
- **THEN** any process that reads the config refuses to proceed and names `agent_providers`

#### Scenario: Providers absent for a process that does not need them
- **WHEN** the config has no `agent_providers` key and a task is created
- **THEN** the create process proceeds exactly as before

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

#### Scenario: Structured IDE command accepted
- **WHEN** the config declares `ide: { command: code, args: [-n] }`
- **THEN** every process that reads the config accepts it, `gemba config show` prints it as declared, and `launch` starts `code -n <harness path>` and prints `opening: code -n` followed by the path

#### Scenario: Malformed IDE command refused
- **WHEN** `ide` is an empty string, a list, a map without `command`, a map whose `command` is empty or not a string, or a map whose `args` is not a list of strings
- **THEN** any process that reads the config refuses to proceed and names `ide`

#### Scenario: IDE absent for a process that does not open it
- **WHEN** the config has no `ide` key and a task is created
- **THEN** the create process proceeds exactly as before

### Requirement: Organization, repositories folder and branch prefix
The config MAY declare a top-level `organization`, a kebab-case name (lowercase
letters, digits and single hyphens) of the organization the config belongs to, which
is a segment of every branch the worktree process creates; a top-level `repos_dir`, a
non-empty string naming the folder whose immediate subfolders are the repositories a
run may check out, absolute, starting with `~`, or relative to the tasks repo root; and
a top-level `branch_prefix`, a kebab-case name that is the first segment of those
branches, `gemba` when absent. Any process that reads the config SHALL refuse to
proceed when `organization` or `branch_prefix` is present and is not kebab-case, or
when `repos_dir` is present and is not a non-empty string, naming the key. A process
that does not need them SHALL proceed when they are absent; the worktree process
reports the absence itself.

#### Scenario: Organization and repositories folder accepted
- **WHEN** the config declares `organization: nakatomi`, `repos_dir: ~/projects` and `branch_prefix: nk`
- **THEN** every process that reads the config accepts it, and a task is created as before

#### Scenario: Malformed organization or branch prefix refused
- **WHEN** `organization` is `Nakatomi Corp`, an empty string or a list, or `branch_prefix` is `Gemba/`
- **THEN** any process that reads the config refuses to proceed and names the key

#### Scenario: Malformed repositories folder refused
- **WHEN** `repos_dir` is an empty string, a list or a map
- **THEN** any process that reads the config refuses to proceed and names `repos_dir`

#### Scenario: Keys absent for a process that does not need them
- **WHEN** the config has no `organization`, `repos_dir` or `branch_prefix` key and a task is created
- **THEN** the create process proceeds exactly as before
