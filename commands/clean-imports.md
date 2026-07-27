---
description: Move reviewed files from import/ to appropriate folders based on type
---

# clean-imports

Move reviewed files out of `import/` and into the folder matching their `type:` field.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/clean-imports.py
```

The script resolves which task system to act on from the current working directory,
and prints the resolved root before moving anything. **Always include that line in
your summary** — this command moves files.

Summarize what was moved:

```
Tasks root: /Users/you/Vaults/Work/Tasks  [work, via marker]

Moved 3 file(s) from import/:

tasks/ (1 file):
- [[task-name]]

ideas/ (2 files):
- [[idea-name]]
- [[another-idea]]

Skipped (no type field):
- filename.md

Import cleanup complete!
```

Files with no `type:` field, or an unrecognized one, stay in `import/`.

If nothing was moved, say "No files to process in import/." — but still report the
resolved root.
