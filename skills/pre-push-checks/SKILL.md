---
name: pre-push-checks
description: Verify the exact repository change intended for push or review-readiness, including its base, dirty files, relevant tests, and required project checks. Verification alone does not authorize delivery.
---

# Pre-push checks

Identify the intended branch and base from the request or PR. Inspect committed changes since their merge base, the staged index, unstaged edits, and untracked paths before selecting the outgoing scope. Keep unrelated work out of the change; do not reset or stage it for convenience.

Choose checks that can expose a regression in the affected behavior. Include public interfaces and adjacent consumers when the change crosses their contracts. Run repository-required checks and compare their inputs with the outgoing content. Reuse passing evidence only while the relevant code, tests, configuration, dependencies, generated inputs, base, and validation environment remain unchanged.

Check the staged patch before commit and the resulting commit before push. A passing check on a dirty working tree does not prove that a different staged or committed tree passed. If a required check fails, fix within the authorized scope or report the blocker; do not bypass it.

Report the verified base and scope, checks and outcomes, remaining gaps, and any unrelated work preserved. Stop at the user's authorized delivery stage; this skill does not authorize commit, push, PR, merge, release, deployment, or production writes.
