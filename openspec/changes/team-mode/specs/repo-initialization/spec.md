# Spec Delta

## ADDED Requirements

### Requirement: A member configures a new clone
When the shared config declares a team and the clone has no `gemba.local.yaml`, the
agent following the `gemba-init` skill SHALL ask only which member the user is, the IDE
command and, for work with code, the repositories folder, write them into
`gemba.local.yaml`, verify it with `gemba config check`, and leave `gemba.yaml`
untouched.

#### Scenario: Member configures a new clone
- **WHEN** `ana` cloned an obeya whose team declares `manuel` and `ana`, ran `gemba init` in it, and asks the agent to configure gemba
- **THEN** the agent asks which member she is among `manuel` and `ana`, then her IDE command and her repositories folder, writes `me: ana` with them into `gemba.local.yaml`, verifies it with `gemba config check`, and leaves `gemba.yaml` as it was
- **Cases**: adds the entry `repo-initialization: Member configures a new clone` of `tests/not-automated.yaml`

#### Scenario: User not yet a member
- **WHEN** the user configuring a new clone is not among the members of the team
- **THEN** the agent says that the team first adds them to `team` in `gemba.yaml` through the `gemba-config` skill, and writes no `me`
- **Cases**: adds the entry `repo-initialization: User not yet a member` of `tests/not-automated.yaml`

## MODIFIED Requirements

### Requirement: The init skill configures a new obeya once
The `gemba-init` skill SHALL be the one process an agent follows to configure an obeya
that `gemba init` just created, and its description SHALL make an agent choose it when
the user asks to configure, set up or customize gemba for the first time. It SHALL be
used for that first configuration only, and for the personal config of a new clone of
an obeya with a team: any later edit follows the `gemba-config` skill.

#### Scenario: Guided configuration is used once
- **WHEN** the user asks to add a workstream or a field to an obeya already configured
- **THEN** the agent follows the `gemba-config` skill, not the guided configuration
- **Cases**: keeps the entry `repo-initialization: Guided configuration is used once` of `tests/not-automated.yaml`

### Requirement: The questions of the guided configuration
Following the `gemba-init` skill, the agent SHALL ask one question at a time, in this
order, skipping what the user already said: what this obeya holds, after saying what
an obeya is, to propose its `obeya` name; whether a team shares it, then its members
and who the user is; the kinds of work, to propose workstreams; the default
workstream; what to record per task, to propose typed fields; the agent providers; the
IDE command; and the repositories folder, only for work with code.

#### Scenario: Obeya explained before its name
- **WHEN** the agent asks its first question of the guided configuration
- **THEN** it says what an obeya is, the room where one part of the person's work is kept in sight, drawn as they choose, such as the organization they work for, a project, a team inside a company or a whole company, asks what this one holds, and proposes the `obeya` name from the answer as a kebab-case name
- **Cases**: keeps the entry `repo-initialization: Obeya explained before its name` of `tests/not-automated.yaml`

#### Scenario: Team asked after the obeya's name
- **WHEN** the user, asked after the obeya's name whether a team shares it, says that `ana` and they share it
- **THEN** the agent proposes for each member a kebab-case folder name and initials used by no other, asks which member the user is, and goes on to the kinds of work
- **Cases**: adds the entry `repo-initialization: Team asked after the obeya's name` of `tests/not-automated.yaml`

### Requirement: The guided configuration writes both files
The agent SHALL then write the answers through the `gemba-config` skill, the IDE
command, the repositories folder and, with a team, the member the user is into
`gemba.local.yaml`, which it creates, and every other answer into `gemba.yaml`; check
them and refresh the skills; and report the resulting config, saying that
`gemba.local.yaml` stays on this machine and that git ignores it, without committing.

#### Scenario: Agent configures a new obeya
- **WHEN** the user asks the agent to configure gemba in an obeya that holds the scaffolded config
- **THEN** the agent asks the questions in the order above, one per message, proposes the workstreams and the fields from the answers, writes the IDE command and the folder of the repositories into `gemba.local.yaml` and the rest into `gemba.yaml`, verifies both with `gemba config check`, refreshes the skills when the providers changed, and reports the config without committing
- **Cases**: keeps the entry `repo-initialization: Agent configures a new obeya` of `tests/not-automated.yaml`
