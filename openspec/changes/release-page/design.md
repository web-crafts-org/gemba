# Design

## Context

See proposal.md. The release workflow has four jobs in sequence, `check`, `build`,
`testpypi` and `pypi`; `check` already fails the run before anything is built when the
tag does not name the declared version. `CHANGELOG.md` follows Keep a Changelog, so the
section of a version starts at `## [<version>]` and ends at the next `## [` heading
or at the reference links at the end of the file.

## Goals / Non-Goals

**Goals:**
- Every tag that publishes also creates its release page, with no manual step.
- A tag whose version has no changelog entry fails before anything is published.

**Non-Goals:**
- Generating notes from commits or pull requests: the changelog is written by hand
  and is the one source of the notes.
- Attaching the distributions to the release page: PyPI holds them.

## Decisions

### The section is extracted in `check`, not in the last job
`check` extracts the section with one `awk` over `CHANGELOG.md` into `notes.md`,
fails when the result is empty, and uploads it as the `release-notes` artifact. A
missing entry is then found before the build, next to the version mismatch it
resembles. Alternative, extracting it in the job that creates the page: rejected,
the package would already be on PyPI when the run fails.

### One more job, after `pypi`
`github` needs `pypi`, downloads the notes, and runs `gh release create v<version>
--title "Gemba <version>" --notes-file notes.md --verify-tag` with the run's own
token and `permissions: contents: write`. The page is created last so that a page
never announces a version the index does not have. Alternative, a third-party
release action: rejected, `gh` is on every runner and needs nothing to pin.

### Documents
`README.md` gains one sentence in "Status" linking `CHANGELOG.md` and the Releases
page. `CONTRIBUTING.md` says in step 1 that the section is what the release page
shows, and in step 3 that the workflow creates the page. `CHANGELOG.md` records the
change under `Unreleased`.

## Risks / Trade-offs

- [The new job cannot run before the next tag] → the extraction is run locally on
  the current changelog for `0.1.0` and for a version that has no section; the
  `gh release create` line is the one used by hand for `v0.1.0`.
- [A changelog edited in a different shape breaks the extraction] → the shape is
  the Keep a Changelog one the file already declares, and a broken extraction fails
  the run before anything is published.
