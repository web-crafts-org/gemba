# Proposal

## Why

The gemba CLI was extracted from the tasks repo of its first organization into this
repository on 2026-10-09 so that it can be published as an open-source package, `gemba-cli` on PyPI,
and grow with ideas and feedback from people outside that organization. The repository still
reads as a tasks repo: the package lives under `cli/`, the README and `CLAUDE.md`
describe `gemba.yaml` and `tasks/` as if they were here, the skills tell the agent to
install from `./cli`, the specs and the cases use the names of a real organization and
of a real client as examples, and nothing declares a license, package metadata or a
way to release. This change makes the repository ready to be made public and to
publish its first version.

## What Changes

- **Package layout.** `cli/` is flattened to the root of the repository:
  `pyproject.toml`, `uv.lock`, `src/gemba/` and `tests/` move up one level. Hatchling
  only reads a readme and a license file inside the project folder, so the README and
  the license that GitHub shows must be the ones the package ships. Every command loses
  `--project cli`; the hooks, the VS Code settings, `openspec/config.yaml` and the
  traceability test follow.
- **Package metadata and license.** `pyproject.toml` declares `readme`, `license`
  (MIT) with its file, `authors`, `urls`, `keywords` and classifiers; `LICENSE` is
  added at the root. The distribution stays `gemba-cli` and the command `gemba`.
- **Release process.** A `package-release` capability: the version is declared once in
  `pyproject.toml` and printed by `gemba --version`; a tag `v<version>` on `main`
  builds the package and publishes it to TestPyPI and then to PyPI through trusted
  publishing, refusing a tag that does not match the declared version. A continuous
  integration workflow runs the formatter check, the linter, the type checker and the
  suite on every push and pull request, and `CHANGELOG.md` records each version.
- **Skills name the published package.** The installation prerequisite of the eleven
  skills changes from `uv tool install -e ./cli` to `uv tool install gemba-cli`.
- **Invented example names.** The real organization, its branch prefix and its two
  example repositories become `nakatomi`, `nk`, `nakatomi-web` and `nakatomi-api` in
  the specs, the cases, the unit tests, the `gemba-worktree` skill and the documents.
  No behaviour changes; the delta specs carry the requirements whose scenarios name
  the values, so that specs and cases move together. The malformed examples of
  `organization` follow (`Nakatomi Corp`, `naka--tomi`).
- **Documents for the public.** `README.md` is rewritten for someone who arrives with
  no other documentation: what Gemba is and solves, the idea in one diagram, install
  and start in five minutes, the cycle of a task with the command under each step, the
  config, contributing, license. `AGENTS.md`, with `CLAUDE.md` as a link to it, is cut
  to what does not change with a change: what the repository is, the vocabulary, the development commands, the
  principles, how a process is named and added, the OpenSpec workflow and the quality
  gates; the per-module paragraphs leave, since each module has a docstring and the
  specs hold the rules. `CONTRIBUTING.md` says how the product is developed and where
  ideas and feedback go.
- **Repository hygiene.** `.pre-commit-config.yaml` drops the `tasks/` exclusion,
  `.gitignore` drops `harnesses/` and ignores `dist/`, and the hooks are installed in
  the clone.

Nothing the CLI does changes: every case keeps its scenario and its expected output,
the example values aside.

## Capabilities

### New Capabilities
- `package-release`: how the package declares its identity and version, and how a
  version is built and published.

### Modified Capabilities
- `built-in-skills`: a new requirement that every skill names the published package
  as the way to install the command.
- `gemba-config`: the scenarios of the organization requirement use invented names.
- `harness-removal`: the scenarios that name repositories and the branch of the run
  use invented names.
- `harness-worktrees`: the scenarios that name repositories, the organization and the
  branch prefix use invented names.

## Impact

- Every path of the repository: the package, the tests, the hooks, the editor
  settings, the OpenSpec config and the three root documents. Git keeps the history of
  moved files.
- The eleven skill assets, and through them every written copy: the tasks repo the
  package came from refreshes its copies with `gemba skills update` when it switches to the
  published package, in a change of its own after the first release.
- New external pieces: GitHub Actions, the `pypi` and `testpypi` environments of the
  repository, and the trusted publisher registrations on pypi.org and test.pypi.org,
  which a person creates by hand once.
- No change to `gemba.yaml`, to the task file format or to any command's behaviour.
