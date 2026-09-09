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
        print("PASS: source-only precheck, installer-result/list/sync/verification closure")


if __name__ == "__main__":
    test_sync()
    test_verifier()
