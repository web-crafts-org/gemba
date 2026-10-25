# Spec Delta

## MODIFIED Requirements

### Requirement: Skills are assets of the package
Every skill of Gemba SHALL ship inside the gemba CLI package, and the package SHALL
hold a registry naming each built-in skill with its scope: the tasks repo, a harness,
or both. `gemba skills update` SHALL write exactly the registered skills whose scope
includes its target and SHALL NOT create, modify or delete any other folder or file
under a provider's skills folder, so that skills of other tools that share the folder
are left as they are. At this change `gemba-create`, `gemba-list`, `gemba-report`,
`gemba-archive`, `gemba-init`, `gemba-config` and `gemba-migrate` belong to the tasks
repo, `gemba-worktree` to the harness, and `gemba-harness`, `gemba-record`,
`gemba-mark` and `gemba-set` to both. `gemba init` SHALL write the tasks-repo skills through the same
registry, so a skill added to it reaches a new tasks repo with no other change.

#### Scenario: Every registered skill is written
- **WHEN** `gemba skills update` runs in a tasks repo that declares one provider and has no skills folder
- **THEN** one `SKILL.md` per registered skill whose scope includes the tasks repo appears under that provider's skills folder, each in a folder named after the skill, `gemba-record`, `gemba-init`, `gemba-config` and `gemba-migrate` included, and the command exits 0
- **Cases**: modifies `tests/cases/skills/every-registered-skill-is-written.yaml` (its first document expects `gemba-migrate` too)

#### Scenario: Unregistered skills are not touched
- **WHEN** the provider's skills folder already holds a skill that is not registered, such as one of another tool
- **THEN** `gemba skills update` leaves that skill byte for byte as it was and does not mention it
- **Cases**: modifies `tests/cases/skills/unregistered-skills-are-not-touched.yaml` (its output lists `gemba-migrate`)

#### Scenario: Harness-scoped skills only
- **WHEN** `gemba skills update` targets a harness
- **THEN** only the skills whose scope includes the harness are written or reported, `gemba-harness`, `gemba-record`, `gemba-mark`, `gemba-set` and `gemba-worktree` at this change, and no `gemba-create`, `gemba-list`, `gemba-report`, `gemba-archive`, `gemba-init`, `gemba-config` or `gemba-migrate` folder is created there
- **Cases**: modifies `tests/cases/skills/harness-scoped-skills-only.yaml` (it expects no `gemba-migrate` folder in the harness)

### Requirement: Update is idempotent and respects hand edits
For each registered skill and each declared provider, `gemba skills update` SHALL
classify the file on disk as one of: **missing** (no file); **unchanged** (identical
to what the current package writes, ignoring `generatedBy`); **outdated** (different
from what the current package writes, while its `contentHash` matches its own
content, so it is an untouched older generation); **edited** (its `contentHash` is
absent or does not match its own content). The command SHALL write a missing skill,
rewrite an outdated one, leave an unchanged one as it is, and leave an edited one as
it is unless `--force` is passed, in which case it SHALL overwrite it. The command
SHALL print one line per skill and provider stating the action taken (`written`,
`updated`, `kept`, `overwritten`) and the path relative to the tasks repo root, and
SHALL say on the `kept` line of an edited skill that `--force` overwrites it. Running
the command twice SHALL leave the tree identical after the second run.

#### Scenario: Missing skill is written
- **WHEN** a registered skill has no file under a declared provider
- **THEN** the file is written and the output reports `written` with its path
- **Cases**: keeps `tests/cases/skills/missing-skill-is-written.yaml`

#### Scenario: Unchanged skill is left alone
- **WHEN** `gemba skills update` runs a second time with nothing changed in between
- **THEN** the tree is identical to the one after the first run and every skill is reported as `kept`
- **Cases**: modifies `tests/cases/skills/unchanged-skill-is-left-alone.yaml` (its output lists `gemba-migrate`)

#### Scenario: Outdated skill is refreshed
- **WHEN** a skill on disk differs from what the current package writes and its `contentHash` matches its own content
- **THEN** the file is rewritten with the current content and the output reports `updated`
- **Cases**: keeps `tests/cases/skills/outdated-skill-is-refreshed.yaml`

#### Scenario: Edited skill is kept and reported
- **WHEN** a skill on disk has no `contentHash` or one that does not match its own content
- **THEN** the file is left byte for byte as it was, the output reports it as `kept` because it was edited by hand and says that `--force` overwrites it, and the command exits 0
- **Cases**: keeps `tests/cases/skills/edited-skill-is-kept-and-reported.yaml`

#### Scenario: Edited skill is overwritten on request
- **WHEN** `gemba skills update --force` runs with an edited skill on disk
- **THEN** the file is replaced with the current content and the output reports `overwritten`
- **Cases**: keeps `tests/cases/skills/edited-skill-is-overwritten-on-request.yaml`

### Requirement: Check mode reports without writing
`gemba skills update --check` SHALL classify every skill as above, print one line per
skill and provider with its state (`missing`, `unchanged`, `outdated`, `edited`) and
its path, write nothing, and exit 0 when every skill is unchanged and 1 otherwise.

#### Scenario: Check finds everything current
- **WHEN** `--check` runs after an update with nothing changed in between
- **THEN** every skill is reported as `unchanged`, the tree is untouched and the exit code is 0
- **Cases**: modifies `tests/cases/skills/check-finds-everything-current.yaml` (its output lists `gemba-migrate`)

#### Scenario: Check finds work to do
- **WHEN** `--check` runs with one skill missing and one edited
- **THEN** both are reported with their state, the tree is untouched and the exit code is 1
- **Cases**: modifies `tests/cases/skills/check-finds-work-to-do.yaml` (its output lists `gemba-migrate`)
