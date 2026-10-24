# Tasks

## 1. Case runner seams

- [ ] 1.1 In `tests/test_cases.py`, add `local_config:`, the content of `gemba.local.yaml` as a map or as raw text, written like `config:`, and `stderr_excludes:`, strings standard error must not contain; describe both in the module docstring and add one runner test for each beside the existing ones; verify the full suite passes unchanged.

## 2. Two files and the layer of each key

- [ ] 2.1 Move `ide`, `repos_dir` and `branch_prefix` from `config:` to `local_config:` in the 37 cases the delta specs mark "moves to the personal config" (6 under `tests/cases/config/`, 8 under `tests/cases/harness/`, 23 under `tests/cases/worktree/`), and make `tests/cases/config/malformed-ide-command-refused.yaml` expect `gemba.local.yaml` and `tests/cases/worktree/config-without-organization-or-repos-dir-refused.yaml` expect the file of each missing key; verify with `-k` that the moved cases fail.
- [ ] 2.2 Write `tests/cases/config/personal-keys-refused-in-the-shared-config.yaml`, `shared-keys-refused-in-the-personal-config.yaml`, `unknown-personal-provider-refused.yaml` and `personal-config-read-from-below-the-root.yaml` (asserting `ide` with `stdout_contains`, so the document can grow), and verify they fail; write `unknown-keys-ignored-in-both-files.yaml`, `empty-personal-config.yaml` and `tests/cases/skills/personal-providers-leave-the-tasks-repo-skills.yaml`, which pin guarantees that already hold, and verify they pass before and after 2.3.
- [ ] 2.3 In `src/gemba/config.py`, add `LOCAL_FILENAME` and read `gemba.local.yaml` at the root found by `gemba.yaml`, an empty file as an empty map (D1); add the layer table of D2 and refuse the misplaced keys of both files in one message, each with the file it goes in; read `ide`, `repos_dir` and `branch_prefix` from the personal file and `agent_providers` from both, keeping the personal list on `Config` with the `harness_providers` property (D5); leave unknown keys ignored; make the missing `repos_dir` message of `src/gemba/commands/worktree.py` name `gemba.local.yaml`; verify the cases of 2.1 and 2.2 pass and `tests/test_config.py` covers the table, the empty file and `harness_providers`.

## 3. Every problem of both files at once

- [ ] 3.1 Write `tests/cases/config/every-problem-reported-at-once.yaml`, `one-mistake-reported-once.yaml` (with `stderr_excludes` for the default workstream and the personal workstream) and `malformed-personal-yaml.yaml`; verify they fail.
- [ ] 3.2 In `src/gemba/metadata.py`, make `parse_fields` check every declaration and return the fields that parsed with the problems of the others, and add `type_problems` beside `types`, which keeps raising for its runtime callers (D3); verify `tests/test_metadata.py` covers two bad declarations of one list and two names that disagree in type.
- [ ] 3.3 In `src/gemba/config.py`, accumulate every problem of both files instead of raising on the first, run each dependent check only on valid inputs, keep checking the other file when one is not valid YAML, and render `ConfigError` as `invalid gemba config:` with one `- <path>: <message>` line per problem (D3); update the message assertions of `tests/test_config.py`; verify the cases of 3.1 pass and every case under `tests/cases/config/`, `create/` and `list/` passes unchanged.

## 4. Personal process blocks and the effective block

- [ ] 4.1 Write `tests/cases/config/personal-blocks-accepted.yaml`, `personal-workstream-not-in-the-catalogue-refused.yaml`, `workstream-definition-refused-in-the-personal-config.yaml` and `malformed-personal-block.yaml`, and add the entry `gemba-config: Personal rule wins over a shared rule` to `tests/not-automated.yaml` with the reason of the spec; verify the cases fail.
- [ ] 4.2 In `src/gemba/config.py`, parse the personal base blocks and `workstreams` of the personal config (identifiers of the shared catalogue, process blocks only, `prefix`, `description` and `metadata` refused naming `gemba.yaml`), validated with the rules of the shared blocks and naming `gemba.local.yaml`; make `effective_block` join the four levels in the order of the spec, generalize the join of contexts to any number of texts, add `user` to `Guide` and print it from `effective_processes` (D4); verify the cases of 4.1 pass and `tests/test_config.py` covers the order of the four levels and the join of three and four contexts.

## 5. `gemba config check` and `gemba config show`

- [ ] 5.1 Write `tests/cases/config/check-summarizes-the-personal-config.yaml`, `providers-declared-in-both-files.yaml` and `show-joins-the-personal-blocks.yaml`, and add `harness_providers` and `guide.user` to the documents expected by `show-prints-the-effective-config.yaml`, `show-combines-the-levels.yaml`, `show-one-workstream.yaml`, `show-from-inside-a-harness.yaml` and `structured-ide-command-accepted.yaml`; verify they fail.
- [ ] 5.2 In `src/gemba/commands/config.py`, print `gemba.local.yaml is valid` when the personal config exists and `harness providers:` when it declares providers, add `harness_providers` and `guide.user` to the document of `show`, and name both files in the help texts (D6); verify the cases of 5.1 pass and `check-summarizes-a-valid-config.yaml` and `check-with-no-providers.yaml` pass unchanged.

