# Spec Delta

## ADDED Requirements

### Requirement: Grouping by owner
A report grouped by `owner` SHALL put each task in the group of its owner, the groups
following the order of the members in the team. In an obeya without a team, `--by
owner` SHALL be refused together with every other invalid input, saying that the obeya
declares no team.

#### Scenario: Report by owner
- **WHEN** the team declares `manuel` then `ana`, and `gemba report --by owner --sum hours` runs over `MR-SUP-1` (`hours: 2`), `AG-SUP-1` (`hours: 3`) and `AG-OPS-1` (`hours: 1`)
- **THEN** the groups are `manuel` with 1 task, ref `MR-SUP-1` and `hours` total 2, then `ana` with 2 tasks, refs `AG-SUP-1` and `AG-OPS-1` in listing order and `hours` total 4, and the total holds 3 tasks and 6 hours
- **Cases**: adds `tests/cases/report/report-by-owner.yaml`

#### Scenario: Grouping by owner without a team refused
- **WHEN** `gemba report --by owner` runs in an obeya whose shared config declares no team
- **THEN** nothing is printed on standard output, the exit status is non-zero, and the message says that the obeya declares no team
- **Cases**: adds `tests/cases/report/grouping-by-owner-without-a-team-refused.yaml`

### Requirement: A member's report covers their own work
In an obeya with a team, the agent SHALL report the work of `me`, read from `gemba
config show`, adding `--owner <me>` to the candidates and to `gemba report`, unless the
user asks for another member, named by their folder, or for the whole team, which it
groups by `owner`.

#### Scenario: What I did in a team
- **WHEN** `me` is `manuel` and the user asks what they did yesterday
- **THEN** the agent lists the candidates with `--owner manuel` and reports only `manuel`'s tasks
- **Cases**: adds the entry `task-reporting: What I did in a team` of `tests/not-automated.yaml`

#### Scenario: Report of the team
- **WHEN** the user asks how many hours the team spent in September
- **THEN** the agent runs `gemba report` without an owner filter and with `--by owner`, and reports each member's total and the team's
- **Cases**: adds the entry `task-reporting: Report of the team` of `tests/not-automated.yaml`

## MODIFIED Requirements

### Requirement: Report inputs
`gemba report` SHALL take the selection filters of `gemba list`, with the same names,
values, validation and semantics, and MAY take groupings, `--by`, each `workstream`,
`status`, `owner` or a declared `text` or `boolean` metadata key, and sums, `--sum`,
each a declared `number` key, both repeatable, a key given twice to either being
invalid. It SHALL validate every input before scanning and, when any is invalid, print
nothing, exit non-zero and report every invalid input in one message.

#### Scenario: Selection as in the listing
- **WHEN** `gemba report --done-from 2026-09-01 --done-to 2026-09-30 --where client=acme` runs over tasks done in August and September for `acme` and for `globex`
- **THEN** the total counts exactly the tasks `gemba list` returns with the same filters, the `acme` tasks done in September
- **Cases**: keeps `tests/cases/report/selection-as-in-the-listing.yaml`

#### Scenario: Invalid inputs reported together
- **WHEN** one call gives `--by hours` on a number field, `--sum client` on a text field, `--by ticket` with no such field declared, and `--status closed`
- **THEN** nothing is printed on standard output, the exit status is non-zero, and one message names the four problems
- **Cases**: keeps `tests/cases/report/invalid-inputs-reported-together.yaml`
