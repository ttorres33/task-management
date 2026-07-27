---
description: Archive completed one-time tasks from tasks/ to completed/
---

# archive

Move completed one-time tasks from `tasks/` to `completed/`. Recurring tasks (those
with a `recurrence:` field) are never archived.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/archive-tasks.py
```

The script resolves which task system to act on from the current working directory,
and prints the resolved root before moving anything. **Always include that line in
your summary** — this command moves files, so which system it acted on must never be
in doubt.

Summarize what was archived, using the link format the script reports:

```
Tasks root: /Users/you/Vaults/Work/Tasks  [work, via marker]

Archived 2 task(s) to completed/:
- [[task-name-1]]                              (if obsidian)
- [task-name](completed/task-name.md)          (if markdown)

Skipped 1 recurring task (stays in tasks/):
- [[weekly-review]]
```

If nothing was archived, say "No completed tasks to archive." — but still report the
resolved root.
