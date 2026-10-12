"""Black-box case runner: the executable specification of the gemba commands.

Every `cases/<process>/*.yaml` file covers one spec scenario and may hold several
YAML documents, one case each. A case uses this vocabulary:

- `name`: short case name, shown when the case fails.
- `scenario`: the spec scenario it covers, as `<capability>: <scenario title>`.
- `config`: content of `gemba.yaml`, as a map or as raw text; omitted means no config.
- `repos`: git repositories to build before `tree`, each name mapped to `branches`
  (each branch name mapped to its files, as `path: content`), `default` (the default
  branch of the remote, the first branch when omitted) and `unfetched` (branches
  mapped to files, as `branches`). For each name the runner creates the bare remote
  `remotes/<name>.git`, with one commit per branch, subject `add <branch>`, holding
  exactly the files declared for it and whose parent is the commit of the default
  branch; it clones it to `repos/<name>`, so `origin` is a file URL, `origin/HEAD` is
  the default branch and that branch is checked out; and it then pushes one commit per
  `unfetched` branch, subject `unfetched <branch>`, adding its files to the tip of the
  branch, so that the clone is behind its remote. A case declares `repos_dir: repos`.
- `tree`: files to create before running, as `path: content`.
- `run`: command name followed by its arguments; the name is resolved through COMMANDS.
- `cwd`: folder, relative to the root, to start the command from. When present,
  `--root` is not passed, so the command must discover the root by walking up.
- `setup`: commands, each written like `run`, run in order before the snapshot that
  `unchanged` compares with; each must exit 0.
- `tree_after_setup`: files to create like `tree`, after the `setup` commands and
  before the snapshot, so that a file can sit uncommitted in a harness that a `launch`
  in `setup` created and committed.
- `git_after_setup`: git commands run after `tree_after_setup` and before the
  snapshot, each written as the repository path, relative to the root, followed by the
  arguments of git; each must exit 0. `{root}` in an argument stands for the root.
- `exit`: expected exit code.
- `stdout`: the exact expected standard output.
- `stdout_contains`, `stderr_contains`: strings the output must contain.
- `stdout_json`: the document standard output must hold, written as YAML. Both sides
  are compared as parsed JSON, so indentation and key order do not matter while every
  key, value, type and list order does. Unquoted YAML dates stand for ISO strings.
- `files`: paths with their exact expected content.
- `files_contain`: paths with the strings each file must contain, for files whose
  full content the case should not embed. A path may be a glob, for files named after
  the clock, and must then match exactly one file.
- `absent`: paths that must not exist. A path may be a glob, which must match nothing,
  so `<folder>/*` checks that a folder is empty.
- `folders`: paths that must be folders.
- `links`: paths that must be symbolic links, each with its exact target.
- `git_log`: git repositories, each path relative to the root, with the subjects of
  their commits, newest first, as `git log --format=%s` prints them.
- `git_clean`: git repositories whose working tree must have nothing to commit and no
  untracked file, as `git status --porcelain` reports it.
- `git_branches`: git repositories, bare ones included, each with the exact list of
  its local branches in sorted order.
- `unchanged`: when true, the tree must be identical to the one before running.

The token `{today}` in `files`, `files_contain`, `absent`, `folders` and `links` paths
and contents, and in the expected output (`stdout_json` included), stands for the
current date, so a case can check the default date. The token `{version}`, in the same
places, stands for the version of the installed gemba CLI package.

Git must be on PATH: harness commands run it. Every command runs with the user's and
the system's git config ignored and a fixed identity, so commits never depend on the
machine running the suite. The IDE is never started: every command runs with a stub
for each name in STUBS first on PATH, which exits 0 and does nothing.
"""

import datetime
import importlib.metadata
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

CASES_DIR = Path(__file__).parent / "cases"

