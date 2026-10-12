# Tasks

## 1. Case runner seams for the new contracts

- [ ] 1.1 In `tests/test_cases.py`, decode the output of every command run as UTF-8 explicitly, add a `lf_only:` check (the named files hold no CR byte), let a `tree` value given as YAML `!!binary` be written as bytes, add `{root}` to `expand()`, write a `code.cmd` stub (`@exit /b 0`) beside the shell stub, and compare `links:` targets as POSIX paths after normalizing separators; verify the full suite still passes on Linux.

## 2. Text contract: LF written, CRLF read, UTF-8 out

- [ ] 2.1 Write the cases `tests/cases/create/task-created-with-lf.yaml`, `tests/cases/record/crlf-task-rewritten-with-lf.yaml`, `tests/cases/record/task-with-crlf-recorded.yaml` and `tests/cases/harness/task-with-crlf-started.yaml` (CRLF content through `\r\n` escapes in the YAML `tree`); verify the CRLF record and start cases fail and the LF cases fail on the CRLF input.
- [ ] 2.2 Create `src/gemba/platform.py` with `decode()` (UTF-8, CRLF and CR to LF), the reserved device names and `is_reserved_name()`, the detached-start `Popen` options per platform, the deletion error classification and the retry schedule, each fully annotated with a module docstring saying what it owns; verify `tests/test_platform.py` covers every function.
- [ ] 2.3 Open the task file of `create.py` with `newline="\n"` and route every `read_bytes().decode()` of a task file, a draft or a note in `record.py` and `commands/harness.py` through `platform.decode()`; verify the four cases of 2.1 pass and the record, mark, set and harness cases still pass.
- [ ] 2.4 Write `tests/cases/harness/draft-with-crlf-filed.yaml` (a body with CRLF and a leading byte-order mark through `\r\n` and `﻿` escapes in the `tree`, checked with `files:` and `lf_only:`) and `tests/cases/harness/draft-not-utf-8-refused.yaml` (a UTF-16 draft, which needs the runner's `tree` to accept bytes through a `!!binary` value); verify the first fails on the byte-order mark and the second passes through the existing refusal.
- [ ] 2.5 File the body of a draft through `platform.decode()` in `commands/harness.py`, keeping the "not UTF-8 text" refusal and `decode()` dropping a leading byte-order mark; verify the cases of 2.4 pass and `tests/cases/harness/note-filed.yaml` still passes.
- [ ] 2.6 Write the cases `tests/cases/list/non-ascii-text-listed.yaml` (accents and an emoji in a description, checked in `stdout_json`) and `tests/cases/create/non-ascii-error-reported.yaml` (an unknown workstream with accents named on stderr); verify they pass on a UTF-8 locale and fail under `PYTHONIOENCODING=ascii`.
- [ ] 2.7 In `cli.main`, reconfigure `sys.stdout` and `sys.stderr` to UTF-8 before dispatching, guarded for streams without `reconfigure`; verify `PYTHONIOENCODING=ascii uv run gemba list --json` prints the accents intact and the cases of 2.6 pass under that variable.
- [ ] 2.8 Move the identity hint into `harness.git_hints(problem)` and add the long-path hint naming `core.longpaths` for a "Filename too long" message, used by `git_failure` in `commands/harness.py` and by the worktree adapter; verify a unit test in `tests/test_harness.py` covers both hints and the absence of a hint.
- [ ] 2.9 Add the entries `platform-support: Suite passes on every platform`, `platform-support: Tasks repo used across platforms`, `platform-support: Rule applied wherever a name is validated` and `platform-support: Git failure on a long path hinted` to `tests/not-automated.yaml` with the reasons of the spec; verify `GEMBA_CHANGE=windows-support uv run python -m unittest discover -s tests -p test_scenarios.py` reports no missing case for `platform-support`.

## 3. `task.md`: a link where the system allows it, a file elsewhere

- [ ] 3.1 Rename and reword `tests/cases/harness/task-linked.yaml` to say the link is made where the system allows it, assertions unchanged; verify it passes.
- [ ] 3.2 Add `harness.task_link_content(task)` (the relative POSIX path plus a newline) and make `write_layout` fall back to writing that file when `symlink_to` raises `OSError`, with the link creation injectable; verify a unit test in `tests/test_harness.py` with a failing link creation checks the file content, and add the entry `harness-launch: Task path written when the system refuses links` to `tests/not-automated.yaml`.
- [ ] 3.3 Write `tests/cases/harness/guide-describes-both-forms-of-the-task-link.yaml` and update the fragments of `tests/cases/harness/guide-names-the-always-rules.yaml`; verify both fail.
- [ ] 3.4 Reword the first section, the third rule and the layout line of `src/gemba/assets/harness/guide.md` as the harness-guide delta says (both forms, the read at the named path, the permission the tool may ask, read-only in both forms) and update the reason of the entry `harness-launch: Agent reads the task through the link` in `tests/not-automated.yaml`; verify the two cases of 3.3 pass and `tests/test_skills.py` passes.

## 4. The `ide` command: string or `{command, args}`, resolved and detached

- [ ] 4.1 Write `tests/cases/config/structured-ide-command-accepted.yaml` (map form; `config show` prints it as declared; launch prints `opening: code -n` and the harness folder name) and `tests/cases/harness/ide-command-not-found.yaml`, add the malformed maps to `tests/cases/config/malformed-ide-command-refused.yaml`, and drop the `/` assumption from `tests/cases/harness/ide-opened.yaml`; verify the new and modified assertions fail.
- [ ] 4.2 In `config.py`, parse `ide` into an `Ide` frozen dataclass (`command`, `args`) from the string through `shlex.split` in POSIX mode or from the map, keeping the declaration as written for `config show`, and report every malformed shape with `ide` named; verify `tests/test_config.py` covers both forms and the malformed shapes, and the config cases of 4.1 pass.
- [ ] 4.3 In `open_ide`, resolve the command with `shutil.which`, fail with the "could not be started" message naming the declared command when it resolves to nothing, start `[executable, *args, folder]` with the detached options of `platform.py`, and print `opening:` with the declaration followed by the path; verify the harness cases of 4.1 pass, including `code.cmd` on the Windows job once 9.1 lands.
- [ ] 4.4 Update the `ide` row of `src/gemba/assets/skills/gemba-config/SKILL.md` and the IDE question of `src/gemba/assets/skills/gemba-init/SKILL.md` to name both forms and the quoting rule of the string; verify `tests/test_skills.py` passes and `uv run gemba skills check` in a scratch tasks repo reports the two skills as outdated.

## 5. Removal that finishes what the system allows

- [ ] 5.1 Add the entries `harness-removal: Read-only files deleted`, `harness-removal: Path held by another program reported` and `harness-worktrees: Worktree path held by another program reported` to `tests/not-automated.yaml` with the reasons of the specs, and write the unit test of the deletion policy in `tests/test_harness.py` with a fake `rmtree` that first raises a read-only `PermissionError`, then a held one, then keeps failing; verify the test fails for want of `delete_tree`.
- [ ] 5.2 Add `delete_tree(folder, *, rmtree, sleep)` to `commands/harness.py`: the error handler (`onexc` from 3.12, `onerror` on 3.11) clears the read-only bit and retries, a held path follows the retry schedule of `platform.py`, and what stays held is reported with the message of the spec; make `harness remove` use it; verify the unit test of 5.1 passes and every harness removal case passes.
- [ ] 5.3 In `commands/worktree.py`, wrap `git worktree remove` with the same retry and the same message when git reports a held path, through the hints of 2.8; verify the worktree removal cases pass and the unit test covers the held message for a worktree.

## 6. Names portable to every platform

- [ ] 6.1 Write `tests/cases/config/reserved-workstream-identifier-refused.yaml` (`nul`, `con`, `aux`, `prn`, `com1`, `lpt1`, each named with "reserved on Windows") and `tests/cases/harness/reserved-note-slug-refused.yaml` (`notes/aux.md` and `notes/com1.md`); verify both fail.
- [ ] 6.2 Refuse reserved names in the workstream check of `config.py` and in `harness.check_draft`, through `platform.is_reserved_name()`, reported together with the other problems of the same call; verify the cases of 6.1 pass and `tests/test_config.py` covers the message.

## 7. `.gitattributes` of the scaffold

- [ ] 7.1 Update `tests/cases/init/tasks-repo-scaffolded.yaml`, `tests/cases/init/scaffolded-at-a-path.yaml`, `tests/cases/init/second-run-changes-nothing.yaml` and `tests/cases/init/missing-pieces-completed.yaml` for the `.gitattributes` (written, kept, updated with one line missing, in the output order of the spec); verify all four fail.
- [ ] 7.2 Add `GITATTRIBUTES_LINES` and `gitattributes_text(existing)` to `repo.py`, mirroring `gitignore_text`, and write, update or keep the file in `init.py` right after the `.gitignore`; verify `tests/test_repo.py` covers the three outcomes and the init cases pass.

## 8. Skills read the date without a shell

- [ ] 8.1 Replace `date +%F` in the seven skills (`gemba-archive`, `gemba-mark`, `gemba-report`, `gemba-set`, `gemba-list`, `gemba-record`, and the second mention of `gemba-mark`) with reading today's date from the environment, naming `date +%F` for a POSIX shell and `Get-Date -Format yyyy-MM-dd` for PowerShell; verify `grep -rn 'date +%F' src/gemba/assets` lists only the parenthetical mentions and `tests/test_skills.py` passes.

## 9. CI, package metadata and documents

- [ ] 9.1 In `.github/workflows/ci.yml`, keep Linux on 3.11 to 3.14 and run macOS and Windows on 3.11 and 3.14 with no step touching the runner's git, replacing the one-version comment of the macOS job with the two-axes rationale; verify the file parses as YAML and the six platform jobs are green on the pull request.
- [ ] 9.2 Add `Operating System :: Microsoft :: Windows` to the classifiers of `pyproject.toml`, assert the three platform classifiers in `tests/test_package.py`, and add the entry `package-release: Suite run per platform and interpreter` to `tests/not-automated.yaml`; verify `tests/test_package.py` and `tests/test_scenarios.py` pass.
- [ ] 9.3 In `README.md`, name uv and git as the prerequisites, add the Windows notes (install from PowerShell, the quoting rule of a string `ide` and the `{command, args}` form, developer mode as optional for the link, `core.longpaths`, `git add --renormalize .` after `gemba init` adds `.gitattributes` to an existing repo, WSL as an alternative) and the `.gitattributes` among what `init` writes; verify every command shown runs as written.
- [ ] 9.4 In `SECURITY.md`, qualify the "Running other programs" row for a `.cmd` or `.bat` IDE command, which Windows runs through `cmd.exe` with the harness path as its only argument, and add the change to the Unreleased section of `CHANGELOG.md`; verify both files read correctly and the changelog section names the new platform.

## 10. Integration

- [ ] 10.1 Run `uv run ruff format .`, `uv run ruff check .`, `uv run pyright` and `uv run python -m unittest discover -s tests`, then `GEMBA_CHANGE=windows-support uv run python -m unittest discover -s tests -p test_scenarios.py`; verify all pass with no case or exemption missing.

## Workflow follow-up

- Open the pull request and read the first Windows run of the suite: it answers the open question of design.md on `os.readlink` and confirms the 8.3 short-name assumption.
- Archive the change after the review, with `openspec archive`, which syncs the nine specs.
