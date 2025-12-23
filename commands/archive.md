---
description: Archive completed one-time tasks from tasks/ to completed/
---

# archive

Archive completed one-time tasks from tasks/ to completed/.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/archive-tasks.py
```

After running, summarize what was archived using the link format from `links.format` in config:

```
Archived X task(s) to completed/:
- [[task-name-1]]   (if obsidian)
- [task-name](completed/task-name.md)   (if markdown)
```

If nothing was archived, just say "No completed tasks to archive."
