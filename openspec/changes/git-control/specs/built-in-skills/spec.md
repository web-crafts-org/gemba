# Spec Delta

## MODIFIED Requirements

### Requirement: Skills are assets of the package
Every skill SHALL ship in the gemba CLI package, in a registry that gives each its
scope: the obeya (`gemba-create`, `gemba-list`, `gemba-report`, `gemba-archive`,
`gemba-sync`, `gemba-init`, `gemba-config`, `gemba-migrate`), a harness
(`gemba-worktree`), or both (`gemba-harness`, `gemba-record`, `gemba-mark`,
`gemba-set`). `gemba skills update` and `gemba init` SHALL write exactly the registered
skills whose scope includes their target, and nothing else under a provider's skills
folder.

#### Scenario: Every registered skill is written
- **WHEN** `gemba skills update` runs in an obeya that declares one provider and has no skills folder
- **THEN** one `SKILL.md` per registered skill whose scope includes the obeya appears under that provider's skills folder, each in a folder named after the skill, `gemba-record`, `gemba-init`, `gemba-config`, `gemba-migrate` and `gemba-sync` included, and the command exits 0
- **Cases**: modifies `tests/cases/skills/every-registered-skill-is-written.yaml` (its first document expects `gemba-sync` too)

#### Scenario: Unregistered skills are not touched
- **WHEN** the provider's skills folder already holds a skill that is not registered, such as one of another tool
- **THEN** `gemba skills update` leaves that skill byte for byte as it was and does not mention it
- **Cases**: modifies `tests/cases/skills/unregistered-skills-are-not-touched.yaml` (its output lists `gemba-sync`)

#### Scenario: Harness-scoped skills only
- **WHEN** `gemba skills update` targets a harness
- **THEN** only the skills whose scope includes the harness are written or reported, `gemba-harness`, `gemba-record`, `gemba-mark`, `gemba-set` and `gemba-worktree` at this change, and no `gemba-create`, `gemba-list`, `gemba-report`, `gemba-archive`, `gemba-sync`, `gemba-init`, `gemba-config` or `gemba-migrate` folder is created there
- **Cases**: modifies `tests/cases/skills/harness-scoped-skills-only.yaml` (it expects no `gemba-sync` folder in the harness)

### Requirement: Update writes what is missing or outdated
For each registered skill and provider, `gemba skills update` SHALL write a missing
skill, rewrite an outdated one (it differs from what the package writes and its
`contentHash` matches its own content) and keep an unchanged one (identical to what
the package writes, `generatedBy` aside). It SHALL print one line per skill and
provider with its action, `written`, `updated`, `kept` or `overwritten`, and its path
relative to the obeya root. A second run SHALL leave the tree as the first left it.

#### Scenario: Missing skill is written
- **WHEN** a registered skill has no file under a declared provider
- **THEN** the file is written and the output reports `written` with its path
- **Cases**: keeps `tests/cases/skills/missing-skill-is-written.yaml`

#### Scenario: Unchanged skill is left alone
- **WHEN** `gemba skills update` runs a second time with nothing changed in between
- **THEN** the tree is identical to the one after the first run and every skill is reported as `kept`
- **Cases**: modifies `tests/cases/skills/unchanged-skill-is-left-alone.yaml` (its output lists `gemba-sync`)

#### Scenario: Outdated skill is refreshed
- **WHEN** a skill on disk differs from what the current package writes and its `contentHash` matches its own content
- **THEN** the file is rewritten with the current content and the output reports `updated`
- **Cases**: keeps `tests/cases/skills/outdated-skill-is-refreshed.yaml`

### Requirement: Check mode reports without writing
`gemba skills update --check` SHALL classify every skill as above, print one line per
skill and provider with its state (`missing`, `unchanged`, `outdated`, `edited`) and
its path, write nothing, and exit 0 when every skill is unchanged and 1 otherwise.

#### Scenario: Check finds everything current
- **WHEN** `--check` runs after an update with nothing changed in between
- **THEN** every skill is reported as `unchanged`, the tree is untouched and the exit code is 0
- **Cases**: modifies `tests/cases/skills/check-finds-everything-current.yaml` (its output lists `gemba-sync`)

#### Scenario: Check finds work to do
- **WHEN** `--check` runs with one skill missing and one edited
- **THEN** both are reported with their state, the tree is untouched and the exit code is 1
- **Cases**: modifies `tests/cases/skills/check-finds-work-to-do.yaml` (its output lists `gemba-sync`)
