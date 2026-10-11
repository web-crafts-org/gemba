# Contributing to Gemba

Thank you for taking the time. Ideas, feedback and bug reports are as welcome as code.

## Ideas and feedback

- **Something is broken or surprising:** open an
  [issue](https://github.com/web-crafts-org/gemba/issues) with what you ran, what you
  expected and what happened. The output of the command, and the `gemba.yaml` with
  anything private removed, are the two things that make a report actionable.
- **An idea or a question:** start a
  [discussion](https://github.com/web-crafts-org/gemba/discussions). Gemba is built
  from real use, so what you do with it, and where it gets in your way, is the most
  useful thing you can tell us.

## How the product is developed

Every change to Gemba is one [OpenSpec](https://github.com/Fission-AI/OpenSpec)
change under `openspec/changes/`: a proposal, a delta of the specs under
`openspec/specs/`, a design and a task list, archived when it lands. The specs are the
contract of what the CLI does; the black-box cases under `tests/cases/` are their
executable form, one case per scenario, run against the real command. Read `AGENTS.md`
for the vocabulary, the principles and the development commands; it is written for
agents and people alike, and `CLAUDE.md` is a link to it.

A contribution of code follows that shape:

1. Open an issue or a discussion first for anything beyond a small fix, so that the
   scope is agreed before the work.
2. Create the change with `openspec new change <name>`, or with the OpenSpec skills of
   your agent, which run the same commands; write the case of each scenario before the
   code that makes it pass, and never edit a case to make it pass.
3. Keep the three piles apart: built-in behaviour in `src/gemba/` and the skills,
   customization in `gemba.yaml`, data in the tasks repo. No module and no skill holds
   a value of one organization.
4. Run the gates below before opening the pull request, and describe in it what the
   change does and which scenarios it adds or modifies.

## Quality gates

```bash
uv sync                                     # once: environment and editable install
uv run pre-commit install --hook-type pre-commit --hook-type pre-push   # once
uv run ruff format .                        # formatter
uv run ruff check .                         # linter
uv run pyright                              # type checker
uv run python -m unittest discover -s tests # black-box cases, unit tests, traceability
uv build                                    # the package builds
```

The hooks run the formatter, the linter and the type checker on every commit and the
suite on every push; the CI workflow runs the same on every push and pull request. A
pull request is merged when the workflow is green and the review is done.

## Releasing (maintainers)

1. Set the new version in `pyproject.toml` and move the `Unreleased` entries of
   `CHANGELOG.md` into a section named after it, with the date. That section becomes
   the notes of the release page, and a version without one is refused.
2. Commit as `Release <version>` and tag it `v<version>`.
3. Push the tag. The release workflow checks that the tag names the declared version
   and that the changelog holds it, builds the distributions, publishes them to
   TestPyPI and then to PyPI through trusted publishing, and creates the GitHub
   Release with the notes of that section. Nothing else publishes.
4. Check `uv tool install gemba-cli==<version>` from a clean folder.
