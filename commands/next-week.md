---
description: Generate next week's task list
---

# next-week

Generate next week's task list.

## Process

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calculate-weeks.py` to get accurate dates
2. Use "Next Week: Monday:" and "Next Week: Sunday:" from the script output
3. Search all files in `tasks/` folder for tasks with `due:` between next week's Monday and Sunday (inclusive)
   - Handle both date formats: with leading zeros (`YYYY-MM-DD`) and without (`YYYY-M-D`)
4. Generate `next-week.md` with:
   - YAML frontmatter with `week_start` and `week_end` dates
   - Heading: `# Next Week - Week of [Month Day]`
   - Tasks grouped by day with subheadings: `## Monday, [Month Day]`, `## Tuesday, [Month Day]`, etc.
   - List of task links under each day: `- [ ] [[task-name]]`
   - Skip days with no tasks
   - If no tasks for the entire week, add note: `No tasks scheduled for next week.`

**Important:** When searching for date ranges, use broad pattern like `^due: 2025-10-` then filter results to match the specific date range, accounting for both leading zero and no-leading-zero formats

## Example Output

```markdown
---
week_start: 2025-10-07
week_end: 2025-10-13
---
# Next Week - Week of October 7

## Monday, October 7
- [ ] [[quarterly-review]]
- [ ] [[team-meeting-prep]]

## Wednesday, October 9
- [ ] [[client-call]]

## Friday, October 11
- [ ] [[weekly-review]]
```
