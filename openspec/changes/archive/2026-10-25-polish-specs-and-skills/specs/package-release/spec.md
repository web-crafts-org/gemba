# Spec Delta

## MODIFIED Requirements

### Requirement: Release from a tag
A tag `v<version>` pushed SHALL trigger the release, and nothing else SHALL publish.
The release SHALL refuse, publishing nothing, when `<version>` is not the version of
`pyproject.toml`, or `CHANGELOG.md` has no section for it or an empty one. Otherwise
it SHALL build both distributions once, publish them to TestPyPI and then, only on
success, to PyPI, by trusted publishing, no token stored, and create the GitHub
Release `v<version>`, titled with the version, with that section as notes.

#### Scenario: Tag matches the version
- **WHEN** `pyproject.toml` declares `0.1.0` and the tag `v0.1.0` is pushed
- **THEN** the release builds the package, publishes it to TestPyPI, then to PyPI, and `uv tool install gemba-cli==0.1.0` installs it
- **Cases**: keeps the entry `package-release: Tag matches the version` of `tests/not-automated.yaml`

#### Scenario: Tag does not match the version
- **WHEN** `pyproject.toml` declares `0.1.0` and the tag `v0.2.0` is pushed
- **THEN** the release fails before building, names both versions, and publishes nothing
- **Cases**: keeps the entry `package-release: Tag does not match the version` of `tests/not-automated.yaml`

#### Scenario: Changelog section missing
- **WHEN** the tag names the declared version and `CHANGELOG.md` has no `## [<version>]` section, or the section holds nothing
- **THEN** the release fails before building, says the changelog lacks the version, and publishes nothing
- **Cases**: keeps the entry `package-release: Changelog section missing` of `tests/not-automated.yaml`

#### Scenario: TestPyPI failure stops the release
- **WHEN** publishing to TestPyPI fails
- **THEN** nothing is published to PyPI
- **Cases**: keeps the entry `package-release: TestPyPI failure stops the release` of `tests/not-automated.yaml`

#### Scenario: Release page created
- **WHEN** the package of `<version>` was published to PyPI
- **THEN** the repository holds the GitHub Release `v<version>`, titled `Gemba <version>`, whose notes are the changelog section of that version, and the Releases page lists it
- **Cases**: keeps the entry `package-release: Release page created` of `tests/not-automated.yaml`

#### Scenario: Nothing else publishes
- **WHEN** a commit is pushed to `main` or a pull request is opened
- **THEN** no release runs and nothing is published
- **Cases**: keeps the entry `package-release: Nothing else publishes` of `tests/not-automated.yaml`

### Requirement: Checks on every change
Every push and every pull request SHALL run the formatter check, the linter, the type
checker and the full test suite, and report the result on the commit and the pull
request, as the hooks check a commit. The suite SHALL run on Linux on every supported
Python version, and on macOS and Windows on the oldest and the newest, with the git of
each runner at its defaults, so that both what differs by platform and what differs by
interpreter are covered.

#### Scenario: Pull request checked
- **WHEN** a pull request is opened or updated
- **THEN** the formatter check, the linter, the type checker and the suite run, and a failure of any of them marks the pull request as failing
- **Cases**: keeps the entry `package-release: Pull request checked` of `tests/not-automated.yaml`

#### Scenario: Push checked
- **WHEN** a commit is pushed to any branch
- **THEN** the same checks run and their result is shown on the commit
- **Cases**: keeps the entry `package-release: Push checked` of `tests/not-automated.yaml`

#### Scenario: Suite run per platform and interpreter
- **WHEN** the checks run
- **THEN** the suite runs on Linux for Python 3.11, 3.12, 3.13 and 3.14, and on macOS and on Windows for Python 3.11 and 3.14, each job with the runner's git unchanged
- **Cases**: keeps the entry `package-release: Suite run per platform and interpreter` of `tests/not-automated.yaml`
