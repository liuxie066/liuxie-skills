"""Run with Python 3.11+; uses only temporary source/home directories."""

import os
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import sync


def rejected(action):
    try:
        action()
    except (ValueError, OSError, subprocess.CalledProcessError):
        return
    raise AssertionError("Expected rejection")


def skill(root, name):
    folder = root / "skills" / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test skill\n---\n")
    return folder


def test_sync():
    with tempfile.TemporaryDirectory(prefix="skill-sync-test-") as folder:
        base = Path(folder).resolve()
        root, home = base / "source", base / "home"
        root.mkdir(); home.mkdir()
        source = skill(root, "alpha")
        skill(root, "unused")
        (source / "empty").mkdir()
        script = source / "run.sh"
        script.write_text("old"); script.chmod(0o755)
        listing = root / "global-skills.txt"
        listing.write_text("# chosen\nalpha\n")
        for name in (".agents", ".claude", ".codex"):
            (home / name).mkdir()
        sentinel = home / ".codex/untouched"
        sentinel.write_text("system sentinel")
        target, claude = home / ".agents/skills", home / ".claude/skills"
        target.symlink_to(root / "skills"); claude.symlink_to(root / "skills")
        before = sync.tree_snapshot(root)
        sync.sync(root, home)
        rejected(lambda: sync.sync(root, home, True))
        assert target.is_symlink() and claude.is_symlink()
        assert sync.tree_snapshot(root) == before
        target.unlink(); target.mkdir()
        rejected(lambda: sync.sync(root, home, True))
        claude.unlink(); claude.symlink_to(target)
        empty = sync.tree_snapshot(target)
        sync.sync(root, home)
        assert sync.tree_snapshot(target) == empty
        sync.sync(root, home, True)
        assert sync.tree_snapshot(target) == sync.load_selection(root)[1]
        # Content mismatch despite equal size/mtime must be repaired; mtime then stays stable on no-op.
        stamp = 1700000000
        script.write_text("new"); os.utime(script, (stamp, stamp))
        os.utime(target / "alpha/run.sh", (stamp, stamp))
        sync.sync(root, home, True)
        assert (target / "alpha/run.sh").read_text() == "new"
        mtime = (target / "alpha/run.sh").stat().st_mtime_ns
        sync.sync(root, home, True)
        assert (target / "alpha/run.sh").stat().st_mtime_ns == mtime
        # Installation and source-only choices, then deactivation and stale file removal.
        skill(root, "installed")
        listing.write_text("alpha\ninstalled\n")
        sync.sync(root, home, True)
        assert (target / "installed/SKILL.md").is_file()
        skill(root, "source-only")
        listing.write_text("alpha\n")
        (target / "alpha/stale").write_text("stale")
        sync.sync(root, home, True)
        assert not (target / "installed").exists() and not (target / "source-only").exists()
        assert not (target / "alpha/stale").exists()
        assert (root / "skills/installed/SKILL.md").is_file()
        # A failed copy can leave partial data; retry must converge without a recovery protocol.
        def fail_copy(*args, **kwargs):
            (target / "alpha/run.sh").write_text("bad")
            raise subprocess.CalledProcessError(12, args[0])
        with patch.object(sync.subprocess, "run", side_effect=fail_copy):
            rejected(lambda: sync.sync(root, home, True))
        sync.sync(root, home, True)
        assert sync.tree_snapshot(target) == sync.load_selection(root)[1]
        for text in ("", "alpha\nalpha\n", "../alpha\n", "*\n", "/alpha\n", "missing\n", "alpha # comment\n"):
            listing.write_text(text)
            rejected(lambda: sync.sync(root, home, True))
        listing.write_text("alpha\n")
        entry = source / "SKILL.md"
        original = entry.read_text()
        entry.write_text("---\nname: other\ndescription: test\n---\n")
        rejected(lambda: sync.sync(root, home, True))
        entry.write_text(original)
        (source / "escape").symlink_to(home)
        rejected(lambda: sync.sync(root, home, True))
        (source / "escape").unlink()
        os.mkfifo(source / "pipe")
        rejected(lambda: sync.sync(root, home, True))
        (source / "pipe").unlink()
        (target / "escape").symlink_to(home / ".codex")
        rejected(lambda: sync.sync(root, home, True))
        (target / "escape").unlink()
        with patch.object(sync.shutil, "which", return_value=None):
            rejected(lambda: sync.sync(root, home))
        moved = home / "agents-away"
        (home / ".agents").rename(moved); (home / ".agents").symlink_to(moved)
        rejected(lambda: sync.sync(root, home, True))
        (home / ".agents").unlink(); moved.rename(home / ".agents")
        assert sentinel.read_text() == "system sentinel"
        assert (root / "skills/unused/SKILL.md").is_file()
        # Exercise the real CLI in an isolated checkout, with HOME obtained through a mock only.
        shutil.copyfile(Path(sync.__file__), root / "sync.py")
        with patch.object(sync, "__file__", str(root / "sync.py")), patch.object(Path, "home", return_value=home):
            with patch("sys.argv", ["sync.py"]):
                assert sync.main() == 0
            with patch("sys.argv", ["sync.py", "--apply"]):
                assert sync.main() == 0
            listing.write_text("")
            with patch("sys.argv", ["sync.py", "--apply"]):
                assert sync.main() == 1
        print("PASS: selection, content/modes, dry-run, retries, CLI and path/input boundaries")


