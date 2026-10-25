# Spec Delta

## MODIFIED Requirements

### Requirement: Config file location and format
The gemba config SHALL be two YAML files at the obeya root: `gemba.yaml`, the shared
config, committed, and `gemba.local.yaml`, the personal config, optional, private to
the clone, ignored by git. Commands SHALL take as root the nearest folder up from the
working directory holding `gemba.yaml`, so they work anywhere inside the obeya,
harnesses included, and SHALL read the personal config at that root when it exists, an
empty one as declaring nothing, never one without a `gemba.yaml` beside it.

#### Scenario: Command run from a subfolder
- **WHEN** a gemba command is started from any folder below the obeya root
- **THEN** it resolves the obeya root as the nearest ancestor folder containing `gemba.yaml` and reads that file, and the `gemba.local.yaml` of that root when there is one
- **Cases**: keeps `tests/cases/create/command-run-from-subfolder.yaml`

#### Scenario: No config found
- **WHEN** no ancestor folder of the current working directory contains `gemba.yaml`
- **THEN** the process stops, reports that no gemba config was found, and writes nothing
- **Cases**: keeps `tests/cases/create/no-config-found.yaml`

#### Scenario: Personal config read from below the root
- **WHEN** `gemba config show` runs from `tasks/support/` and the obeya root holds `gemba.yaml` and a `gemba.local.yaml` declaring `ide: "code -n"`
- **THEN** the document holds `ide: "code -n"`
- **Cases**: keeps `tests/cases/config/personal-config-read-from-below-the-root.yaml`

#### Scenario: Empty personal config
- **WHEN** `gemba.local.yaml` is an empty file and a task is created
- **THEN** the create process proceeds exactly as with no personal config
- **Cases**: keeps `tests/cases/config/empty-personal-config.yaml`

### Requirement: Workstream catalogue
The config SHALL declare its workstreams in a top-level `workstreams` map keyed by
identifier: kebab-case (lowercase letters, digits and single hyphens) and not a
reserved device name of Windows (`con`, `prn`, `aux`, `nul`, `com0` to `com9`, `lpt0`
to `lpt9`), since it names a folder of `tasks/`. Each block SHALL hold a `prefix`, one
or more uppercase ASCII letters unique in the catalogue, and a non-empty `description`
of the work that belongs there, and MAY hold `metadata` and process blocks.

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
- **Cases**: keeps `tests/cases/config/reserved-workstream-identifier-refused.yaml`

#### Scenario: Missing description
- **WHEN** a workstream block has no `description` or an empty one
- **THEN** any process that reads the config refuses to proceed and names the workstream
- **Cases**: keeps `tests/cases/create/missing-description.yaml`

### Requirement: Metadata field declaration
A metadata field declaration SHALL be a map of `name`, required, in snake_case;
`type`, required, one of `text`, `number`, `boolean` and `date`; `required`, a
boolean, `false` by default; and `description`, optional, when the name alone does not
say what is expected. The type sets how a value is handled, never what it means. Any
other key, allowed values and defaults included, SHALL be refused, and so SHALL the
names `workstream` and `status`, by which the report groups every task.

#### Scenario: Minimal declaration
- **WHEN** a declaration is `{ name: client, type: text }`
- **THEN** the field `client` is an optional text field and has no description
- **Cases**: keeps `tests/cases/create/minimal-declaration.yaml`

#### Scenario: Required field with description
- **WHEN** a declaration is `{ name: merge_url, type: text, required: true, description: Link to the merge request, any provider }`
- **THEN** the field `merge_url` must be supplied when a task is created in that workstream, and the description is available to the agent when asking for it
- **Cases**: keeps `tests/cases/create/required-field-with-description.yaml`

#### Scenario: Invalid field name
- **WHEN** a declaration has no `name` or a name that is not snake_case
- **THEN** any process that reads the config refuses to proceed and reports the declaration
- **Cases**: keeps `tests/cases/create/invalid-field-name.yaml`

