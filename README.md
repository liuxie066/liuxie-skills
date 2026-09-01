# liuxie-skills

Reusable Codex skills by liuxie.

## Skills

| Skill | Purpose |
| --- | --- |
| [`devflow`](skills/devflow/) | Move a development task through brainstorming, a durable design, four independent design critiques, plan review, implementation, and deep code review, with human-gated transitions. |

## Install

From this repository:

```bash
cp -R skills/devflow ~/.agents/skills/
```

Then invoke it in Codex:

```text
$devflow <task>
```

`devflow` composes the companion skills `ponytail`, `planreview`, and `deepreview`. Its four-person design panel uses DSH Crew `ds-pro` for the fourth reviewer when available and falls back to a native subagent otherwise. In an `options-monitor` repository it can also use the optional project skill `om-doc-hygiene`; elsewhere it follows that repository's documentation conventions.

## License

MIT
