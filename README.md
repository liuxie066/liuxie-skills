# liuxie-skills

Reusable Codex skills by liuxie.

## Skills

| Skill | Purpose |
| --- | --- |
| [`devflow`](skills/devflow/) | Move a development task through brainstorming, a durable design, independent critique, plan review, implementation, and deep code review, with explicit human confirmation between every stage. |

## Install

From this repository:

```bash
cp -R skills/devflow ~/.agents/skills/
```

Then invoke it in Codex:

```text
$devflow <task>
```

`devflow` composes the companion skills `ponytail`, `planreview`, and `deepreview`. In an `options-monitor` repository it can also use the optional project skill `om-doc-hygiene`; elsewhere it follows that repository's documentation conventions.

## License

MIT