#### Scenario: Missing or unknown type
- **WHEN** a declaration has no `type`, or a type other than the four, such as `{ name: hours, type: integer }`
- **THEN** any process that reads the config refuses to proceed, names the field and lists the four types
- **Cases**: keeps `tests/cases/config/missing-or-unknown-type-refused.yaml`

#### Scenario: Unsupported declaration key
- **WHEN** a declaration carries a key other than `name`, `type`, `required` and `description`, such as `values: [acme, globex]`
- **THEN** any process that reads the config refuses to proceed, names the field and the key, and lists the allowed keys
- **Cases**: keeps `tests/cases/config/unsupported-declaration-key-refused.yaml`

#### Scenario: Reserved field name
- **WHEN** a declaration is named `status` or `workstream`
- **THEN** any process that reads the config refuses to proceed and says the name is reserved
- **Cases**: keeps `tests/cases/config/reserved-field-name-refused.yaml`

### Requirement: Base metadata and effective schema
The config MAY declare a top-level `metadata` list shared by every workstream. The
effective schema of a workstream SHALL be the union by name of that list and its own,
its declaration of a name replacing the base one entirely. A name SHALL have one type
in every list that declares it, so its values read, compare and add alike everywhere:
a config where two declarations of a name differ in type SHALL be refused, naming the
field and the two lists. A name repeated in one list SHALL be refused.

#### Scenario: Union of base and workstream fields
- **WHEN** the base list declares `client` and `hours`, and workstream `support` declares `project`
- **THEN** the effective schema of `support` is `client`, `hours`, `project`
- **Cases**: keeps `tests/cases/create/union-of-base-and-workstream-fields.yaml`

#### Scenario: Workstream overrides a base field
- **WHEN** the base list declares `{ name: client, type: text }` and workstream `support` declares `{ name: client, type: text, required: true }`
- **THEN** `client` is required for `support` and remains optional for workstreams that do not redeclare it
- **Cases**: keeps `tests/cases/create/workstream-overrides-base-field.yaml`

#### Scenario: No metadata declared anywhere
- **WHEN** neither the base list nor the workstream declares any field
- **THEN** the effective schema is empty and tasks in that workstream carry an empty `metadata` map
- **Cases**: keeps `tests/cases/create/no-metadata-declared-anywhere.yaml`

#### Scenario: Repeated name within one list
- **WHEN** the same field name appears twice in the base list or twice in one workstream list
- **THEN** any process that reads the config refuses to proceed and reports the duplicate
- **Cases**: keeps `tests/cases/create/repeated-name-within-one-list.yaml`

#### Scenario: One type per field name
- **WHEN** the base list declares `{ name: hours, type: number }` and workstream `support` declares `{ name: hours, type: text }`, or two workstreams declare `due` as a `date` and as a `text`
- **THEN** any process that reads the config refuses to proceed, names the field and the two lists that disagree
- **Cases**: keeps `tests/cases/config/one-type-per-field-name.yaml`

### Requirement: Config validation precedes any write
A process that reads the config SHALL validate both files before any action and, when
they fail, refuse, writing nothing, with one message that starts with
`invalid gemba config` and lists every problem of both files, one per line with the
path of its file; a file that is not valid YAML with its parse error, the other file
still checked. A check that needs another value SHALL run only on what parsed, so that
one mistake is reported once.

#### Scenario: Malformed YAML
- **WHEN** `gemba.yaml` cannot be parsed as YAML
- **THEN** the process stops, reports the parse error, and writes nothing
- **Cases**: keeps `tests/cases/create/malformed-yaml.yaml`

#### Scenario: Every problem reported at once
- **WHEN** `gemba.yaml` declares two workstreams with the same prefix and a field `hours` of type `integer`, and `gemba.local.yaml` declares `ide: ""` and `obeya: nakatomi`
- **THEN** any process that reads the config refuses to proceed with one message that names the two workstreams, the field `hours`, `ide` and `obeya`, each problem with the path of its file, and writes nothing
- **Cases**: keeps `tests/cases/config/every-problem-reported-at-once.yaml`