# A port of the CLI is done when every case passes with this table pointing at it.
COMMANDS = {
    "init": ["gemba", "init"],
    "create": ["gemba", "create"],
    "list": ["gemba", "list"],
    "skills": ["gemba", "skills"],
    "harness": ["gemba", "harness"],
    "record": ["gemba", "record"],
    "mark": ["gemba", "mark"],
    "archive": ["gemba", "archive"],
    "report": ["gemba", "report"],
    "set": ["gemba", "set"],
    "worktree": ["gemba", "worktree"],
    "config": ["gemba", "config"],
    # Not a subcommand: the option of the command itself, run with no subcommand.
    "--version": ["gemba", "--version"],
}
VERSION = importlib.metadata.version("gemba-cli")
GIT_ENVIRONMENT = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    # No background maintenance: a detached gc would rewrite .git/objects between the
    # snapshots of a case, under no control of the command under test.
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": "gc.auto",
    "GIT_CONFIG_VALUE_0": "0",
    "GIT_CONFIG_KEY_1": "maintenance.auto",
    "GIT_CONFIG_VALUE_1": "false",
    "GIT_AUTHOR_NAME": "Gemba Cases",
    "GIT_AUTHOR_EMAIL": "cases@gemba.invalid",
    "GIT_COMMITTER_NAME": "Gemba Cases",
    "GIT_COMMITTER_EMAIL": "cases@gemba.invalid",
}
GLOB_CHARACTERS = "*?["
# Executables the cases may name in a config, such as `ide: "code -n"`, replaced by stubs.
STUBS = ("code",)
_STUBS_DIR = tempfile.TemporaryDirectory(prefix="gemba-stubs-")
for _stub in STUBS:
    _path = Path(_STUBS_DIR.name) / _stub
    _path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    _path.chmod(0o755)


