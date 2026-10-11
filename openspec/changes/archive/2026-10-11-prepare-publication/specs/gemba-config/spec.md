# Spec Delta

## MODIFIED Requirements

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
