# Security policy

## Supported versions

Only the latest release of the gemba CLI on [PyPI](https://pypi.org/project/gemba-cli/)
receives security fixes. A fix ships as a new release; nothing is backported.

## Reporting a vulnerability

Do not open a public issue for a vulnerability. Report it privately through
[GitHub's private vulnerability reporting](https://github.com/web-crafts-org/gemba/security/advisories/new),
so that a fix can be released before the details are public.

Include what you ran, the version of gemba (`gemba --version`), the `gemba.yaml` with
anything private removed, and the steps that reproduce the problem. If the report
involves a task file, a harness or a worktree, say what the agent was allowed to do.

You will get an acknowledgement within a week. Once the report is confirmed, the fix,
the release and the security advisory that credits you are coordinated with you.

## Scope

Gemba writes files inside the tasks repo and the harnesses, runs `git` on the
repositories under the configured `repos_dir`, and opens the harness in the configured
IDE. Anything that lets a task file, a config or an agent make it do more than that is
in scope: writing outside those folders, running a command that is not declared in
`gemba.yaml`, or pushing a branch of a run under its own name.
