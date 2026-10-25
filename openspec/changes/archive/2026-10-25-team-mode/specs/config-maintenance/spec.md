# Spec Delta

## ADDED Requirements

### Requirement: Check summarizes the team
When the shared config declares a team, `gemba config check` SHALL also print, right
after the `default workstream:` line, a `team:` line with every member in config order
as `<member> (<INITIALS>)`, or `<member> (<INITIALS>, inactive)` for an inactive one,
then a `me:` line naming the member of the clone when the personal config declares
one. Without a team it SHALL print neither line.

#### Scenario: Team summarized
- **WHEN** `gemba config check` runs in an obeya whose team declares `manuel` (`MR`) and `ana` (`AG`, `active: false`) and whose personal config declares `me: manuel`
- **THEN** the output holds `team: manuel (MR), ana (AG, inactive)` right after the `default workstream:` line, then `me: manuel`, the tree is untouched and the exit code is 0
- **Cases**: adds `tests/cases/config/team-summarized.yaml`

### Requirement: Show prints the team
In an obeya with a team, the document of `gemba config show` SHALL also hold `team`,
a map of each member, in config order, to its `initials` and `active`, the default
applied, and `me`, `null` when the personal config declares none. Without a team, the
document SHALL hold neither key.

#### Scenario: Team shown
- **WHEN** `gemba config show` runs in an obeya whose team declares `manuel` (`MR`) and `ana` (`AG`, `active: false`) and whose personal config declares no `me`
- **THEN** `team` maps `manuel` to `initials` `MR` and `active` `true` and `ana` to `initials` `AG` and `active` `false`, `me` is `null`, and the exit code is 0
- **Cases**: adds `tests/cases/config/team-shown.yaml`

### Requirement: The agent maintains the team
Following the `gemba-config` skill, the agent SHALL add a member with a folder name and
initials no member ever used, mark a member who leaves `active: false` and never remove
one or reuse their initials, since refs are never reused, and SHALL never add `team` to
an obeya whose `tasks/` holds tasks, pointing to the `gemba-migrate` skill instead.

#### Scenario: Member added
- **WHEN** the user asks to add `ana` to the team of the obeya
- **THEN** the agent proposes initials no member used, adds `ana` to `team` in `gemba.yaml`, verifies it with `gemba config check`, and says that `ana` declares `me` in the personal config of her own clone
- **Cases**: adds the entry `config-maintenance: Member added` of `tests/not-automated.yaml`

#### Scenario: Member who leaves kept
- **WHEN** the user says that `ana` left the team
- **THEN** the agent sets `active: false` on `ana` and removes neither her entry nor her tasks
- **Cases**: adds the entry `config-maintenance: Member who leaves kept` of `tests/not-automated.yaml`

#### Scenario: Team not added over existing tasks
- **WHEN** the user asks to share with a team an obeya whose `tasks/` holds tasks
- **THEN** the agent explains that a team starts in a new obeya, offers to bring the tasks with the `gemba-migrate` skill, and leaves `gemba.yaml` as it is
- **Cases**: adds the entry `config-maintenance: Team not added over existing tasks` of `tests/not-automated.yaml`
