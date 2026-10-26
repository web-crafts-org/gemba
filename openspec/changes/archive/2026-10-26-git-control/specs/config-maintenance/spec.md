# Spec Delta

## MODIFIED Requirements

### Requirement: Check summarizes the team
When the shared config declares a team, `gemba config check` SHALL also print, right
after the `default workstream:` line, a `team:` line with every member in config order
as `<member> (<INITIALS>)`, or `<member> (<INITIALS>, inactive)` for an inactive one,
then a `me:` line naming the member of the clone when the personal config declares
one, then `git hooks: on` or `git hooks: off`, as both files resolve `git_hooks` for the
clone. Without a team it SHALL print none of these lines.

#### Scenario: Team summarized
- **WHEN** `gemba config check` runs in an obeya whose team declares `manuel` (`MR`) and `ana` (`AG`, `active: false`), whose personal config declares `me: manuel`, and where neither file declares `git_hooks`
- **THEN** the output holds `team: manuel (MR), ana (AG, inactive)` right after the `default workstream:` line, then `me: manuel`, then `git hooks: off`, the tree is untouched and the exit code is 0
- **Cases**: modifies `tests/cases/config/team-summarized.yaml` (its output gains `git hooks: off` after `me: manuel`)

### Requirement: Show prints the team
In an obeya with a team, the document of `gemba config show` SHALL also hold `team`,
a map of each member, in config order, to its `initials` and `active`, the default
applied; `me`, `null` when the personal config declares none; and `git_hooks`, `true` or
`false`, as both files resolve it for the clone. Without a team, the document SHALL hold
none of these keys.

#### Scenario: Team shown
- **WHEN** `gemba config show` runs in an obeya whose team declares `manuel` (`MR`) and `ana` (`AG`, `active: false`), whose personal config declares no `me`, and where neither file declares `git_hooks`
- **THEN** `team` maps `manuel` to `initials` `MR` and `active` `true` and `ana` to `initials` `AG` and `active` `false`, `me` is `null`, `git_hooks` is `false`, and the exit code is 0
- **Cases**: modifies `tests/cases/config/team-shown.yaml` (its document gains `git_hooks: false` after `me`)
