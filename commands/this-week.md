---
description: Generate this week's task list (excluding today)
---

# this-week

Generate `this-week.md`: tasks due from tomorrow through the end of this week.

## Process

Run the script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-this-week.py
```

The script resolves which task system to act on from the current working directory,
then writes `this-week.md` into that root. It prints the resolved root before writing
anything — include that line in your summary so it is always clear which system was
touched.

Report the task count from the script's output. Do not re-read or re-render the file.

## Example Output

```markdown
---
week_start: 2026-03-09
week_end: 2026-03-15
---
# This Week - Week ending March 15

## Thursday, March 12
- [ ] [[send-liberty-mutual-product-sheets]]

## Saturday, March 14
- [ ] [[construct-connect-toolbox-sale]]
- [ ] [[client-meeting-prep]]
```

Days with no tasks are skipped. If today is the last day of the week, the file says
`No tasks remaining this week.`

Tasks due *today* are in `today.md`, not here.
