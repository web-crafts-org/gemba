# Spec Delta

## MODIFIED Requirements

### Requirement: Distribution metadata
The package SHALL be built from `pyproject.toml` at the root of the repository with
the distribution name `gemba-cli` and the command `gemba`, the repository's
`README.md` as its long description, the MIT license with the repository's `LICENSE`
file, authors, the URLs of the repository, the changelog and the issues, keywords and
classifiers that name the three supported platforms, POSIX, macOS and Microsoft
Windows, and SHALL require Python 3.11 or later.

#### Scenario: Metadata declared
- **WHEN** `pyproject.toml` is read
- **THEN** it declares `gemba-cli`, the `gemba` script, `readme`, `license` MIT with `license-files`, `authors`, `urls` with the repository, the changelog and the issues, `classifiers` naming POSIX, macOS and Microsoft Windows, and `requires-python` of 3.11 or later
- **Cases**: keeps the entry `package-release: Metadata declared` of `tests/not-automated.yaml` (the unit test over `pyproject.toml` in `tests/test_package.py` gains the three platform classifiers)

#### Scenario: Package built
- **WHEN** `uv build` runs at the root of the repository
- **THEN** it writes a wheel and a source distribution under `dist/` whose metadata carry the name, the version, the license and the readme
- **Cases**: keeps the entry `package-release: Package built` of `tests/not-automated.yaml`

#### Scenario: Installed from the index
- **WHEN** `uv tool install gemba-cli` runs on a machine with Python 3.11 or later
- **THEN** `gemba --version` prints the version installed and every subcommand is available
- **Cases**: keeps the entry `package-release: Installed from the index` of `tests/not-automated.yaml`

### Requirement: Checks on every change
Every push and every pull request SHALL run the formatter check, the linter, the type
checker and the full test suite, and SHALL report the result on the commit and on the
pull request, so that a contribution is checked the same way the hooks check a commit.
The suite SHALL run on Linux on every supported Python version, and on macOS and on
Windows on the oldest and the newest supported Python versions, with the git of each
runner at its defaults, so that what differs by platform and what differs by
interpreter are both covered.

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
- **Cases**: adds the entry `package-release: Suite run per platform and interpreter` to `tests/not-automated.yaml` (the subject is the CI workflow under `.github/workflows`, run by GitHub Actions)
