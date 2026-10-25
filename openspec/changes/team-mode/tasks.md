# Tasks

## 1. The team in the config

- [ ] 1.1 Write the cases of the `gemba-config` scenarios under `tests/cases/config/`: `team-accepted.yaml`, `malformed-team-refused.yaml` (every fault of the scenario in one document, each named in `stderr_contains`), `repeated-initials-refused.yaml`, `member-named-after-a-workstream-refused.yaml`, `unknown-member-refused.yaml`, `member-without-a-team-refused.yaml`, `team-keys-refused-in-the-wrong-file.yaml` and `team-declared-over-an-obeya-without-a-team.yaml` (run with `list`, `tasks/support/` holding `SUP-1`, `unchanged: true`). Add a document for `owner` to `reserved-field-name-refused.yaml`. Verify with `-k` that each fails, except `team-accepted.yaml`, which the current CLI passes since it ignores unknown keys, and which then guards that both keys are accepted.
- [ ] 1.2 Implement D1 to D3: `src/gemba/team.py` with `Member`, the pattern of initials and `layout_problem`; in `src/gemba/config.py`, `team` and `me` in `LAYERS`, `_parse_team`, `me` in `_parse_personal`, `Config.team`, `Config.me` and `Config.members`, and the call of `layout_problem` in `load`; `owner` in `metadata.RESERVED`. Add unit tests in `tests/test_config.py` (every fault of `team` and `me` at once, a bad member not echoed by `me`) and `tests/test_team.py` (`layout_problem`, paths built as POSIX). Run the checks of `.claude/skills/guidelines/cross-platform` on the diff. Verify that the cases of 1.1 and every case under `tests/cases/config/` pass.
- [ ] 1.3 Write `tests/cases/config/team-summarized.yaml` (`stdout` exact) and `team-shown.yaml` (`stdout_json`, one workstream, no `me`). Verify with `-k` that both fail.
- [ ] 1.4 Implement D8 in `src/gemba/commands/config.py`, with the help texts of `check` and `show`. Verify that both cases and every existing `show` and `check` case pass unchanged.
- [ ] 1.5 Add the entries `config-maintenance: Member added`, `config-maintenance: Member who leaves kept` and `config-maintenance: Team not added over existing tasks` to `tests/not-automated.yaml`, the agent following the `gemba-config` skill. Update `src/gemba/assets/skills/gemba-config/SKILL.md` as D9 says. Add *team*, *member* and *owner* to the vocabulary of `AGENTS.md`, and the team, `me` and the breaking reserved name `owner` to `[Unreleased]` in `CHANGELOG.md`. Verify that `test_exemptions_are_current` and every case under `tests/cases/skills/` and `tests/cases/init/` pass.

## 2. Refs and creation in a team

