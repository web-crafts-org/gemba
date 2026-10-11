# Design

## Context

See proposal.md for the motivation. What shapes the approach:

- The package lives under `cli/` and is built by hatchling, which refuses a `readme`
  or a `license-files` path outside the project folder (`Readme path must be within
  the project directory`, checked on 2026-10-09). The README and the license GitHub
  shows must be the ones the package ships, so the project folder must be the root.
- The suite runs the `gemba` executable found on PATH, the one of the project
  environment; `tests/test_scenarios.py` finds `openspec/` two levels above the tests
  folder, and the pre-commit hooks, the VS Code settings and `openspec/config.yaml`
  name `cli/`.
- The eleven skill assets repeat the same prerequisite paragraph; skills are stamped
  as they are, with no templating. The written copies of the skills live only in
  tasks repos, none in this repository.
- The version is already read from the installed package metadata by `gemba
  --version`, `harness launch` and the skill provenance; the cases check it through
  the `{version}` token.
- No continuous integration exists; quality is kept by the hooks of each clone.
- The `gemba` in daily use is an editable install of the tasks repo the package came
  from, not of this repository, so nothing here affects that use.

## Goals / Non-Goals

**Goals:**
- One layout that serves the package, GitHub and PyPI with one README and one license.
- A first release that a tag produces end to end, with no secret stored.
- Documents that a newcomer can read alone and that a change rarely touches.
- Every example value in the repository invented, with nothing to scrub later.

**Non-Goals:**
- Any change to what a command does, prints or writes.
- The decisions of the comparison with the first instance, including what the
  published CLI keeps or serves differently.
- Documentation beyond the README: a site or a manual is a later decision.
- Switching the tasks repo the package came from to the published package: its own
  change.
- A `gemba harness list`, a post-worktree hook, or refreshing the guide of a harness.

## Decisions

### The package folder is the root
`cli/pyproject.toml`, `cli/uv.lock`, `cli/src/` and `cli/tests/` move up with `git
mv`, so history follows. `tests/test_scenarios.py` finds `openspec/` as
`TESTS_DIR.parent / "openspec"`. The hooks run `uv run ruff`, `uv run pyright` and
`uv run python -m unittest discover -s tests`; the pyright hook exports `src`, `tests`
and `pyproject.toml` from the index. The VS Code settings point at `.venv`, `src` and
`tests`. `openspec/config.yaml` names `tests/cases` and `tests/not-automated.yaml`.
Alternative, keeping `cli/` and a second README and LICENSE inside it: rejected, two
copies to keep equal by hand on every release. Alternative, a symlink inside `cli/`:
rejected, it breaks on Windows checkouts and hatchling's handling of it is undefined.

### Invented names by one substitution
The organization becomes `nakatomi`, its branch prefix `nk`, the two example
repositories `nakatomi-web` and `nakatomi-api`, and the malformed examples of the
organization `Nakatomi Corp` and `naka--tomi`, applied once with the same
substitution to the cases, the unit tests, the `gemba-worktree` skill and the
documents; the delta specs already carry it. Nakatomi is a fictional company, obviously
so, and Japanese like the name of the product. `acme` is not used for the organization
because it already stands for the client in every example, and the two must stay
distinguishable. The main specs are not edited by hand: the archive of this change
syncs them, and the traceability test matches scenario titles, which do not change, so
cases and specs stay in step throughout.

### The prerequisite paragraph is edited in each skill
The eleven assets get the sentence `uv tool install gemba-cli`. A shared fragment
rendered into every skill would be a new mechanism for one sentence; instead a unit
test in `tests/test_skills.py` reads every registered asset and checks that it names
`uv tool install gemba-cli` and neither `./cli` nor an editable install. Owner: the
tests only; no module changes.

### Metadata in `pyproject.toml`, hatchling kept
`readme = "README.md"`, `license = "MIT"` and `license-files = ["LICENSE"]` in the
PEP 639 form, `authors`, `urls` (`Repository`, `Changelog`, `Issues`), `keywords`
and classifiers without a `License ::` entry, which PEP 639 deprecates. If the locked
hatchling rejects the PEP 639 fields, the table form `license = { file = "LICENSE" }`
is used instead; `uv build` and the `METADATA` of the wheel decide. `authors` and the
copyright line of `LICENSE` name Manuel Robles: the organization that owns the GitHub
repository is a personal brand with no legal form, so the copyright holder is the
person (decided at review on 2026-10-09). A unit test in
`tests/test_package.py` reads `pyproject.toml` with `tomllib` and checks the declared
keys, so a release never ships without them.

