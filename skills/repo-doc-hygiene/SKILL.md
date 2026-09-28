---
name: repo-doc-hygiene
description: Edit or audit software-repository documentation, comments, and user-facing text for factual accuracy, clear ownership, and preserved behavior. Use project instructions for domain-specific checks; not for Word layout work.
---

# Repository documentation hygiene

Use the requested file or diff as the scope. An audit stays read-only unless the user asks for edits. Read the relevant repository instructions and locate the source of truth for each material claim; when evidence conflicts, report the conflict rather than choosing a convenient source.

Update the current owner of a fact and link to it from other places. Treat generated files as outputs of their maintained source. Preserve the purpose of historical records such as changelogs and postmortems; current-state guidance should stand on its own without a prior conversation.

When rewriting, retain actors, conditions, order, numbers, permissions, side effects, failure states, and the distinction between required and optional behavior. Keep missing data explicit. Remove narration or duplication only when it adds no fact or rationale.

After an edit, check links, commands, paths, and public names against the repository. Run the relevant formatting or documentation checks; user-facing runtime copy also needs a focused behavior check. For a read-only audit, report inspected evidence and gaps without running edit checks solely for formality.
