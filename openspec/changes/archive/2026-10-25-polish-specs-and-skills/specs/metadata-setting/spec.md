# Spec Delta

## MODIFIED Requirements

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
- **Cases**: keeps `tests/cases/set/text-kept-as-written.yaml`

#### Scenario: Sums are exact
- **WHEN** `gemba set SUP-1 hours+=0.2` runs on a task with `hours: 0.1`, and `gemba set SUP-2 hours+=0.5` on a task with `hours: 1.5`
- **THEN** the first reads `hours: 0.3` and the second `hours: 2`
- **Cases**: keeps `tests/cases/set/sums-are-exact.yaml`

## REMOVED Requirements

### Requirement: Set writes metadata values of a task
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "Set
writes each assignment", "Set refuses an invalid assignment" and "Set reports each
value".

### Requirement: Setting by the agent
**Reason**: Longer than the 500 characters OpenSpec allows a requirement, because it
states several behaviors; split into one requirement per behavior.
**Migration**: Its text and its scenarios, unchanged in meaning, are now in "The agent
sets what the user says" and "The agent reuses the spelling in use".

## ADDED Requirements

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
- **Cases**: keeps `tests/cases/set/values-set.yaml`

#### Scenario: Number added to a total
- **WHEN** `gemba set SUP-1 hours+=2.5` runs on a task with `hours: 12`, and then on a task with `hours: null`
- **THEN** the first reads `hours: 14.5` with the output `hours: 12 -> 14.5`, and the second reads `hours: 2.5`
- **Cases**: keeps `tests/cases/set/number-added-to-a-total.yaml`

#### Scenario: Value cleared
- **WHEN** `gemba set SUP-1 client=null` runs on an optional field that holds `acme`
- **THEN** the field reads `client: null` and the output holds `client: acme -> null`
- **Cases**: keeps `tests/cases/set/value-cleared.yaml`

#### Scenario: Text list set
- **WHEN** `gemba set SUP-1 project=checkout project=landing` runs on a text field
- **THEN** the field reads `project: [checkout, landing]`, replacing any previous value
- **Cases**: keeps `tests/cases/set/text-list-set.yaml`

#### Scenario: Archived or done task set
- **WHEN** the task with the ref is `done`, or lies under an `archive/` folder
- **THEN** its metadata is written like any other task's, in place
- **Cases**: keeps `tests/cases/set/archived-or-done-task-set.yaml`

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
- **Cases**: keeps `tests/cases/set/problems-reported-together.yaml`

#### Scenario: Required field not cleared
- **WHEN** `client` is required for the task's workstream and `gemba set SUP-1 client=null` runs
- **THEN** the command exits 1, says `client` is required, and writes nothing
- **Cases**: keeps `tests/cases/set/required-field-not-cleared.yaml`

#### Scenario: Unknown ref refused
- **WHEN** no task under `tasks/` has the ref given
- **THEN** the command exits 1, reports that no task has that ref, and writes nothing
- **Cases**: keeps `tests/cases/set/unknown-ref-refused.yaml`

### Requirement: Set reports each value
On success `gemba set` SHALL print the task path relative to the obeya root, then one
line per assigned key, `<key>: <old> -> <new>`, or `<key>: <value> (unchanged)` when
it did not change, values as they read in YAML flow style, and exit 0. When no value
changes, it SHALL write nothing.

#### Scenario: Same value left as it was
- **WHEN** `gemba set SUP-1 client=acme` runs on a task whose `client` is already `acme`
- **THEN** the command exits 0, the output says `client: acme (unchanged)`, and the tree is unchanged
- **Cases**: keeps `tests/cases/set/same-value-left-as-it-was.yaml`

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
- **Cases**: keeps the entry `metadata-setting: Agent sets a value` of `tests/not-automated.yaml`

#### Scenario: Agent follows the verb's rules
- **WHEN** workstream `support` declares `set.rules` containing "set invoiced only when the task is done"
- **THEN** the agent follows that rule before running the command for a `support` task
- **Cases**: keeps the entry `metadata-setting: Agent follows the verb's rules` of `tests/not-automated.yaml`

### Requirement: The agent reuses the spelling in use
For a text field, the agent SHALL look up the values already in use with
`gemba report --by <field>` and reuse their spelling when the user means one of them,
asking when it cannot tell.

#### Scenario: Spelling in use reused
- **WHEN** the user says a task is for "ACME" and the text field `client` already holds `acme` on other tasks
- **THEN** the agent finds `acme` with `gemba report --by client` and sets `client=acme`, asking when it cannot tell whether the user means the value in use
- **Cases**: keeps the entry `metadata-setting: Spelling in use reused` of `tests/not-automated.yaml`