### One version, checked by the release
The version stays in `pyproject.toml` only. The release workflow compares the tag with
`uv version --short` and fails before building when they differ. `CHANGELOG.md`
follows Keep a Changelog: `Unreleased` on top, one section per version with its date.
Releasing is a documented procedure for maintainers in `CONTRIBUTING.md`: bump the
version, move `Unreleased` into the version with the date, commit, tag `v<version>`,
push the tag.

### Two workflows under `.github/workflows/`
`ci.yml` runs on every push and pull request: `uv sync`, `ruff format --check`,
`ruff check`, `pyright`, the suite on Python 3.11 and 3.13, and `uv build` as a smoke
check of the package. `release.yml` runs on tags `v*`: the version check, `uv build`
once with the distributions uploaded as an artifact, `uv publish` to TestPyPI in the
`testpypi` environment, then, only on success, `uv publish` to PyPI in the `pypi`
environment, each job with `id-token: write` and `--trusted-publishing always`. The
two environments are created in the repository settings, and the trusted publishers
are registered by a person on pypi.org and test.pypi.org as pending publishers before
the first tag. Alternative, a token in a secret: rejected, trusted publishing is the
recommended path and leaves nothing to rotate. Alternative, releasing from a local
machine with `uv publish`: rejected, not reproducible and needs a token.

### The documents
`README.md` is written for someone who arrives with no other documentation, in the
order agreed on 2026-10-09: what Gemba is and solves, the idea in one diagram, install
and start in five minutes, the cycle of a task with the command under each step, the
config, contributing, license; the current manual survives inside the cycle, cut
down, and the examples use `nakatomi` for the organization and `acme` for the client.
`AGENTS.md`, written for every agent, with `CLAUDE.md` as a symbolic link to it,
keeps only what no change touches: what the repository is, the vocabulary,
the development commands, the principles, how a process is named and how a process, a
skill or an agent provider is added, the OpenSpec workflow and the quality gates;
about 120 lines. The per-module paragraphs leave, since every module has a docstring
and the specs hold the rules. `CONTRIBUTING.md` holds the flow of a contribution,
ideas and feedback through issues and discussions, the OpenSpec workflow and the
gates, and the release procedure.

### Hygiene
`.gitignore` keeps `__pycache__/` and `.venv/`, drops `harnesses/` and adds `dist/`
and `.ruff_cache/`. `.pre-commit-config.yaml` drops `exclude: ^tasks/`. The hooks are
installed in the clone as part of the change.

## Risks / Trade-offs

- [The release workflow cannot run before a tag exists] → the version check, the
  build and the publish command are the same `uv` commands run locally in the final
  task; the TestPyPI job runs before the PyPI one; the first tag may be a pre-release
  such as `v0.1.0rc1`, with the version bumped to match, to exercise the pipeline
  without spending `0.1.0`.
- [A trusted publisher not registered before the first tag] → the publish job fails
  with a permission error and nothing is published; registering and re-running the
  job is enough, no tag needs to move.
- [The locked hatchling may not accept the PEP 639 fields] → decided by `uv build`
  in the metadata task, with the table form as the fallback.
- [The rename touches 31 cases and 4 test modules] → one substitution applied
  mechanically, then a grep that finds no old name and the suite green.
- [The README and AGENTS.md are judged by their reader] → the author reviews both
  before the change is archived; the repository is private until then.
- [Moving files hides them from a reader of the old layout] → `git log --follow`
  keeps every file's history across the move.

## Migration Plan

No user has installed the package yet, so there is nothing to migrate. The tasks repo
the package came from keeps its editable install of its own `cli/` until the first
release, then switches in a change of its own, planned in that repository.

## Open Questions

- Whether the suite in `ci.yml` should also cover Python 3.12, between the two ends
  tested.