## 6. Launch: the personal providers and the `Your user` section

- [ ] 6.1 Write `tests/cases/harness/harness-launched-for-the-personal-providers.yaml`, `user-section-rendered.yaml` and `every-guide-section-rendered.yaml`; verify they fail.
- [ ] 6.2 In `src/gemba/harness.py`, add `USER_HEADING = "## Your user"` and make `render_guide` render the user text last (D7); in `src/gemba/commands/harness.py`, make launch read `harness_providers` for the refusal of a missing list, the guides, the harness skills and `harness.yaml` (D5), and pass `Guide.user` to `render_guide`; verify the cases of 6.1 pass, `tests/test_harness.py` covers `render_guide` with every combination of the three texts, and every case under `tests/cases/harness/` passes.

## 7. `gemba init` ignores the personal config

- [ ] 7.1 Update `tests/cases/init/tasks-repo-scaffolded.yaml` (the `.gitignore` holds both lines and `gemba.local.yaml` is absent), `scaffolded-at-a-path.yaml` and `missing-pieces-completed.yaml` (both lines appended in order), add a case whose personal config declares `organization` to `invalid-config-refused.yaml`, and write `personal-config-ignored-in-an-earlier-tasks-repo.yaml`; verify the updated and new cases fail, except the added refusal, which passes since group 2.
- [ ] 7.2 In `src/gemba/repo.py`, replace `IGNORED_LINE` by `IGNORED_LINES = ("harnesses/", "gemba.local.yaml")` and make `gitignore_text` mirror `gitattributes_text` (D8), and update the help text of `src/gemba/commands/init.py`; verify `tests/test_repo.py` covers no file, both lines missing, one missing and both present, and every case under `tests/cases/init/` passes.

## 8. Skills

- [ ] 8.1 In `src/gemba/assets/skills/gemba-config/SKILL.md`, name `gemba.local.yaml` in the description, give every key of the reference the file it belongs in, add a section on the personal config and its `workstreams` entries, have the agent ask where a key both files hold goes, edit the file a key belongs in and create `gemba.local.yaml` when needed, fix every problem `gemba config check` reports, move the keys of an earlier `gemba.yaml` (a section of its own), and run `gemba skills update` only when the shared providers changed; add the entry `config-maintenance: Keys of an earlier config moved` to `tests/not-automated.yaml`; verify `tests/test_skills.py` passes and the reference names every key of the layer table of `config.py`.
- [ ] 8.2 In `src/gemba/assets/skills/gemba-init/SKILL.md`, have questions 6 and 7 write `ide` and `repos_dir` into `gemba.local.yaml`, step 8 write the other answers into `gemba.yaml` through the `gemba-config` skill, and step 9 say that `gemba.local.yaml` stays on this machine and that git ignores it; verify `tests/test_skills.py` passes and `uv run gemba skills check` in a scratch tasks repo reports the two skills as outdated.

## 9. Documents

- [ ] 9.1 In `AGENTS.md`, define the gemba config as the shared config, `gemba.yaml`, and the personal config, `gemba.local.yaml`, and say that the IDE and the `repos_dir` of the worktrees are declared in the personal config; verify `grep -n 'gemba.yaml' AGENTS.md` shows no line that still gives a personal key to `gemba.yaml`.
- [ ] 9.2 In `README.md`, show both files in the config section and add `gemba.local.yaml` to what `init` writes into the `.gitignore`, leaving the upgrade to `CHANGELOG.md`; verify every command shown runs as written in a scratch tasks repo.
- [ ] 9.3 In `SECURITY.md`, say that `ide` and `repos_dir` are read from `gemba.local.yaml` only, which git ignores, so that no command a teammate commits runs on your machine; add the change to the Unreleased section of `CHANGELOG.md`, the move of the three keys under Changed as breaking and the personal config under Added; verify both files read correctly.
- [ ] 9.4 Edit the Purpose of `openspec/specs/gemba-config/spec.md`, "the single customization layer", and of `openspec/specs/config-maintenance/spec.md`, which names `gemba.yaml` alone, to the two files, since archiving syncs requirements only; verify `openspec validate --specs --strict` passes.

## 10. Integration

- [ ] 10.1 Run `uv run ruff format .`, `uv run ruff check .`, `uv run pyright` and `uv run python -m unittest discover -s tests`, then `GEMBA_CHANGE=personal-config-layer uv run python -m unittest discover -s tests -p test_scenarios.py`; verify all pass with no case or exemption missing.

## Workflow follow-up

- Push the branch and open the merge request only through an approved `external-action` note of the harness that names the branch of the remote.
- After the review, archive the change with `openspec archive`, which syncs the eight specs, and check that the synced main specs carry no `**Cases**` lines, as the earlier archives left none.
