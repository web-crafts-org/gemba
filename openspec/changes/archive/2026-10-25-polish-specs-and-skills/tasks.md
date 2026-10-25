# Tasks

## 1. Requirements under the limit

- [x] 1.1 Add the rule of D3 to `rules.specs` in `openspec/config.yaml`. Verify that `openspec instructions specs --change polish-specs-and-skills` prints it inside `<rules>`, and that `openspec validate polish-specs-and-skills --strict` still passes.
- [x] 1.2 Write `tests/cases/harness/guide-explains-notes-and-assets.yaml` for the scenario "Guide explains notes and assets". Model it on `guide-names-the-always-rules.yaml`: launch `SUP-1`, then expect fragments of `CLAUDE.md`, each within one line of the guide asset: notes as the memory of the run, small and frequent; the draft under `notes/` filed with the `gemba-harness` skill; no hand-written frontmatter; assets under `assets/` named `<unix-timestamp>-<slug>.<ext>`; and gemba committing when a note is filed. The guide already says all of it, so the case passes from the start and guards the text. Verify with `-k` that it passes, and that `GEMBA_CHANGE=polish-specs-and-skills` `test_scenarios.py` no longer lists the scenario.

## 2. Notes as links

- [x] 2.1 Add the entry `harness-notes: Note awaiting approval linked` to `tests/not-automated.yaml`. Its reason: the agent links the note and asks for the approval by following the `gemba-harness` skill. Verify that `test_exemptions_are_current` passes and that `GEMBA_CHANGE=polish-specs-and-skills` `test_scenarios.py` no longer lists it.
- [x] 2.2 In `src/gemba/assets/skills/gemba-harness/SKILL.md`, rewrite step 6 of Note and step 6 of Resolve as D4 says. The agent gives the note as `[<path>](<path>)` with the path the command printed, never the path of the draft. For a note that waits for approval, it keeps the reminder that the user sets `approved: true` from that link and that a yes in the chat is not one. Add a line on the `gemba-harness` skill under Changed in the `[Unreleased]` section of `CHANGELOG.md`. Verify that every case under `tests/cases/skills/`, `tests/cases/init/` and `tests/cases/harness/` passes, and that `uv run gemba skills update` in a scratch obeya writes the new text.

## 3. `gemba worktree list --available`

- [x] 3.1 Write `tests/cases/worktree/repositories-listed.yaml`, `no-repository-to-list.yaml` and `repositories-folder-missing-for-the-list-refused.yaml` for the three scenarios of "List shows the repositories that can be added". In `repositories-listed.yaml`, attach `nakatomi-web` in `setup` and expect `stdout` to be exactly `nakatomi-api` and `nakatomi-web`, with `unchanged: true`. In `no-repository-to-list.yaml`, give `repos_dir` a folder that holds only a plain subfolder with a file. The refusal case has two documents: one with no `repos_dir`, expecting `repos_dir` and `gemba.local.yaml` on stderr, and one whose `repos_dir` names a file, expecting `is not a folder`. Verify with `-k` that each one fails.
- [x] 3.2 Implement D5. In `src/gemba/worktree.py`, add `NO_REPOSITORIES` and the refusal of a missing `repos_dir`, which `add` then uses in place of its inline message. In `src/gemba/commands/worktree.py`, add the `--available` flag of `list`, with its help, over `repositories()`. Add a unit test in `tests/test_worktree.py` for any new domain function. Run the checks of `.claude/skills/guidelines/cross-platform` on the diff. Verify that the three cases and every case under `tests/cases/worktree/` pass, and that `uv run gemba worktree list --help` shows the flag.
- [x] 3.3 Add `gemba worktree list --available` to the worktree commands of `README.md`, with a comment naming the repositories `add` accepts, and an entry under Added in the `[Unreleased]` section of `CHANGELOG.md`. Verify that the command runs as written in a scratch obeya with a harness and a `repos_dir`.

## 4. The agent looks the repository up

- [x] 4.1 Add the entries `harness-worktrees: Repository found by its exact name` and `harness-worktrees: Repository chosen by the user` to `tests/not-automated.yaml`. Their reason: the agent matches the request against `gemba worktree list --available` and asks the user by following the `gemba-worktree` skill. Verify that `GEMBA_CHANGE=polish-specs-and-skills` `test_scenarios.py` lists no uncovered scenario and that `test_exemptions_are_current` passes.
- [x] 4.2 In `src/gemba/assets/skills/gemba-worktree/SKILL.md`, rewrite step 1 of Add as D6 says, and remove "never browse `repos_dir` or any folder above the harness to guess it". The agent still never reads `repos_dir` itself. In step 5, treat a refusal of `add` that lists the repositories as step 1 does. In List, name `--available`. Add a line on the `gemba-worktree` skill under Changed in the `[Unreleased]` section of `CHANGELOG.md`. Verify that every case under `tests/cases/skills/` and `tests/cases/harness/` passes, and that `git grep -n "browse" src/gemba/assets/skills/gemba-worktree` finds nothing.

## 5. Integration

- [x] 5.1 Run `uv run ruff format .`, `uv run ruff check .`, `uv run pyright` and `uv run python -m unittest discover -s tests`, then `GEMBA_CHANGE=polish-specs-and-skills uv run python -m unittest discover -s tests -p test_scenarios.py` and `openspec validate polish-specs-and-skills --strict`. Run the sync of D2 on a copy of `openspec/`, then `openspec validate --specs` there. Verify that every check passes, that the copy reports 0 issues and no requirement over 500 characters, and that the comparison of D2 finds no scenario lost and no scenario text changed but the two of `harness-notes`.

## Workflow follow-up

- Push the branch and open the pull request only through an approved `external-action` note of the harness that names the branch of the remote.
- Archive as D2 says: sync the 19 specs by script, each part of a split in the place of its requirement and no `**Cases**` line kept, then `openspec archive polish-specs-and-skills --skip-specs --yes`. Check that `openspec validate --specs` reports no warning and that `test_scenarios.py` passes against the main specs alone.
- Then propose `team-mode`, keeping each new requirement under 500 characters as the rule of D3 asks.
