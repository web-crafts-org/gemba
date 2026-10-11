# Proposal

## Why

The first release left the Releases page of GitHub empty: the workflow publishes to
PyPI but creates no release page, so the notes of a version live only in
`CHANGELOG.md`, which GitHub does not link and the README does not mention. The
page of `v0.1.0` was created by hand on 2026-10-11; every next version should get
its page from the workflow, with the notes the changelog already holds.

## What Changes

- The release workflow extracts the section of `CHANGELOG.md` of the version being
  released before building, refuses the tag when the section is missing or empty,
  and, once the package is on PyPI, creates the GitHub Release `v<version>` with
  that section as its notes.
- The README links the changelog and the Releases page from its status section;
  `CONTRIBUTING.md` says the release procedure creates the page and that the
  changelog section is required; `CHANGELOG.md` records the change under
  `Unreleased`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `package-release`: the requirement "Release from a tag" gains the changelog check
  before building and the release page after publishing.

## Impact

- `.github/workflows/release.yml`, `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`,
  `tests/not-automated.yaml`. No code of the package changes.
- The workflow needs `contents: write` on the job that creates the page, granted by
  the token GitHub gives every run; no secret is added.