#### Scenario: One mistake reported once
- **WHEN** `workstreams` in `gemba.yaml` is a list, `default_workstream` is `support`, and `gemba.local.yaml` declares `create.rules` under `workstreams.support`
- **THEN** the refusal names `workstreams` and says nothing of the default workstream or of the workstream of the personal config
- **Cases**: keeps `tests/cases/config/one-mistake-reported-once.yaml`

#### Scenario: Malformed personal YAML
- **WHEN** `gemba.local.yaml` cannot be parsed as YAML and `gemba.yaml` declares two workstreams with the same prefix
- **THEN** the process refuses to proceed with one message that names `gemba.local.yaml` with its parse error and the two workstreams of `gemba.yaml`, and writes nothing
- **Cases**: keeps `tests/cases/config/malformed-personal-yaml.yaml`

### Requirement: IDE command
The personal config MAY declare `ide`, the command that opens a folder in the person's
IDE, to which `launch` appends the harness path. It SHALL be a non-empty string, split
into a command and its arguments as a POSIX shell would, or a map of `command`, a
non-empty string, and optional `args`, a list of strings: `"code -n"` and
`{command: code, args: [-n]}` mean the same. Any other value SHALL be refused, naming
`ide` and its file. A process that does not open the IDE SHALL proceed without it.

#### Scenario: IDE command accepted
- **WHEN** the personal config declares `ide: "code -n"`
- **THEN** every process that reads the config accepts it and `launch` starts `code -n <harness path>`
- **Cases**: keeps `tests/cases/harness/ide-opened.yaml`

#### Scenario: Structured IDE command accepted
- **WHEN** the personal config declares `ide: { command: code, args: [-n] }`
- **THEN** every process that reads the config accepts it, `gemba config show` prints it as declared, and `launch` starts `code -n <harness path>` and prints `opening: code -n` followed by the path
- **Cases**: keeps `tests/cases/config/structured-ide-command-accepted.yaml`

#### Scenario: Malformed IDE command refused
- **WHEN** the `ide` of the personal config is an empty string, a list, a map without `command`, a map whose `command` is empty or not a string, or a map whose `args` is not a list of strings
- **THEN** any process that reads the config refuses to proceed and names `ide` and `gemba.local.yaml`
- **Cases**: keeps `tests/cases/config/malformed-ide-command-refused.yaml`

#### Scenario: IDE absent for a process that does not open it
- **WHEN** the config has no `ide` key and a task is created
- **THEN** the create process proceeds exactly as before
- **Cases**: keeps `tests/cases/config/ide-absent-for-create.yaml`

### Requirement: Obeya, repositories folder and branch prefix
The shared config MAY declare `obeya`, the name of the obeya, and the personal config
`branch_prefix`, `gemba` when absent: kebab-case names, segments of the branch of a
run. The personal config MAY declare `repos_dir`, a non-empty string, the folder whose
immediate subfolders are the repositories a run may check out: absolute, starting with
`~`, or relative to the obeya root. Other values SHALL be refused, naming the key and
its file; a process that does not need a key SHALL proceed without it.

#### Scenario: Obeya and repositories folder accepted
- **WHEN** the shared config declares `obeya: nakatomi` and the personal config declares `repos_dir: ~/projects` and `branch_prefix: nk`
- **THEN** every process that reads the config accepts it, and a task is created as before
- **Cases**: keeps `tests/cases/config/obeya-and-repos-dir-accepted.yaml`

#### Scenario: Malformed obeya or branch prefix refused
- **WHEN** the `obeya` of the shared config is `Nakatomi Corp`, an empty string or a list, or the `branch_prefix` of the personal config is `Gemba/`
- **THEN** any process that reads the config refuses to proceed and names the key
- **Cases**: keeps `tests/cases/config/malformed-obeya-or-branch-prefix-refused.yaml`

