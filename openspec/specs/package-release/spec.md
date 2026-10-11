# package-release Specification

## Purpose

The package declares its identity, license and version in one place, and a version is
built and published from a tag, so that anyone installs the command with one
`uv tool install gemba-cli` and a release is reproducible and needs no stored secret.

## Requirements

### Requirement: Distribution metadata
The package SHALL be built from `pyproject.toml` at the root of the repository with
the distribution name `gemba-cli` and the command `gemba`, the repository's
`README.md` as its long description, the MIT license with the repository's `LICENSE`
file, authors, the URLs of the repository, the changelog and the issues, keywords and
classifiers, and SHALL require Python 3.11 or later.

#### Scenario: Metadata declared
- **WHEN** `pyproject.toml` is read
- **THEN** it declares `gemba-cli`, the `gemba` script, `readme`, `license` MIT with `license-files`, `authors`, `urls` with the repository, the changelog and the issues, `classifiers`, and `requires-python` of 3.11 or later

#### Scenario: Package built
- **WHEN** `uv build` runs at the root of the repository
- **THEN** it writes a wheel and a source distribution under `dist/` whose metadata carry the name, the version, the license and the readme

#### Scenario: Installed from the index
- **WHEN** `uv tool install gemba-cli` runs on a machine with Python 3.11 or later
- **THEN** `gemba --version` prints the version installed and every subcommand is available

### Requirement: One version
The version SHALL be declared once, in `pyproject.toml`, and `gemba --version` SHALL
print exactly that value. `CHANGELOG.md` SHALL hold one section per released version,
newest first, each with its release date, under an `Unreleased` section that gathers
what the next version holds.

#### Scenario: Version printed
- **WHEN** `gemba --version` runs
- **THEN** it prints the version declared in `pyproject.toml` and exits 0

#### Scenario: Changelog carries the version
- **WHEN** a version is released
- **THEN** `CHANGELOG.md` holds a section with that version and its date, and the `Unreleased` section above it is empty

### Requirement: Release from a tag
A tag `v<version>` pushed to the repository SHALL trigger the release, and nothing else
SHALL publish. The release SHALL refuse, publishing nothing, when `<version>` is not
the version declared in `pyproject.toml` or when `CHANGELOG.md` has no section for
`<version>` or that section is empty. Otherwise it SHALL build the wheel and the
source distribution once, publish them to TestPyPI and, only when that succeeded, to
PyPI, both through trusted publishing, with no token stored in the repository, and
then create the GitHub Release `v<version>`, titled with the version, whose notes
are that section of the changelog.

#### Scenario: Tag matches the version
- **WHEN** `pyproject.toml` declares `0.1.0` and the tag `v0.1.0` is pushed
- **THEN** the release builds the package, publishes it to TestPyPI, then to PyPI, and `uv tool install gemba-cli==0.1.0` installs it

#### Scenario: Tag does not match the version
- **WHEN** `pyproject.toml` declares `0.1.0` and the tag `v0.2.0` is pushed
- **THEN** the release fails before building, names both versions, and publishes nothing

#### Scenario: Changelog section missing
- **WHEN** the tag names the declared version and `CHANGELOG.md` has no `## [<version>]` section, or the section holds nothing
- **THEN** the release fails before building, says the changelog lacks the version, and publishes nothing

#### Scenario: TestPyPI failure stops the release
- **WHEN** publishing to TestPyPI fails
- **THEN** nothing is published to PyPI

#### Scenario: Release page created
- **WHEN** the package of `<version>` was published to PyPI
- **THEN** the repository holds the GitHub Release `v<version>`, titled `Gemba <version>`, whose notes are the changelog section of that version, and the Releases page lists it

#### Scenario: Nothing else publishes
- **WHEN** a commit is pushed to `main` or a pull request is opened
- **THEN** no release runs and nothing is published

### Requirement: Checks on every change
Every push and every pull request SHALL run the formatter check, the linter, the type
checker and the full test suite, and SHALL report the result on the commit and on the
pull request, so that a contribution is checked the same way the hooks check a commit.

#### Scenario: Pull request checked
- **WHEN** a pull request is opened or updated
- **THEN** the formatter check, the linter, the type checker and the suite run, and a failure of any of them marks the pull request as failing

#### Scenario: Push checked
- **WHEN** a commit is pushed to any branch
- **THEN** the same checks run and their result is shown on the commit
