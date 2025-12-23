---
description: Archive completed one-time tasks from tasks/ to completed/
---

# archive

Archive completed one-time tasks from tasks/ to completed/.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/archive-tasks.py
```

After running, summarize what was archived in a clean format:

```
Archived X task(s) to completed/:
- [[task-name-1]]
- [[task-name-2]]
```

If nothing was archived, just say "No completed tasks to archive."