#### Scenario: Malformed repositories folder refused
- **WHEN** the `repos_dir` of the personal config is an empty string, a list or a map
- **THEN** any process that reads the config refuses to proceed and names `repos_dir`
- **Cases**: keeps `tests/cases/config/malformed-repos-dir-refused.yaml`

#### Scenario: Keys absent for a process that does not need them
- **WHEN** neither file declares `obeya`, `repos_dir` or `branch_prefix` and a task is created
- **THEN** the create process proceeds exactly as before
- **Cases**: keeps `tests/cases/config/worktree-keys-absent-for-create.yaml`

### Requirement: Keys of each layer
Each top-level key SHALL have a layer: only the shared config holds `metadata`,
`default_workstream`, `obeya` and the workstream catalogue; only the personal config
holds `ide`, `repos_dir` and `branch_prefix`; both may hold `agent_providers` and
process blocks, at top level or under `workstreams`. A key in the wrong file SHALL be
refused, naming the file it goes in. `organization` SHALL be refused in either file as
renamed `obeya`, which belongs in `gemba.yaml`. Other keys SHALL be ignored.

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

## REMOVED Requirements

### Requirement: Per-process customization block
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Process
blocks of a workstream" and "Blocks of the harness and worktree groups".

### Requirement: Base process blocks and the effective block
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Base
process blocks", "The effective block of a process" and "The later rule wins".

### Requirement: Agent providers
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Agent
providers of each file" and "Agent providers are validated".

## ADDED Requirements

### Requirement: Process blocks of a workstream
A workstream block MAY hold a block per Gemba process: `create`, `list`, `record`,
`report`, `mark`, `archive` and `set`, each one verb, and the groups `harness` and
`worktree`. A verb block MAY hold `rules`, non-empty strings the agent follows while
running that verb for that workstream, and `context`, background it reads first. Every
process SHALL validate the shape of every known block, read only its own, a verb of a
group only its verb's, and ignore the blocks it does not know.

#### Scenario: Create rules applied
- **WHEN** workstream `deployments` declares `create.rules` containing "environment is production or staging; ask if not stated"
- **THEN** an agent creating a task in `deployments` follows that rule before creating the file
- **Cases**: keeps `tests/cases/create/create-rules-applied.yaml`

#### Scenario: List rules applied
- **WHEN** workstream `support` declares `list.rules` containing "always mention the client next to the title"
- **THEN** an agent listing `support` tasks follows that rule when rendering the result
- **Cases**: keeps the entry `gemba-config: List rules applied` of `tests/not-automated.yaml`

#### Scenario: Unknown process block ignored
- **WHEN** a workstream declares a block named `publish` and the create process runs
- **THEN** the create process behaves exactly as if the `publish` block were absent
- **Cases**: keeps `tests/cases/create/unknown-process-block-ignored.yaml`

#### Scenario: Malformed process block
- **WHEN** a workstream declares `list.rules` as a string instead of a list, or `list.context` as a list instead of a string
- **THEN** any process that reads the config refuses to proceed and names the workstream and the block
- **Cases**: keeps `tests/cases/list/malformed-process-block.yaml`

#### Scenario: Record and report blocks accepted
- **WHEN** workstream `support` declares `record.rules` and `report.context`
- **THEN** every process that reads the config accepts it, and a task is created in `support` as before
- **Cases**: keeps `tests/cases/config/record-and-report-blocks-accepted.yaml`

#### Scenario: Malformed record or report block
- **WHEN** a workstream declares `record.rules` as a string, or `report.context` as a list
- **THEN** any process that reads the config refuses to proceed and names the workstream and the block
- **Cases**: keeps `tests/cases/config/malformed-record-or-report-block.yaml`

