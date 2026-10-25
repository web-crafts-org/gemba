# Spec Delta

## ADDED Requirements

### Requirement: The team of the shared config
The shared config MAY declare `team`, a non-empty map keyed by the folder name of each
member: kebab-case, not reserved on Windows, and not the identifier of a workstream.
Each entry SHALL hold `initials`, one or more uppercase ASCII letters used by no other
member, and MAY hold `active`, a boolean, `true` when absent. Any other shape, key or
value SHALL be refused, naming the member and the key.

#### Scenario: Team accepted
- **WHEN** the shared config declares a team with `manuel` (`initials: MR`) and `ana` (`initials: AG`, `active: false`), and the personal config declares `me: manuel`
- **THEN** every process that reads the config accepts it, and `gemba list` exits 0
- **Cases**: adds `tests/cases/config/team-accepted.yaml`

#### Scenario: Malformed team refused
- **WHEN** `team` is a list, or a member is named `Ana`, has initials `mr` or none, declares `active: yes`, or holds a key `email`
- **THEN** any process that reads the config refuses to proceed with one message that names each member and each key at fault
- **Cases**: adds `tests/cases/config/malformed-team-refused.yaml`

#### Scenario: Repeated initials refused
- **WHEN** the members `manuel` and `mario` both declare `initials: MR`
- **THEN** any process that reads the config refuses to proceed and names both members and the initials
- **Cases**: adds `tests/cases/config/repeated-initials-refused.yaml`

#### Scenario: Member named after a workstream refused
- **WHEN** the team declares a member `support` and the catalogue a workstream `support`
- **THEN** any process that reads the config refuses to proceed and names the member
- **Cases**: adds `tests/cases/config/member-named-after-a-workstream-refused.yaml`

### Requirement: The member of a clone
The personal config MAY declare `me`, the folder name of the member of the team the
clone belongs to, active or not. `me` SHALL be refused when the shared config declares
no team, and when it names no member of the team, listing the members.

#### Scenario: Unknown member refused
- **WHEN** the team declares `manuel` and `ana` and the personal config declares `me: bob`
- **THEN** any process that reads the config refuses to proceed, names `bob` and lists `manuel` and `ana`
- **Cases**: adds `tests/cases/config/unknown-member-refused.yaml`

#### Scenario: Member without a team refused
- **WHEN** the personal config declares `me: manuel` and the shared config declares no team
- **THEN** any process that reads the config refuses to proceed and says that `me` needs a team in `gemba.yaml`
- **Cases**: adds `tests/cases/config/member-without-a-team-refused.yaml`

### Requirement: A team starts in a new obeya
When the shared config declares a team, every process that reads the config SHALL
refuse to proceed while a folder directly under `tasks/` bears the identifier of a
workstream, the layout of an obeya without a team, naming each such folder and the
`gemba-migrate` skill, which brings earlier tasks into a new obeya. No command converts
an obeya in place.

#### Scenario: Team declared over an obeya without a team
- **WHEN** `gemba.yaml` declares a team while `tasks/support/` holds the task `SUP-1`
- **THEN** any process that reads the config, `gemba list` included, refuses to proceed with a message that names `tasks/support` and the `gemba-migrate` skill, and writes nothing
- **Cases**: adds `tests/cases/config/team-declared-over-an-obeya-without-a-team.yaml`

## MODIFIED Requirements

### Requirement: Metadata field declaration
A metadata field declaration SHALL be a map of `name`, required, in snake_case;
`type`, required, one of `text`, `number`, `boolean` and `date`; `required`, a
boolean, `false` by default; and `description`, optional, when the name alone does not
say what is expected. The type sets how a value is handled, never what it means. Any
other key, allowed values and defaults included, SHALL be refused, and so SHALL the
names `workstream`, `status` and `owner`, by which the report groups tasks.

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
- **WHEN** a declaration is named `status`, `workstream` or `owner`
- **THEN** any process that reads the config refuses to proceed and says the name is reserved
- **Cases**: modifies `tests/cases/config/reserved-field-name-refused.yaml`, which gains a document for `owner`

### Requirement: Keys of each layer
Each top-level key SHALL have a layer: only the shared config holds `metadata`,
`default_workstream`, `obeya`, `team` and the workstream catalogue; only the personal
config holds `ide`, `repos_dir`, `branch_prefix` and `me`; both may hold
`agent_providers` and process blocks, at top level or under `workstreams`. A key in the
wrong file SHALL be refused, naming the file it goes in. `organization` SHALL be
refused in either file as renamed `obeya`. Other keys SHALL be ignored.

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
- **Cases**: adds `tests/cases/config/team-keys-refused-in-the-wrong-file.yaml`
