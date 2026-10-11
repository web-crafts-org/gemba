# Tasks

## 1. The release page from the workflow

- [x] 1.1 Add to `tests/not-automated.yaml` the entries for "package-release: Changelog section missing" and "package-release: Release page created" (the subject is the release workflow), and verify `test_scenarios` passes with the delta applied
- [x] 1.2 In `.github/workflows/release.yml`, extract the changelog section of the declared version in the `check` job, fail when it is empty, upload it as the `release-notes` artifact, and add the `github` job after `pypi` that creates the release with `gh release create --verify-tag` and the notes; verify the file parses as YAML
- [x] 1.3 Run the extraction locally against `CHANGELOG.md` and verify it yields the `0.1.0` section and fails for a version with no section

## 2. Documents

- [x] 2.1 Add to the "Status" section of `README.md` one sentence linking `CHANGELOG.md` and the Releases page, and verify both links resolve
- [x] 2.2 Update the release procedure of `CONTRIBUTING.md` (the section is what the page shows; the workflow creates the page) and record the change under `Unreleased` in `CHANGELOG.md`; verify the changelog keeps its shape by running the extraction of 1.3 again

## 3. Final checks

- [x] 3.1 Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, the full suite and `openspec validate release-page`, and verify all pass
