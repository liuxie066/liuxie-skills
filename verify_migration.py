"""Verify source evidence, then the selected global copy (Python 3.11+)."""
import argparse
import json
import tomllib
from pathlib import Path

import yaml

from sync import entry_layout, load_selection, tree_snapshot


def verify(root, home, source_only=False):
    manifest = json.loads((root / "migration.json").read_text())
    source = root / "skills"
    names, expected = load_selection(root)
    all_content = tree_snapshot(source)
    sources = set(manifest["sources"])
    assert {p.parent.name for p in source.glob("*/SKILL.md")} == sources
    actual_files = {rel: item[2] for rel, item in all_content.items() if item[0] == "file"}
    assert actual_files == manifest["files"], "Source hashes differ from recorded evidence"
    assert set(names) <= sources
    policy = manifest["invocation_policy"]
    assert not set(policy["manual"]) & set(policy["automatic"])
    modes = {}
    for name in sources:
        path = source / name / "agents/openai.yaml"
        metadata = yaml.safe_load(path.read_text()) if path.exists() else {}
        metadata = metadata or {}
        assert isinstance(metadata, dict), path
        settings = metadata.get("policy", {})
        assert isinstance(settings, dict), path
        implicit = settings.get("allow_implicit_invocation", True)
        assert isinstance(implicit, bool), path
        modes[name] = "automatic" if implicit else "manual"
    for mode, recorded_names in policy.items():
        assert mode in ("manual", "automatic")
        for name in recorded_names:
            assert name in modes and modes[name] == mode, name
    assert not (source / "skill-creator").exists()
    ima = source / "ima-skill"
    assert list(ima.rglob("SKILL.md")) == [ima / "SKILL.md"]
    for module in ("notes", "knowledge-base"):
        assert (ima / module / "GUIDE.md").is_file()
        assert (ima / module / "references/api.md").is_file()
        assert f"{module}/GUIDE.md" in (ima / "SKILL.md").read_text()
    if not source_only:
        assert entry_layout(root, home) == "distributed", "Run the one-time migration first"
        assert tree_snapshot(home / ".agents/skills") == expected, "Global copy differs; rerun sync.py --apply"
        assert (home / ".codex/skills/.system/skill-creator/SKILL.md").is_file()
        config = tomllib.loads((home / ".codex/config.toml").read_text())
        disabled = {Path(s["path"]).expanduser() for s in config["skills"]["config"] if not s.get("enabled", True)}
        for name in manifest["codex_disabled"]:
            assert home / ".agents/skills" / name / "SKILL.md" in disabled, name
        for name in sources:
            legacy = home / ".codex/skills" / name
            assert not legacy.exists() and not legacy.is_symlink(), legacy
    manual = sum(modes[name] == "manual" for name in names)
    scope = "source/list only" if source_only else "source/list/global copy/entry links"
    print(f"PASS: {scope}; {len(sources)} source skills; {len(names)} selected ({manual} manual / {len(names)-manual} automatic)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only", action="store_true", help="check source/list evidence before sync or while retrying")
    args = parser.parse_args()
    verify(Path(__file__).resolve().parent, Path.home().resolve(), args.source_only)