#### Scenario: Mark and archive blocks accepted
- **WHEN** workstream `support` declares `mark.rules` and `archive.context`
- **THEN** every process that reads the config accepts it, and a task is created in `support` as before
- **Cases**: keeps `tests/cases/config/mark-and-archive-blocks-accepted.yaml`

#### Scenario: Malformed mark or archive block
- **WHEN** a workstream declares `mark.rules` as a string, or `archive.context` as a list
- **THEN** any process that reads the config refuses to proceed and names the workstream and the block
- **Cases**: keeps `tests/cases/config/malformed-mark-or-archive-block.yaml`

#### Scenario: Set block accepted
- **WHEN** workstream `support` declares `set.rules` and `set.context`
- **THEN** every process that reads the config accepts it, and a task is created in `support` as before
- **Cases**: keeps `tests/cases/config/set-block-accepted.yaml`

#### Scenario: Malformed set block
- **WHEN** a workstream declares `set.rules` as a string, or `set.context` as a list
- **THEN** any process that reads the config refuses to proceed and names the workstream and the block
- **Cases**: keeps `tests/cases/config/malformed-set-block.yaml`

### Requirement: Blocks of the harness and worktree groups
The `harness` block MAY hold a verb block for each of `launch`, `note`, `resolve` and
`remove`, and `guide`, a non-empty string that `launch` renders into the guide of the
harness. The `worktree` block MAY hold a verb block for each of `add`, `list` and
`remove`. Any other key inside either group, `guide` inside `worktree` included, SHALL
be refused.

#### Scenario: Harness verb blocks accepted
- **WHEN** workstream `code-reviews` declares `harness.guide`, `harness.note.rules`, `harness.resolve.context` and `harness.remove.rules`
- **THEN** every process that reads the config accepts it, and launching a `code-reviews` task renders the guide text
- **Cases**: keeps `tests/cases/config/harness-verb-blocks-accepted.yaml`

#### Scenario: Malformed harness block
- **WHEN** a workstream declares `harness.guide` as a list, `harness.note.rules` as a string, or a key inside `harness` that is neither `guide` nor a verb of the group, such as `harness.rules`
- **THEN** any process that reads the config refuses to proceed and names the workstream and the offending key
- **Cases**: keeps `tests/cases/config/malformed-harness-block.yaml`

#### Scenario: Worktree verb blocks accepted
- **WHEN** workstream `code-reviews` declares `worktree.add.rules`, `worktree.list.context` and `worktree.remove.rules`
- **THEN** every process that reads the config accepts it, and a task is created in `code-reviews` as before
- **Cases**: keeps `tests/cases/config/worktree-verb-blocks-accepted.yaml`

#### Scenario: Malformed worktree block
- **WHEN** a workstream declares `worktree.add.rules` as a string, `worktree.guide`, or a key inside `worktree` that is not a verb of the group, such as `worktree.rules`
- **THEN** any process that reads the config refuses to proceed and names the workstream and the offending key
- **Cases**: keeps `tests/cases/config/malformed-worktree-block.yaml`

### Requirement: Base process blocks
Each file of the config MAY declare at its top level any process block a workstream
block may hold, with the same keys and shapes: the base blocks, shared by every
workstream. A malformed base block SHALL be refused, naming its file, the top level
and the offending key. When a process runs over several workstreams, the base blocks
SHALL apply once, alongside the blocks of each. A config with no base block and no
personal config SHALL behave as before.

#### Scenario: Base blocks accepted
- **WHEN** the top level of the config declares `create.context`, `harness.guide`, `harness.note.rules` and `worktree.add.rules`, and no workstream declares a process block
- **THEN** every process that reads the config accepts it, a task is created as before, and launching a task renders the base guide text
- **Cases**: keeps `tests/cases/config/base-blocks-accepted.yaml`

