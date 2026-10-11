# Spec Delta

## MODIFIED Requirements

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
