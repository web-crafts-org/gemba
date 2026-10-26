# Spec Delta

## ADDED Requirements

### Requirement: Numbers of a subtree
When the user asks how much went into a task together with the tasks split from it,
the agent SHALL take the numbers from `gemba report --under <ref> --include-archived`,
with no period and no owner filter unless the user names one, grouping `--by owner` in
an obeya with a team when asked per member, and SHALL say that they cover the task and
its subtree.

#### Scenario: Hours of a task with its subtasks
- **WHEN** the user asks how many hours each member put into `MR-DEV-1` with its subtasks
- **THEN** the agent runs `gemba report --under MR-DEV-1 --include-archived --sum hours --by owner`, and states each member's total and the total as printed, saying that they cover `MR-DEV-1` and its subtree
- **Cases**: adds the entry `task-reporting: Hours of a task with its subtasks` of `tests/not-automated.yaml`
