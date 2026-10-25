# metadata-setting Specification

## Purpose

Setting writes the metadata of a task after its creation, through one command that
converts every value by the declared type of its field, so that a value known later, a
correction or a growing total is a frontmatter fact a command can trust and never a
hand edit.

## Requirements

### Requirement: Set writes each assignment
`gemba set <ref> <assignment> [<assignment> ...]` SHALL resolve the task with that ref
anywhere under `tasks/`, archives included, and write each assignment into its
`metadata`: `<key>=<value>` sets the value, `<key>=null` clears it, and
`<key>+=<number>` adds the number to a number field, a `null` or missing value
counting as zero. A key given more than once with `=` SHALL set a list, in the order
given.

#### Scenario: Values set
- **WHEN** `gemba set SUP-1 client=acme invoiced=2026-10-03` runs on a task whose `client` and `invoiced` are `null`, `client` a text field and `invoiced` a date field
- **THEN** its `metadata` reads `client: acme` and `invoiced: 2026-10-03`, and the output holds the path, `client: null -> acme` and `invoiced: null -> 2026-10-03`

#### Scenario: Number added to a total
- **WHEN** `gemba set SUP-1 hours+=2.5` runs on a task with `hours: 12`, and then on a task with `hours: null`
- **THEN** the first reads `hours: 14.5` with the output `hours: 12 -> 14.5`, and the second reads `hours: 2.5`

#### Scenario: Value cleared
- **WHEN** `gemba set SUP-1 client=null` runs on an optional field that holds `acme`
- **THEN** the field reads `client: null` and the output holds `client: acme -> null`

#### Scenario: Text list set
- **WHEN** `gemba set SUP-1 project=checkout project=landing` runs on a text field
- **THEN** the field reads `project: [checkout, landing]`, replacing any previous value

#### Scenario: Archived or done task set
- **WHEN** the task with the ref is `done`, or lies under an `archive/` folder
- **THEN** its metadata is written like any other task's, in place

### Requirement: Set refuses an invalid assignment
The command SHALL refuse, writing nothing, when no task has that ref, when a key is
not in the effective schema of the task's workstream, when a value does not convert to
its field's type, when `+=` names a field that is not a `number` or holds no number,
when a key is repeated for a field that is not `text` or given with both `=` and `+=`,
or when a required field would be left `null`, reporting every problem in one message
and exiting 1.

#### Scenario: Problems reported together
- **WHEN** one call gives an undeclared key `ticket`, `hours=two` on a number field, `invoiced+=1` on a date field and `billed=true` twice on a boolean field
- **THEN** the command exits 1, one message names the four problems, and nothing is written

#### Scenario: Required field not cleared
- **WHEN** `client` is required for the task's workstream and `gemba set SUP-1 client=null` runs
- **THEN** the command exits 1, says `client` is required, and writes nothing

#### Scenario: Unknown ref refused
- **WHEN** no task under `tasks/` has the ref given
- **THEN** the command exits 1, reports that no task has that ref, and writes nothing

### Requirement: Set reports each value
On success `gemba set` SHALL print the task path relative to the obeya root, then one
line per assigned key, `<key>: <old> -> <new>`, or `<key>: <value> (unchanged)` when
it did not change, values as they read in YAML flow style, and exit 0. When no value
changes, it SHALL write nothing.

#### Scenario: Same value left as it was
- **WHEN** `gemba set SUP-1 client=acme` runs on a task whose `client` is already `acme`
- **THEN** the command exits 0, the output says `client: acme (unchanged)`, and the tree is unchanged

### Requirement: Values follow the declared type
Each value SHALL be converted by its field's type, never read as YAML: a `text` kept
exactly as written; a `number` a decimal literal, an optional minus sign, digits
without leading zeros and an optional fractional part; a `boolean` `true` or `false`;
a `date` an ISO `YYYY-MM-DD` date; `null` clears any type. Sums SHALL be exact in
decimal (`0.1` plus `0.2` is `0.3`), and a whole total SHALL be written as an integer.
The value written SHALL read back in YAML as its type, quoted when needed.