def load_cases():
    for path in sorted(CASES_DIR.rglob("*.yaml")):
        documents = [doc for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")) if doc]
        for index, case in enumerate(documents, start=1):
            suffix = f"_{index}" if len(documents) > 1 else ""
            test_name = f"test_{path.parent.name}_{path.stem}{suffix}".replace("-", "_")
            yield test_name, path.relative_to(CASES_DIR), case


def snapshot(root):
    """Every path under `root` mapped to its bytes, or None for folders."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


def expand(text):
    return str(text).replace("{today}", datetime.date.today().isoformat()).replace("{version}", VERSION)


def expand_json(expected):
    """The expected document serialized to JSON, `{today}` expanded, and parsed back."""
    return json.loads(expand(json.dumps(expected, default=lambda value: value.isoformat())))


def canonical(document):
    """One line per value with sorted keys, so a failed comparison shows a readable diff."""
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False)


def is_glob(relative):
    return any(character in relative for character in GLOB_CHARACTERS)


def environment():
    path = os.pathsep.join([_STUBS_DIR.name, os.environ.get("PATH", "")])
    return {**os.environ, **GIT_ENVIRONMENT, "PATH": path}


def write_tree(root, tree):
    """Create every file of `tree`, a map of path to content, under `root`."""
    for relative, content in (tree or {}).items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content or "", encoding="utf-8")


def git(root, relative, *args):
    """Run git in the repository at `relative` without writing to it, not even the index."""
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(root / expand(relative)), *args],
        env=environment(),
        capture_output=True,
        text=True,
        timeout=60,
    )


def branches(root, relative):
    """The local branches of the repository at `relative`, sorted, or None when git cannot read them."""
    result = git(root, relative, "branch", "--format=%(refname:short)")
    return sorted(result.stdout.splitlines()) if result.returncode == 0 else None


class CaseRunner(unittest.TestCase):
    """Builds the tree of a case, runs its command and checks the result; holds no test of its own."""

    maxDiff = None

    def run_case(self, source, case):
        label = f"[{case.get('name', source)}] ({source})"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, label)
            before = snapshot(root)
            result = self.execute(root, case, label, case["run"])
            self.check(root, case, label, before, result)

    def prepare(self, root, case, label):
        """Build the tree the command runs in: `config`, `repos`, `tree`, `cwd`, the `setup` commands,
        `tree_after_setup` and `git_after_setup`."""
        self.materialize(root, case, label)
        for run in case.get("setup") or []:
            prepared = self.execute(root, case, label, run)
            self.assertEqual(prepared.returncode, 0, f"{label} setup {run}\n{prepared.stdout}{prepared.stderr}")
        write_tree(root, case.get("tree_after_setup"))
        for relative, *args in case.get("git_after_setup") or []:
            args = [expand(arg).replace("{root}", str(root)) for arg in args]
            self.run_git(root / expand(relative), *args, label=f"{label} git_after_setup")

    def materialize(self, root, case, label):
        if "config" in case:
            config = case["config"]
            text = config if isinstance(config, str) else yaml.safe_dump(config, sort_keys=False)
            (root / "gemba.yaml").write_text(text, encoding="utf-8")
        for name, declaration in (case.get("repos") or {}).items():
            self.build_repository(root, name, declaration or {}, f"{label} repos {name}")
        write_tree(root, case.get("tree"))
        if "cwd" in case:
            (root / case["cwd"]).mkdir(parents=True, exist_ok=True)

    def build_repository(self, root, name, declaration, label):
        """The bare remote `remotes/<name>.git` and its clone `repos/<name>`, as `repos` describes them."""
        declared = declaration.get("branches") or {"main": {}}
        default = declaration.get("default") or next(iter(declared))
        self.assertIn(default, declared, f"{label}: default branch '{default}' is not declared")
        remote = root / "remotes" / f"{name}.git"
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp)
            self.run_git(scratch, "init", "--quiet", "--initial-branch", default, label=label)
            write_tree(scratch, declared[default])
            self.commit_all(scratch, f"add {default}", label)
            for branch, files in declared.items():
                if branch != default:
                    self.run_git(scratch, "checkout", "--quiet", "-b", branch, default, label=label)
                    self.run_git(scratch, "rm", "-r", "--quiet", "--ignore-unmatch", ".", label=label)
                    write_tree(scratch, files)
                    self.commit_all(scratch, f"add {branch}", label)
            remote.parent.mkdir(parents=True, exist_ok=True)
            self.run_git(root, "init", "--quiet", "--bare", "--initial-branch", default, str(remote), label=label)
            self.run_git(scratch, "push", "--quiet", str(remote), "refs/heads/*:refs/heads/*", label=label)
            clone = root / "repos" / name
            clone.parent.mkdir(parents=True, exist_ok=True)
            self.run_git(root, "clone", "--quiet", remote.as_uri(), str(clone), label=label)
            for branch, files in (declaration.get("unfetched") or {}).items():
                self.run_git(scratch, "checkout", "--quiet", branch, label=label)
                write_tree(scratch, files)
                self.commit_all(scratch, f"unfetched {branch}", label)
                self.run_git(scratch, "push", "--quiet", str(remote), branch, label=label)

    def commit_all(self, repository, subject, label):
        self.run_git(repository, "add", "-A", label=label)
        self.run_git(repository, "commit", "--quiet", "--allow-empty", "-m", subject, label=label)

    def run_git(self, cwd, *args, label):
        result = subprocess.run(
            ["git", "-C", str(cwd), *args], env=environment(), capture_output=True, text=True, timeout=60
        )
        self.assertEqual(result.returncode, 0, f"{label}: git {' '.join(args)}\n{result.stdout}{result.stderr}")
        return result

    def execute(self, root, case, label, run):
        name, *args = [str(arg) for arg in run]
        self.assertIn(name, COMMANDS, f"{label} run: unknown command name '{name}'")
        command = COMMANDS[name]
        executable = shutil.which(command[0])
        if executable is None:
            self.fail(f"{label} run: '{command[0]}' is not on PATH")
        if "cwd" in case:
            cwd = root / case["cwd"]
        else:
            cwd = root
            args += ["--root", str(root)]
        return subprocess.run(
            [executable, *command[1:], *args], cwd=cwd, env=environment(), capture_output=True, text=True, timeout=60
        )

    def check(self, root, case, label, before, result):
        output = f"\n--- stdout ---\n{result.stdout}--- stderr ---\n{result.stderr}"
        if "exit" in case:
            self.assertEqual(result.returncode, case["exit"], f"{label} exit{output}")
        if "stdout" in case:
            self.assertEqual(result.stdout, expand(case["stdout"]), f"{label} stdout{output}")
        for expected in case.get("stdout_contains") or []:
            self.assertIn(expand(expected), result.stdout, f"{label} stdout_contains{output}")
        for expected in case.get("stderr_contains") or []:
            self.assertIn(expand(expected), result.stderr, f"{label} stderr_contains{output}")
        if "stdout_json" in case:
            try:
                actual = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                self.fail(f"{label} stdout_json: standard output is not JSON: {exc}{output}")
            expected = expand_json(case["stdout_json"])
            self.assertEqual(canonical(actual), canonical(expected), f"{label} stdout_json")
        for relative, expected in (case.get("files") or {}).items():
            path = root / expand(relative)
            self.assertTrue(path.is_file(), f"{label} files: {expand(relative)} does not exist{output}")
            actual = path.read_text(encoding="utf-8")
            self.assertEqual(actual, expand(expected), f"{label} files: {expand(relative)}")
        for relative, fragments in (case.get("files_contain") or {}).items():
            relative = expand(relative)
            path = root / relative
            if is_glob(relative):
                matches = sorted(match.relative_to(root).as_posix() for match in root.glob(relative))
                self.assertEqual(len(matches), 1, f"{label} files_contain: {relative} matches {matches}{output}")
                path = root / matches[0]
            self.assertTrue(path.is_file(), f"{label} files_contain: {relative} does not exist{output}")
            actual = path.read_text(encoding="utf-8")
            for fragment in fragments:
                self.assertIn(expand(fragment), actual, f"{label} files_contain: {relative}")
        for relative in case.get("absent") or []:
            relative = expand(relative)
            if is_glob(relative):
                matches = sorted(match.relative_to(root).as_posix() for match in root.glob(relative))
                self.assertEqual(matches, [], f"{label} absent: {relative} matches")
            else:
                self.assertFalse((root / relative).exists(), f"{label} absent: {relative} exists")
        for relative in case.get("folders") or []:
            self.assertTrue((root / expand(relative)).is_dir(), f"{label} folders: {expand(relative)} is not a folder")
        for relative, target in (case.get("links") or {}).items():
            path = root / expand(relative)
            self.assertTrue(path.is_symlink(), f"{label} links: {expand(relative)} is not a symbolic link{output}")
            self.assertEqual(os.readlink(path), expand(target), f"{label} links: {expand(relative)}")
        for relative, subjects in (case.get("git_log") or {}).items():
            log = git(root, relative, "log", "--format=%s")
            self.assertEqual(log.returncode, 0, f"{label} git_log: {expand(relative)}\n{log.stderr}{output}")
            self.assertEqual(log.stdout.splitlines(), [expand(subject) for subject in subjects], f"{label} git_log")
        for relative in case.get("git_clean") or []:
            status = git(root, relative, "status", "--porcelain")
            self.assertEqual(status.returncode, 0, f"{label} git_clean: {expand(relative)}\n{status.stderr}{output}")
            self.assertEqual(status.stdout, "", f"{label} git_clean: {expand(relative)} has changes")
        for relative, expected in (case.get("git_branches") or {}).items():
            actual = branches(root, relative)
            self.assertIsNotNone(actual, f"{label} git_branches: {expand(relative)} is not readable{output}")
            self.assertEqual(actual, [expand(name) for name in expected], f"{label} git_branches: {expand(relative)}")
        if case.get("unchanged"):
            self.assertEqual(snapshot(root), before, f"{label} unchanged: the tree was modified{output}")


class CaseTest(CaseRunner):
    """One test per case document, added below from the files under CASES_DIR."""


class RunnerTest(CaseRunner):
    """The runner's own vocabulary, where no spec scenario covers it."""

    def test_tree_after_setup_is_not_committed_by_a_launch_in_setup(self):
        harness = "harnesses/support/2026-09-30-SUP-1-login-fails"
        case = {
            "config": {
                "default_workstream": "support",
                "agent_providers": ["claude"],
                "workstreams": {"support": {"prefix": "SUP", "description": "Investigate a problem"}},
            },
            "tree": {
                "tasks/support/2026-09-30-SUP-1-login-fails.md": (
                    "---\nstatus: open\nref: SUP-1\nupdated_at: 2026-09-30\nmetadata: {}\n---\n\n## Updates\n"
                ),
            },
            "setup": [["harness", "launch", "SUP-1", "--no-open"]],
            "tree_after_setup": {f"{harness}/notes/draft.md": "Not filed yet.\n"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "tree_after_setup")
            self.assertEqual((root / harness / "notes" / "draft.md").read_text(encoding="utf-8"), "Not filed yet.\n")
            status = git(root, harness, "status", "--porcelain")
            self.assertEqual(status.stdout, "?? notes/\n")
            log = git(root, harness, "log", "--format=%s")
            self.assertEqual(log.stdout.splitlines(), ["launch SUP-1"])

    def test_repos_are_clones_of_their_remote(self):
        case = {
            "repos": {
                "nakatomi-web": {
                    "branches": {"feature/a": {"a.txt": "a\n"}, "main": {"README.md": "main\n", "app.txt": "v1\n"}},
                    "default": "main",
                    "unfetched": {"main": {"new.txt": "new\n"}},
                },
                "group/other": {},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "repos")
            clone, remote = "repos/nakatomi-web", "remotes/nakatomi-web.git"
            url = git(root, clone, "remote", "get-url", "origin").stdout.strip()
            self.assertEqual(url, (root / remote).as_uri())
            head = git(root, clone, "symbolic-ref", "refs/remotes/origin/HEAD").stdout.strip()
            self.assertEqual(head, "refs/remotes/origin/main")
            self.assertEqual(branches(root, clone), ["main"])
            self.assertEqual(branches(root, remote), ["feature/a", "main"])
            self.assertEqual(sorted(path.name for path in (root / clone).iterdir()), [".git", "README.md", "app.txt"])
            feature = git(root, clone, "ls-tree", "--name-only", "origin/feature/a").stdout.splitlines()
            self.assertEqual(feature, ["a.txt"])
            parent = git(root, clone, "rev-parse", "origin/feature/a^", "origin/main").stdout.split()
            self.assertEqual(parent[0], parent[1])
            behind = git(root, remote, "log", "--format=%s", "main").stdout.splitlines()
            self.assertEqual(behind, ["unfetched main", "add main"])
            self.assertEqual(git(root, clone, "log", "--format=%s", "origin/main").stdout.splitlines(), ["add main"])
            self.assertEqual(branches(root, "repos/group/other"), ["main"])

    def test_git_after_setup_runs_in_a_repository_of_the_tree(self):
        case = {
            "repos": {"nakatomi-web": {}},
            "git_after_setup": [
                ["repos/nakatomi-web", "commit", "--quiet", "--allow-empty", "-m", "local work"],
                ["repos/nakatomi-web", "config", "gemba.root", "{root}"],
            ],
            "git_log": {"repos/nakatomi-web": ["local work", "add main"]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root, case, "git_after_setup")
            self.assertEqual(git(root, "repos/nakatomi-web", "config", "gemba.root").stdout.strip(), str(root))
            self.check(root, case, "git_after_setup", snapshot(root), subprocess.CompletedProcess([], 0, "", ""))

    def test_new_command_names_resolve_to_the_binary(self):
        for name in ("mark", "archive", "report", "set", "worktree", "init", "config"):
            with self.subTest(name=name):
                self.assertEqual(COMMANDS[name], ["gemba", name])
                with tempfile.TemporaryDirectory() as tmp:
                    result = self.execute(Path(tmp), {}, name, [name, "--help"])
                self.assertTrue((result.stdout + result.stderr).startswith("usage: gemba"), result.stderr)


def _make_test(source, case):
    def test(self):
        self.run_case(source, case)

    return test


for _name, _source, _case in load_cases():
    setattr(CaseTest, _name, _make_test(_source, _case))


if __name__ == "__main__":
    unittest.main()
