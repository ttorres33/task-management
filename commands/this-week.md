---
description: Generate this week's task list (excluding today)
---

# this-week

Generate this week's task list (excluding today).

## Process

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calculate-weeks.py` to get accurate dates
2. Use "Tomorrow:" and "This Week: Sunday:" from the script output
3. Search all files in `tasks/` folder for tasks with `due:` between tomorrow and this week's Sunday (inclusive)
   - Handle both date formats: with leading zeros (`YYYY-MM-DD`) and without (`YYYY-M-D`)
4. Generate `this-week.md` with:
   - YAML frontmatter with `week_start` and `week_end` dates
   - Heading: `# This Week - Week ending [Month Day]`
   - Tasks grouped by day with subheadings: `## Monday, [Month Day]`, `## Tuesday, [Month Day]`, etc.
   - List of task links under each day: `- [ ] [[task-name]]`
   - Skip days with no tasks
   - If no tasks for the entire week, add note: `(Tasks due today are in today.md)`

**Important:** When searching for date ranges, use broad pattern like `^due: 2025-10-` then filter results to match the specific date range, accounting for both leading zero and no-leading-zero formats

## Example Output

```markdown
---
week_start: 2025-10-04
week_end: 2025-10-06
---
# This Week - Week ending October 6

## Friday, October 4
- [ ] [[send-liberty-mutual-product-sheets]]

## Saturday, October 5
- [ ] [[construct-connect-toolbox-sale]]
- [ ] [[client-meeting-prep]]
```
