---
description: Generate next week's task list
---

# next-week

Generate `next-week.md`: tasks due Monday through Sunday of next week.

## Process

Run the script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-next-week.py
```

The script resolves which task system to act on from the current working directory,
then writes `next-week.md` into that root. It prints the resolved root before writing
anything — include that line in your summary so it is always clear which system was
touched.

Report the task count from the script's output. Do not re-read or re-render the file.

## Example Output

```markdown
---
week_start: 2026-03-16
week_end: 2026-03-22
---
# Next Week - Week of March 16

## Monday, March 16
- [ ] [[quarterly-review]]
- [ ] [[team-meeting-prep]]

## Wednesday, March 18
- [ ] [[client-call]]
```

Days with no tasks are skipped.
