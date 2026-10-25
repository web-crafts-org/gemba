# Spec Delta

## MODIFIED Requirements

### Requirement: Supported platforms
The gemba CLI SHALL run on Linux, macOS and Windows 10 or later, needing only Python
3.11 or later and `git` on PATH, with no administrator rights, no developer mode and
no particular shell, and SHALL behave the same on every platform: same commands,
same output, same exit codes. An obeya or a harness created on one platform
SHALL be usable on another.

#### Scenario: Suite passes on every platform
- **WHEN** a commit is pushed or a pull request is opened
- **THEN** the full test suite passes on Linux, on macOS and on Windows
- **Cases**: keeps the entry `platform-support: Suite passes on every platform` of `tests/not-automated.yaml`

#### Scenario: Obeya used across platforms
- **WHEN** an obeya created on Linux, with its tasks and its config, is cloned on Windows
- **THEN** every command reads its tasks, creates and marks tasks in it, and launches a harness, with no edit to any file
- **Cases**: modifies the entry `platform-support: Tasks repo used across platforms` of `tests/not-automated.yaml` (now `platform-support: Obeya used across platforms`; its reason says obeya)