def test_invocation_policy():
    from verify_migration import validate_skill
    with tempfile.TemporaryDirectory(prefix="skill-policy-test-") as tmp:
        root = Path(tmp).resolve() / "source"
        home = root.parent / "home"
        entry = skill(root, "alpha")
        (root / "global-skills.txt").write_text("alpha\n")
        (home / ".agents/skills").mkdir(parents=True)
        (home / ".claude").mkdir()
        (home / ".claude/skills").symlink_to(home / ".agents/skills")
        sentinel = home / ".agents/skills/untouched"
        sentinel.write_text("keep")
        target_before = sync.tree_snapshot(sentinel.parent)
        md, agent = entry / "SKILL.md", entry / "agents/openai.yaml"
        agent.parent.mkdir()
        def write(front="", policy=None, body="Instructions.\n"):
            md.write_text("---\nname: alpha\ndescription: Test skill\n" + front + "---\n" + body)
            if policy is None:
                agent.unlink(missing_ok=True)
            else:
                agent.write_text(policy)
        manual = "policy:\n  allow_implicit_invocation: false\n"
        automatic = "policy:\n  allow_implicit_invocation: true\n"
        disabled = "disable-model-invocation: true\n"
        enabled = "disable-model-invocation: false\n"
        for front, policy in (("", None), (enabled, automatic), (disabled, manual),
                              (disabled, "interface:\n  display_name: Alpha\ndependencies: {}\n" + manual)):
            write(front, policy)
            sync.load_selection(root)
            validate_skill(entry)
        invalid = [
            (disabled, automatic), (enabled, manual), ("", manual),
            ('disable-model-invocation: "true"\n', manual),
            ('disable-model-invocation: 1\n', manual),
            ('disable-model-invocation: null\n', manual),
            (disabled, 'policy:\n  allow_implicit_invocation: "false"\n'),
            (disabled, 'policy:\n  allow_implicit_invocation: 0\n'),
            (disabled, 'policy: []\n'), (disabled, '[]\n'), (disabled, ''),
            (disabled + disabled, manual),
            (disabled, manual + manual),
            (disabled, manual + '  allow_implicit_invocation: false\n'),
            (disabled + 'metadata:\n  same: a\n  same: b\n', manual),
            (disabled + '[bad yaml\n', manual),
        ]
        for value in ('yes', 'no', 'on', 'off', 'YES', 'NO', 'Yes', 'No', 'On', 'Off', '!!bool no'):
            invalid.append((f'disable-model-invocation: {value}\n', manual))
            invalid.append((disabled, f'policy:\n  allow_implicit_invocation: {value}\n'))
        assert sync.yaml.safe_load('no') is False  # Our resolver must not mutate PyYAML globally.
        write('disable-model-invocation: TRUE\n', 'policy:\n  allow_implicit_invocation: False\n')
        sync.load_selection(root)
        # Display text resembling YAML 1.1 booleans remains ordinary sibling metadata.
        write(disabled, 'interface:\n  display_name: On\n' + manual)
        sync.load_selection(root)
        assert sync.yaml_mapping(agent.read_text(), agent)['interface']['display_name'] == 'On'
        for front, policy in invalid:
            write(front, policy)
            for apply in (False, True):
                with patch.object(sync.subprocess, "run") as run:
                    rejected(lambda: sync.sync(root, home, apply))
                    run.assert_not_called()
                assert sync.tree_snapshot(sentinel.parent) == target_before
            with patch.object(sync.subprocess, "run") as run:
                rejected(lambda: validate_skill(entry))
                run.assert_not_called()
        for bad in ('---\n[]\n---\n', '---\nname: alpha\ndescription: Test\n', 'no header'):
            md.write_text(bad)
            with patch.object(sync.subprocess, "run") as run:
                rejected(lambda: sync.sync(root, home, True))
                run.assert_not_called()
        # The compatible copy must not hide unrelated system validation errors.
        for front, body in ((disabled + 'unknown: field\n', 'Instructions.\n'),
                            (disabled, '[TODO: finish this]\n')):
            write(front, manual, body)
            rejected(lambda: validate_skill(entry))
        write(disabled, manual)
        original = sync.tree_snapshot(entry)
        rejected(lambda: validate_skill(entry, root / 'missing-validator.py'))
        real_run = subprocess.run
        copies = []
        def capture(args, **kwargs):
            copy = Path(args[-1])
            copies.append(copy)
            assert sorted(p.name for p in copy.iterdir()) == ['SKILL.md']
            assert 'disable-model-invocation' not in (copy / 'SKILL.md').read_text()
            assert (copy / 'SKILL.md').read_text().endswith('Instructions.\n')
            return real_run(args, **kwargs)
        with patch.object(sync.subprocess, 'run', side_effect=capture):
            validate_skill(entry)
        assert copies and all(not p.exists() for p in copies)
        def failure(args, **kwargs):
            copies.append(Path(args[-1]))
            raise subprocess.CalledProcessError(7, args)
        with patch.object(sync.subprocess, 'run', side_effect=failure):
            rejected(lambda: validate_skill(entry))
        assert all(not p.exists() for p in copies)
        assert sync.tree_snapshot(entry) == original
        assert sync.tree_snapshot(sentinel.parent) == target_before
        print("PASS: policy agreement/defaults, zero-rsync failures, compatible-copy errors and cleanup")


