# Tasks

## 1. The package folder is the root

- [x] 1.1 Move `cli/pyproject.toml`, `cli/uv.lock`, `cli/src/` and `cli/tests/` to the root with `git mv`, delete `cli/.venv` and the empty `cli/`, and verify `git log --follow -- src/gemba/cli.py` reaches "Initialize repository"
- [x] 1.2 Point `tests/test_scenarios.py` at `TESTS_DIR.parent / "openspec"`, run `uv sync` at the root and verify the full suite passes with `uv run python -m unittest discover -s tests`
- [x] 1.3 Rewrite `.pre-commit-config.yaml` for the root layout (`uv run` without `--project`, the pyright hook exporting `src`, `tests` and `pyproject.toml`, the suite from `tests`), drop `exclude: ^tasks/`, install the hooks with `uv run pre-commit install --hook-type pre-commit --hook-type pre-push` and verify `uv run pre-commit run --all-files` passes
- [x] 1.4 Point `.vscode/settings.json` at `.venv`, `src` and `tests`, name `tests/cases` and `tests/not-automated.yaml` in `openspec/config.yaml`, and verify `openspec validate prepare-publication` still passes
- [x] 1.5 Set `.gitignore` to `__pycache__/`, `.venv/`, `.ruff_cache/` and `dist/`, and verify `git status --short` shows no ignored folder as untracked

## 2. Invented example names

- [x] 2.1 Apply the substitution of design.md (the organization→`nakatomi`, its prefix→`nk`, its two repositories→`nakatomi-web` and `nakatomi-api`, the malformed examples→`Nakatomi Corp` and `naka--tomi`) to every file under `tests/cases/` and to `tests/test_cases.py`, `tests/test_config.py`, `tests/test_harness.py` and `tests/test_worktree.py`, and verify the suite passes and a grep for the old names finds nothing under `tests/`
- [x] 2.2 Replace the old example repository in `src/gemba/assets/skills/gemba-worktree/SKILL.md` with `nakatomi-web` and verify the `skills` cases pass

## 3. Skills name the published package

- [x] 3.1 Add to `tests/test_skills.py` a test that reads every asset of `SKILLS` and asserts it contains `uv tool install gemba-cli` and neither `./cli` nor `-e ` (scenario "built-in-skills: No development path in a skill"), and verify it fails
- [x] 3.2 Change the prerequisite paragraph of the eleven skill assets to `uv tool install gemba-cli`, and verify the new test and the `skills` and `harness` cases pass
- [x] 3.3 Add "built-in-skills: Command missing" to `tests/not-automated.yaml` (the agent follows the skill) and verify `test_scenarios` passes

## 4. Distribution metadata and license

- [x] 4.1 Add `tests/test_package.py` reading `pyproject.toml` with `tomllib` and asserting the name `gemba-cli`, the `gemba` script, `readme`, `license` MIT with `license-files`, `authors`, `urls` with `Repository`, `Changelog` and `Issues`, `classifiers` and `requires-python` `>=3.11` (scenario "package-release: Metadata declared"), and verify it fails
- [x] 4.2 Write `LICENSE` (MIT, copyright 2026 Manuel Robles) and the metadata of design.md in `pyproject.toml`, and verify the new test passes
- [x] 4.3 Run `uv build` and verify the wheel's `METADATA` carries the name, the version, `License-Expression: MIT`, the `LICENSE` file and the README as description; if hatchling rejects the PEP 639 fields, switch to `license = { file = "LICENSE" }` and repeat
- [x] 4.4 Add `tests/cases/release/version-printed.yaml` running `--version` with `stdout: "{version}\n"` (scenario "package-release: Version printed") and verify it passes
- [x] 4.5 Add to `tests/not-automated.yaml` the entries for "package-release: Package built" (the build step of the CI and release workflows), "package-release: Installed from the index" (needs the published index) and "package-release: Changelog carries the version" (a step of the release procedure), and verify `test_scenarios` passes

## 5. Workflows

- [x] 5.1 Write `.github/workflows/ci.yml` (push and pull request: `uv sync`, `ruff format --check`, `ruff check`, `pyright`, the suite on Python 3.11 and 3.13, `uv build`) and verify every command of it passes when run locally in the same order
- [x] 5.2 Write `.github/workflows/release.yml` (tags `v*`: version check against `uv version --short`, `uv build` with the distributions as an artifact, `uv publish` to TestPyPI in the `testpypi` environment with trusted publishing, then to PyPI in the `pypi` environment) and verify the version check passes locally for `v0.1.0` and fails for `v0.2.0`
- [x] 5.3 Create the `testpypi` and `pypi` environments of `web-crafts-org/gemba` with `gh api` and verify `gh api repos/web-crafts-org/gemba/environments` lists both
- [x] 5.4 Add to `tests/not-automated.yaml` the entries for "package-release: Tag matches the version", "Tag does not match the version", "TestPyPI failure stops the release", "Nothing else publishes", "Pull request checked" and "Push checked" (the subject is GitHub Actions), and verify `test_scenarios` passes

## 6. Changelog and contributing guide

- [x] 6.1 Write `CHANGELOG.md` in the Keep a Changelog format with an empty `Unreleased` section and `0.1.0` describing the first release, and verify the `Changelog` URL of `pyproject.toml` points at it
- [x] 6.2 Write `CONTRIBUTING.md`: ideas and feedback through issues and discussions, the OpenSpec workflow and the case-first rule, the quality gates and the hooks, the release procedure for maintainers (bump, changelog, commit, tag, push the tag), and verify every command it names runs as written

## 7. README and CLAUDE.md

- [x] 7.1 Rewrite `README.md` in the order of design.md (what Gemba is and solves, the idea in one diagram, install and start in five minutes, the cycle of a task, the config, contributing, license) with invented example names, and verify every command it names runs as written and a grep for the old names finds nothing in it
- [x] 7.2 Rewrite the agent guide as `AGENTS.md`, with `CLAUDE.md` a link to it, to what no change touches (what the repository is, the vocabulary, the development commands, the principles, how a process is named and how a process, a skill or a provider is added, the OpenSpec workflow and the quality gates), and verify it is about 120 lines and names no module paragraph, `cli/`, the old organization or `product/`

## 8. Final checks

- [x] 8.1 Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, the full suite with `uv run python -m unittest discover -s tests`, `uv build` and `openspec validate prepare-publication`, and verify all of them pass

## Workflow follow-up

- The author reviews `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, the `authors`
  entry and the copyright holder before the change is archived.
- Archive the change and sync the specs; verify the main specs name no real
  organization or client.
- Then the publication plan kept in the tasks repo the package came from continues: remove the
  archived changes of the MVP and `product/`, squash the history, make the repository
  public, register the trusted publishers on pypi.org and test.pypi.org, and push the
  first tag.
