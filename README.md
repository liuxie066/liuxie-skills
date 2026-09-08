# liuxie-skills

Reusable Codex skills by liuxie.

## Skills

| Skill | Purpose |
| --- | --- |
| [`prdflow`](skills/prdflow/) | Turn an idea into a confirmed, testable product requirement through dialogue, goal checks, concrete flows, and a bounded devflow handoff. |
| [`devflow`](skills/devflow/) | Move a development task through brainstorming, a durable design, four independent design critiques, plan review, implementation, and deep code review, with human-gated transitions. |

## Install

From this repository:

```bash
mkdir -p ~/.codex/skills
cp -R skills/devflow ~/.codex/skills/
```

Then invoke it in Codex:

```text
$devflow <task>
```

`devflow` works standalone and uses `ponytail`, `planreview`, `deepreview`, and the project-specific `om-doc-hygiene` when they are discoverable. Missing companion skills use disclosed native fallbacks. Its four-person design panel uses a DSH Crew pro worker (`tier=pro`) when available and falls back to a native subagent otherwise.

`prdflow` prepares product requirements; it does not start `devflow` or authorize implementation.

## License

MIT