def test_verifier():
    from verify_migration import verify
    central = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="skill-verifier-test-") as folder:
        base = Path(folder).resolve()
        root, home = base / "source", base / "home"
        root.mkdir(); home.mkdir()
        shutil.copytree(central / "skills", root / "skills")
        for name in ("migration.json", "global-skills.txt"):
            shutil.copyfile(central / name, root / name)
        for name in (".agents/skills", ".claude", ".codex/skills/.system/skill-creator"):
            (home / name).mkdir(parents=True)
        (home / ".codex/skills/.system/skill-creator/SKILL.md").write_text("system fixture")
        manifest = json.loads((root / "migration.json").read_text())
        (home / ".codex/config.toml").write_text("\n".join(
            f'[[skills.config]]\npath = "{home}/.agents/skills/{name}/SKILL.md"\nenabled = false'
            for name in manifest["codex_disabled"]))
        (home / ".claude/skills").symlink_to(home / ".agents/skills")
        verify(root, home, source_only=True)
        sync.sync(root, home, True)
        verify(root, home)
        # Represent a validated installer result; only its source evidence and list membership change.
        added = skill(root, "installed-example")
        manifest["sources"]["installed-example"] = "local installer fixture"
        manifest["files"]["installed-example/SKILL.md"] = hashlib.sha256((added / "SKILL.md").read_bytes()).hexdigest()
        manifest["invocation_policy"]["automatic"].append("installed-example")
        (root / "migration.json").write_text(json.dumps(manifest))
        verify(root, home, source_only=True)
        assert not (home / ".agents/skills/installed-example").exists()
        listing = root / "global-skills.txt"
        listing.write_text(listing.read_text() + "installed-example\n")
        verify(root, home, source_only=True)
        try:
            verify(root, home)
        except AssertionError:
            pass
        else:
            raise AssertionError("Runtime must fail before the newly selected skill is synced")
        sync.sync(root, home, True)
        verify(root, home)
        assert (home / ".agents/skills/installed-example/SKILL.md").is_file()
        before_list = listing.read_bytes()
        (added / "agents").mkdir()
        (added / "agents/openai.yaml").write_text("interface:\n  display_name: Installed\npolicy:\n  allow_implicit_invocation: false\n")
        entry = added / "SKILL.md"
        entry.write_text(entry.read_text().replace("---\n", "---\ndisable-model-invocation: true\n", 1))
        from verify_migration import validate_skill
        validate_skill(added)
        manifest["invocation_policy"]["automatic"].remove("installed-example")
        manifest["invocation_policy"]["manual"].append("installed-example")
        for path in added.rglob("*"):
            if path.is_file():
                manifest["files"][path.relative_to(root / "skills").as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        (root / "migration.json").write_text(json.dumps(manifest))
        verify(root, home, source_only=True)
        sync.sync(root, home, True)
        verify(root, home)
        assert listing.read_bytes() == before_list
        assert 'display_name: Installed' in (home / '.agents/skills/installed-example/agents/openai.yaml').read_text()
        print("PASS: source-only precheck, create/install/update/list/sync/verification closure")


if __name__ == "__main__":
    test_sync()
    test_invocation_policy()
    test_verifier()
