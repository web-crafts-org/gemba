# Security policy

## Reporting a vulnerability

Report privately through
[GitHub's private vulnerability reporting](https://github.com/web-crafts-org/gemba/security/advisories/new).
Please do not open a public issue for a suspected vulnerability.

Include what you can: the version (`gemba --version`), the steps that reproduce the
problem, the `gemba.yaml` with anything private removed, and the impact you believe it
has. You will get an acknowledgement within a week, and a fix or a decision within 30
days. Valid reports are credited in the advisory unless you would rather stay anonymous.

## Supported versions

Fixes ship in the latest release of `gemba-cli` on
[PyPI](https://pypi.org/project/gemba-cli/). Older versions are not patched; upgrade to
pick up a fix.

## Threat model

Gemba is a local command-line tool. It has no server, no network listener, no daemon,
no telemetry and no self-update, and it reads no environment variable. It reads and
writes Markdown and YAML under the tasks repo and the harnesses, with your own user
permissions. It runs `git` on the repositories under the `repos_dir` of `gemba.yaml`,
and starts the `ide` command of `gemba.yaml` on a harness. Its one network operation
is a `git fetch` of `origin` during `gemba worktree add`, with the credentials git
already holds; it never pushes and never clones.

That shapes what is and is not a vulnerability here:

| In scope | Out of scope |
| --- | --- |
| Code execution triggered by parsing a task file, `gemba.yaml`, `harness.yaml` or a note | What the `ide` command of your `gemba.yaml` does: you wrote it |
| Writing or deleting outside the tasks repo, the harnesses and the worktrees of a run, through a ref, a slug, a workstream, a config value or a file name | Reading or writing a path you passed to the CLI yourself |
| Deleting a harness or a worktree that holds uncommitted changes or commits on no remote branch, without `--force` | What an agent does inside a harness: gemba creates the harness, it does not run the agent |
| A push, or any network access beyond the one fetch | Vulnerabilities in development dependencies that do not ship in the published package |
| Running any program other than `git` and the configured `ide` command | Denial of service against your own machine using your own input |

If you think something sits on the boundary, report it and we will work it out together.

## What the CLI does on your machine

| Surface | Behavior |
| --- | --- |
| Install scripts | `gemba-cli` is a pure Python wheel built with hatchling and no build hooks, so installing it from PyPI runs no code from Gemba. |
| Running other programs | `git` is run with an argument array (`git -C <folder> ...`), never through a shell. The `ide` command is split into an argument array with `shlex`, the harness folder is appended as its last argument, and it is started detached, with no shell and no inherited standard streams. Nothing from a task file, a note or a command-line value is interpolated into a command. |
| Parsing | Every YAML document is read with `yaml.safe_load`. Refs, slugs, workstream identifiers, prefixes, dates and filed names are validated against fixed patterns before any of them becomes part of a path. |
| Deleting | `gemba harness remove` and `gemba worktree remove` show what they would delete and delete nothing without `--yes`. They refuse while a worktree holds uncommitted changes or commits on no remote branch, or a branch of the run left without a worktree holds such commits. `--force` on `harness remove` discards that work; it never removes a harness the working directory is inside of, nor one whose repository state cannot be read. |
| Network | One `git fetch --prune origin` during `gemba worktree add`, so that the worktree starts from the current remote branch. It uses git's own configuration and credentials, and is told not to move the recorded default branch. |
| Telemetry | None. |

## Published package contents

The wheel holds the `gemba` package: the code and its assets, the skills, the harness
guide and the files `gemba init` writes. The source distribution adds the tests, the README, the changelog, the
license, `pyproject.toml` and `uv.lock`. The one runtime dependency is PyYAML.

ruff, pyright and pre-commit, with everything they pull in, are development
dependencies and are not published. A scanner that reads `uv.lock` without separating
dependency groups will report advisories for packages that never reach an installed
copy of Gemba. You do not have to take that on trust:

```sh
pip install gemba-cli
pip show gemba-cli   # Requires: pyyaml
```

## Automated checks

| Tool | Covers |
| --- | --- |
| [CodeQL](https://github.com/web-crafts-org/gemba/security/code-scanning) | Static analysis of the Python code and the workflows on every push and pull request to `main` |
| [Dependabot](https://github.com/web-crafts-org/gemba/security/dependabot) | Dependency advisories, plus weekly grouped update pull requests for the lock file and the CI actions |
| Release quarantine | uv resolves no release younger than 30 days (`exclude-newer` in `pyproject.toml`), and Dependabot's cooldown matches it. Dependabot security updates are off because they ignore that cooldown and cannot resolve; a patched release is picked up by the weekly update once it leaves the quarantine, or earlier by a deliberate `exclude-newer-package` exception |
| Secret scanning | Enabled on the repository, including push protection |
| Pinned actions | Every GitHub Action runs from a commit SHA, so a moved tag cannot change what CI executes |
| Workflow permissions | Both workflows are read-only by default; the release jobs that publish or create the release grant themselves the one permission they need |
| Trusted publishing | Releases reach TestPyPI and PyPI through OpenID Connect; no PyPI token is stored |

Alerts are triaged against the threat model above, so a finding in a development
dependency is fixed on the normal update cadence rather than treated as an incident.