#### Scenario: Malformed base block
- **WHEN** the top level of the config declares `list.rules` as a string, `harness.guide` as a list, or a key inside `harness` that is neither `guide` nor a verb of the group, such as `harness.rules`
- **THEN** any process that reads the config refuses to proceed, names the top level and the offending key, and writes nothing
- **Cases**: keeps `tests/cases/config/malformed-base-block.yaml`

### Requirement: The effective block of a process
The effective block of a process, or of a verb of a group, for a workstream SHALL join
four levels in order: the shared base block, the workstream's shared block, the
personal base block and the workstream's personal block. Its `context` is the context
of every level, one empty line apart; its `rules`, the rules of every level.
`gemba config show` SHALL print the effective blocks and metadata schemas, and a skill
SHALL have the agent read them there, never combining the levels of the files.

#### Scenario: Base and workstream blocks followed together
- **WHEN** the top level declares `create.context` and `create.rules` containing "ask who requested the work if not stated", and workstream `deployments` declares `create.rules` containing "environment is production or staging; ask if not stated"
- **THEN** an agent creating a task in `deployments` reads the effective `create` block of `deployments` from `gemba config show`, the base context first and both rules, the base one first, and follows both before creating the file
- **Cases**: keeps the entry `gemba-config: Base and workstream blocks followed together` of `tests/not-automated.yaml`

### Requirement: The later rule wins
The agent SHALL follow every rule of the effective block. When two rules contradict,
it SHALL follow the later one: the rule of the workstream over the base rule of the
same file, and any rule of the personal config over any rule of the shared config.

#### Scenario: Workstream rule wins over a base rule
- **WHEN** the top level declares `worktree.add.rules` containing "start from the default branch of origin" and workstream `support` declares `worktree.add.rules` containing "start from the branch deployed to production"
- **THEN** an agent adding a worktree in a `support` harness reads both rules in that order from `gemba config show` and starts from the branch deployed to production
- **Cases**: keeps the entry `gemba-config: Workstream rule wins over a base rule` of `tests/not-automated.yaml`

#### Scenario: Personal rule wins over a shared rule
- **WHEN** workstream `support` of `gemba.yaml` declares `worktree.add.rules` containing "start from the branch deployed to production" and the top level of `gemba.local.yaml` declares `worktree.add.rules` containing "start from the default branch of origin"
- **THEN** an agent adding a worktree in a `support` harness reads both rules in that order from `gemba config show` and starts from the default branch of origin
- **Cases**: keeps the entry `gemba-config: Personal rule wins over a shared rule` of `tests/not-automated.yaml`

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
- **Cases**: keeps `tests/cases/skills/one-folder-per-declared-provider.yaml`

#### Scenario: Providers absent for a process that does not need them
- **WHEN** the config has no `agent_providers` key and a task is created
- **THEN** the create process proceeds exactly as before
- **Cases**: keeps `tests/cases/config/providers-absent-for-create.yaml`

#### Scenario: Providers declared in both files
- **WHEN** `gemba.yaml` declares `agent_providers: [claude, agents]` and `gemba.local.yaml` declares `agent_providers: [claude]`
- **THEN** every process that reads the config accepts it, and `gemba config show` prints `agent_providers` as `[claude, agents]` and `harness_providers` as `[claude]`
- **Cases**: keeps `tests/cases/config/providers-declared-in-both-files.yaml`

### Requirement: Agent providers are validated
In either file, `agent_providers` SHALL be a non-empty list of providers the CLI
knows, `claude` and `agents`, none of them twice. Any process that reads the config
SHALL refuse a list that is malformed, names an unknown provider or repeats one,
naming its file and the known providers.

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

#### Scenario: Unknown personal provider refused
- **WHEN** `gemba.local.yaml` declares `agent_providers: [cursor]`
- **THEN** any process that reads the config refuses to proceed and names `gemba.local.yaml`, `cursor` and the known providers
- **Cases**: keeps `tests/cases/config/unknown-personal-provider-refused.yaml`