- [ ] 2.1 Write under `tests/cases/create/`: `task-placed-in-its-member-folder.yaml`, `ref-of-a-members-task.yaml` (a create document, and a list document over the file it writes, with `setup` and `--date 2026-10-25`), `counters-of-two-members.yaml` and `write-without-a-member-refused.yaml` (`unchanged: true`). Verify with `-k` that each fails.
- [ ] 2.2 Implement D4 and the guard of D5 for `create`: `FILENAME_PATTERN` and `next_ref` with initials in `src/gemba/tasks.py`, `write_problems` in `src/gemba/team.py`, and the folder of `me` and its initials in `src/gemba/commands/create.py`. Add unit tests in `tests/test_tasks.py` (both forms of a filename, separate counters for a bare prefix and for two members' initials) and `tests/test_team.py` (the three problems of `write_problems`, the file name taken as an argument). Verify that the four cases and every case under `tests/cases/create/` pass.
- [ ] 2.3 Add the entry `task-ownership: Task asked for another member` to `tests/not-automated.yaml`, and update `src/gemba/assets/skills/gemba-create/SKILL.md` as D9 says. Verify that `test_exemptions_are_current` and every case under `tests/cases/skills/` pass.

## 3. Reading an obeya with a team

- [ ] 3.1 Write under `tests/cases/list/`: `tasks-of-every-member-listed.yaml` (with and without `--include-archived`), `folder-that-is-not-a-member.yaml`, `folder-of-a-member-that-is-not-a-workstream.yaml`, `record-of-a-members-task.yaml` (`stdout_json`), `tasks-of-an-inactive-member-read.yaml`, `tasks-of-one-member.yaml`, `owner-filter-without-a-team-refused.yaml` and `unknown-owner-refused.yaml`. Verify with `-k` that each fails.
- [ ] 3.2 Implement D6 and the listing part of D7: `Task.owner`, `read` and `scan` with `owners`, `find_by_ref` with `owners` and `archive_destination` in `src/gemba/tasks.py`; `--owner` and `Scope.owners` in `src/gemba/commands/selection.py`; `gemba list` leaving `owner` out without a team; every caller of `scan` and `find_by_ref` passing `Config.members` (`mark`, `set`, `archive`, `record`, `harness launch` and `remove`), and `record` inside a harness deriving the owner from `harness.yaml`. Add unit tests in `tests/test_tasks.py` for the scan of member folders and its strays. Verify that the cases of 3.1, every case under `tests/cases/list/` and the full suite pass.
- [ ] 3.3 Add the entries `task-listing: My open tasks in a team` and `task-listing: Open tasks of the team` to `tests/not-automated.yaml`, update `src/gemba/assets/skills/gemba-list/SKILL.md` as D9 says, and add `--owner` to `[Unreleased]` in `CHANGELOG.md`. Verify that `test_exemptions_are_current` and every case under `tests/cases/skills/` pass.

## 4. Reporting by owner

- [ ] 4.1 Write `tests/cases/report/report-by-owner.yaml`, `tests/cases/report/grouping-by-owner-without-a-team-refused.yaml` and `tests/cases/list/tasks-read-without-a-member.yaml` (a `list` document and a `report --by owner` document, no `local_config`). Verify with `-k` that each fails.
- [ ] 4.2 Implement the reporting part of D7 in `src/gemba/report.py` and `src/gemba/commands/report.py`: `owner` refused without a team, the owner's group, the order of the team. Add unit tests in `tests/test_report.py`. Verify that the three cases and every case under `tests/cases/report/` pass.
- [ ] 4.3 Add the entries `task-reporting: What I did in a team` and `task-reporting: Report of the team` to `tests/not-automated.yaml`, update `src/gemba/assets/skills/gemba-report/SKILL.md` as D9 says, and add `--by owner` to `[Unreleased]` in `CHANGELOG.md`. Verify that `test_exemptions_are_current` and every case under `tests/cases/skills/` pass.

## 5. The write guard

- [ ] 5.1 Write `tests/cases/mark/inactive-member-writes-nothing.yaml`, `tests/cases/mark/another-members-task-not-marked.yaml`, `tests/cases/set/another-members-task-not-set.yaml`, `tests/cases/record/another-members-task-not-recorded.yaml`, `tests/cases/archive/another-members-task-not-archived.yaml` (`MR-SUP-1` archived into `tasks/manuel/support/archive/`, exit 1), `tests/cases/harness/another-members-task-not-launched.yaml` and `tests/cases/harness/own-task-launched.yaml` (`links` or the `task.md` content, `--no-open`). Verify with `-k` that each refusal case fails; `own-task-launched.yaml` passes after group 3 and then guards the launch of a member's task.
- [ ] 5.2 Implement D5 in `src/gemba/commands/record.py`, `mark.py`, `set.py`, `archive.py` and `harness.py` (launch), each adding the problems of `write_problems` to its own. Verify that the cases of 5.1 and every case under `tests/cases/` pass.
- [ ] 5.3 Add the entry `task-ownership: Refusal of another member's task relayed` to `tests/not-automated.yaml`, and the rule of D9 to the `gemba-record`, `gemba-mark`, `gemba-set`, `gemba-archive` and `gemba-harness` skills. Write the section of the README and the line of `SECURITY.md` of D10, and the guard in `[Unreleased]` of `CHANGELOG.md`. Verify that `test_exemptions_are_current` and every case under `tests/cases/skills/` pass, and that the commands of the README section run as written in a scratch obeya with a team of two clones.

## 6. The init skill

- [ ] 6.1 Add the entries `repo-initialization: Team asked after the obeya's name`, `repo-initialization: Member configures a new clone` and `repo-initialization: User not yet a member` to `tests/not-automated.yaml`, the agent following the `gemba-init` skill. Verify that `GEMBA_CHANGE=team-mode` `test_scenarios.py` lists no uncovered scenario and that `test_exemptions_are_current` passes.
- [ ] 6.2 Update `src/gemba/assets/skills/gemba-init/SKILL.md` as D9 says, and add the skills of this change to the line of `[Unreleased]` in `CHANGELOG.md` that asks to run `gemba skills update`. Verify that every case under `tests/cases/skills/` and `tests/cases/init/` passes, and that `uv run gemba skills update` in a scratch obeya writes the new texts.

## 7. Integration

- [ ] 7.1 Run `uv run ruff format .`, `uv run ruff check .`, `uv run pyright` and `uv run python -m unittest discover -s tests`, then `GEMBA_CHANGE=team-mode uv run python -m unittest discover -s tests -p test_scenarios.py`, `openspec validate team-mode --strict` and `openspec validate --specs`. Run the checks of `.claude/skills/guidelines/cross-platform` on the whole diff, new files included. Verify that every check passes, that no existing case changed its expectation apart from the new document of `reserved-field-name-refused.yaml`, and that every requirement of the deltas is at 500 characters or fewer.

## Workflow follow-up

- Push the branch and open the pull request only through an approved `external-action` note of the harness that names the branch of the remote.
- Archive with the specs synced: the new main spec `task-ownership`, the ADDED requirements appended, the MODIFIED ones replaced in place, no `**Cases**` line kept. Check that `openspec validate --specs` reports no warning and that `test_scenarios.py` passes against the main specs alone.
- Then propose `task-relations`, over the layout and the refs of this change.
