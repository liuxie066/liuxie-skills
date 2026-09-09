"""Distribute the central skill list to the fixed local Codex directory."""

import argparse
import hashlib
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import yaml


def real_directory(path):
    if not path.is_dir() or path.is_symlink() or path.resolve() != path.absolute():
        raise ValueError(f"Expected a real directory without symlink parents: {path}")


def tree_snapshot(root):
    """Compare content and permissions, including empty directories; never follow links."""
    real_directory(root)
    result = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISDIR(info.st_mode):
            value = ("directory", mode)
        elif stat.S_ISREG(info.st_mode):
            value = ("file", mode, hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            raise ValueError(f"Symlink or special file is not supported: {path}")
        result[path.relative_to(root).as_posix()] = value
    return result


def load_selection(root):
    source = root / "skills"
    real_directory(source)
    listing = root / "global-skills.txt"
    if listing.is_symlink() or not listing.is_file():
        raise ValueError(f"Missing regular global list: {listing}")
    names = []
    for line in listing.read_text().splitlines():
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name) or name in names:
            raise ValueError(f"Invalid or duplicate skill name: {name!r}")
        names.append(name)
    if not names:
        raise ValueError("Refusing an empty global list")
    snapshot = tree_snapshot(source)
    for name in names:
        skill = source / name / "SKILL.md"
        if not skill.is_file():
            raise ValueError(f"Missing SKILL.md: {skill}")
        lines = skill.read_text().splitlines()
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            raise ValueError(f"Missing YAML frontmatter: {skill}")
        metadata = yaml.safe_load("\n".join(lines[1:lines.index("---", 1)]))
        if (not isinstance(metadata, dict) or metadata.get("name") != name
                or not isinstance(metadata.get("description"), str)
                or not metadata["description"].strip()):
            raise ValueError(f"Invalid skill name/description: {skill}")
    chosen = set(names)
    return names, {key: value for key, value in snapshot.items()
                   if key.split("/", 1)[0] in chosen}


def entry_layout(root, home):
    source = root / "skills"
    target = home / ".agents/skills"
    claude = home / ".claude/skills"
    for path in (home, target.parent, claude.parent):
        real_directory(path)
    if (source == target or source.is_relative_to(target)
            or target.is_relative_to(source)):
        raise ValueError("Source and target must not overlap")
    if (target.is_symlink() and claude.is_symlink()
            and target.resolve() == source and claude.resolve() == source):
        return "legacy"
    real_directory(target)
    if not claude.is_symlink() or claude.resolve() != target:
        raise ValueError(f"Unknown entry layout: {claude} must link to {target}")
    return "distributed"


def sync(root, home, apply=False):
    real_directory(root)
    names, expected = load_selection(root)
    layout = entry_layout(root, home)
    rsync = shutil.which("rsync")
    if not rsync:
        raise ValueError("rsync is not installed")
    target = home / ".agents/skills"
    if layout == "legacy":
        if apply:
            raise ValueError("Legacy source symlinks: complete the documented one-time migration first")
        print(f"Preview only: back up the two source symlinks; create {target}; link Claude to it.")
        print("Then copy: " + ", ".join(names))
        return
    # Reject destination links too: source is authoritative, but external paths are never ours.
    tree_snapshot(target)
    args = [rsync, "-acvi", "--delete", "--delete-excluded"]
    if not apply:
        args.append("-n")
    args.extend(f"--include=/{name}/***" for name in names)
    args.extend(["--exclude=*", str(root / "skills") + "/", str(target) + "/"])
    # ponytail: serial local maintenance; add a shared lock only if concurrent writers are needed.
    subprocess.run(args, check=True)
    if apply:
        current_names, current_source = load_selection(root)
        if current_names != names or current_source != expected:
            raise ValueError("Source/list changed during sync; stop editing and rerun")
        actual = tree_snapshot(target)
        differences = sorted(key for key in expected.keys() | actual.keys()
                             if expected.get(key) != actual.get(key))
        if differences:
            raise ValueError("Copy verification failed: " + ", ".join(differences))
        print(f"PASS: {len(names)} global skills match source content and permissions")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="update the copy; default is a read-only preview")
    args = parser.parse_args()
    try:
        sync(Path(__file__).resolve().parent, Path.home().resolve(), args.apply)
    except (OSError, ValueError, RuntimeError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        if args.apply:
            print("Sync incomplete; the copy may be partially updated. Fix the cause and rerun.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