#### Scenario: Text kept as written
- **WHEN** `gemba set SUP-1 client=no code=007` runs on two text fields
- **THEN** the frontmatter holds `client: 'no'` and `code: '007'`, both read back as text

#### Scenario: Sums are exact
- **WHEN** `gemba set SUP-1 hours+=0.2` runs on a task with `hours: 0.1`, and `gemba set SUP-2 hours+=0.5` on a task with `hours: 1.5`
- **THEN** the first reads `hours: 0.3` and the second `hours: 2`

### Requirement: Setting touches nothing but the metadata
`set` SHALL write only the task file and only its `metadata`: `status`, `ref`,
`updated_at` and `done_at` SHALL be written as they were, the frontmatter SHALL keep its
fixed key order, and the body SHALL be kept byte for byte. `updated_at` SHALL NOT move:
metadata is data about the task, not activity on it. The command SHALL NOT touch the
harness of the task, if one exists, and SHALL run no git. It SHALL work from any folder
below the obeya root, a harness included.

#### Scenario: Only the metadata changes
- **WHEN** `gemba set SUP-1 hours+=2` runs on a `done` task with `done_at`, a description, a link line and two recorded days
- **THEN** only the value of `hours` differs: the other frontmatter lines, `updated_at` included, and the body are byte for byte what they were

#### Scenario: Set from inside the harness
- **WHEN** `gemba set SUP-1 hours+=1` runs from inside the launched harness of `SUP-1`
- **THEN** the task file holds the new value, and the harness repository has the same commits as after the launch and a clean working tree

### Requirement: An older task takes the current schema
When `set` writes a task, the `metadata` map SHALL hold every key of the current
effective schema of the task's workstream, in the schema's order, each with its value,
or `null` for a key the task lacked, followed by every key the schema no longer
declares, with its value as it was. The command SHALL print `<key>: added as null` for
every key it added, and SHALL never remove a key.

#### Scenario: Field declared after the task was created
- **WHEN** the schema declares `client` and `invoiced`, a task created before `invoiced` existed holds only `client: acme`, and `gemba set SUP-1 client=globex` runs
- **THEN** its `metadata` reads `client: globex` and `invoiced: null`, and the output holds `client: acme -> globex` and `invoiced: added as null`

#### Scenario: Field no longer declared kept
- **WHEN** a task holds `ticket_id: PROD-1`, the config no longer declares `ticket_id`, and a declared field is set
- **THEN** `ticket_id: PROD-1` is written after the declared keys, as it was

### Requirement: The agent sets what the user says
The `gemba-set` skill SHALL have the agent identify the task by its ref, from
`harness.yaml` inside a harness, asking when the request is ambiguous; follow the
`set` block of its workstream; map what the user says to declared fields by their
names and descriptions; write each value in the form of its type, with `+=` whenever
the user adds to an amount, never summing itself; run `gemba set` once with every
assignment, relay the output and stop, never editing the frontmatter by hand.

#### Scenario: Agent sets a value
- **WHEN** the user says a task took two more hours, or that it was invoiced today
- **THEN** the agent runs `gemba set` with `+=2` on the number field, or today's date on the date field, and relays the output

#### Scenario: Agent follows the verb's rules
- **WHEN** workstream `support` declares `set.rules` containing "set invoiced only when the task is done"
- **THEN** the agent follows that rule before running the command for a `support` task

### Requirement: The agent reuses the spelling in use
For a text field, the agent SHALL look up the values already in use with
`gemba report --by <field>` and reuse their spelling when the user means one of them,
asking when it cannot tell.

#### Scenario: Spelling in use reused
- **WHEN** the user says a task is for "ACME" and the text field `client` already holds `acme` on other tasks
- **THEN** the agent finds `acme` with `gemba report --by client` and sets `client=acme`, asking when it cannot tell whether the user means the value in use

### Requirement: Skill contains no configured value
The `gemba-set` skill SHALL contain only the process and SHALL NOT name any workstream,
prefix, metadata field or configured rule. It MAY branch on the declared type
of a field, never on its name or meaning.

#### Scenario: Config change without skill change
- **WHEN** a metadata field is added, retyped or removed in `gemba.yaml`
- **THEN** the skill needs no edit for the agent to set it
