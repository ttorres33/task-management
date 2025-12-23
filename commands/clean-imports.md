---
description: Move reviewed files from import/ to appropriate folders based on type
---

# clean-imports

Move all reviewed files from import/ to their appropriate folders based on type.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/clean-imports.py
```

After running, summarize what was moved in a clean format:

```
Moved X file(s) from import/:

tasks/ (N files):
- [[task-name]]

ideas/ (N files):
- [[idea-name]]

Skipped (no type field):
- filename.md

Import cleanup complete!
```

If nothing was moved, just say "No files to process in import/."
