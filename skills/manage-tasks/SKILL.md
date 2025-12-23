---
name: manage-tasks
description: Task conventions and file organization for markdown-based task management. Use when creating or modifying task files.
allowed-tools: Read, Edit, Write, Glob, Grep
---

# Task Management Skill

## File Structure

- `tasks/` - Items with specific due dates that need to be completed
- `ideas/` - Projects and ideas without due dates (someday/maybe)
- `templates/` - Reusable task templates (e.g., blog post checklist, event prep)
- `memories/` - Reference items and context (not actionable)
- `bugs/` - Issues and problems to fix
- `completed/` - Archived one-time tasks that have been finished
- `import/` - Temporary folder for reviewing imported items before moving to appropriate folders

## Task File Format

Each task is a markdown file with YAML frontmatter:

```yaml
---
type: task | idea | template | memory | bug
due: YYYY-MM-DD
tags: [tag1, tag2]
---
# Task Title

Task content here.
```

### Required Fields

- `type` - Categorizes the file for organization:
  - `task` - Actionable item with due date (goes in tasks/)
  - `idea` - Project or concept without deadline (goes in ideas/)
  - `template` - Reusable checklist or structure (goes in templates/)
  - `memory` - Reference/context item, not actionable (goes in memories/)
  - `bug` - Issue or problem to fix (goes in bugs/)

### Optional Fields

- `due: YYYY-MM-DD` - Due date (required for tasks, optional for ideas)
- `completed: YYYY-MM-DD` - Completion date for finished one-time tasks
- `recurrence: monthly | quarterly | weekly | biweekly | yearly` - For recurring tasks
- `recurrence_day: N` - Day of month for recurring tasks
- `status: in-progress | noodling | someday` - For idea files only (not used in tasks/)
- `tags: [tag1, tag2]` - Categorization tags

## File Organization Rules

### tasks/
- One-time tasks: When completed, add `completed:` date and move to completed/
- Recurring tasks: Stay in tasks/ permanently, update `due:` date when complete (never move to completed/)

### ideas/
- Use `status` field to track progress:
  - `in-progress` - Actively working on this, but no specific deadline yet
  - `noodling` - Thinking about it, exploring, might become in-progress
  - `someday` - Parked for later, not active now
- When an idea gets a due date, move it to tasks/

### templates/
- Copy template, add due date and specifics, save to tasks/

### memories/
- No due dates, no action required
- Meeting notes, documentation, decisions made

### bugs/
- Can have due dates or not
- Track technical issues, website problems, system bugs
- When fixed, add `completed:` date and move to completed/

### completed/
- Contains finished tasks with `completed:` date
- Keeps active tasks/ folder clean
- Never put recurring tasks here

### import/
- Set `type:` field during review
- Move to appropriate folder based on type

## Recurring Tasks

Recurring tasks include:
- Instructions section explaining how to update when complete
- History section to log completion dates
- Never move to completed/ - stay in tasks/ permanently

Example:
```yaml
---
type: task
due: 2025-01-15
recurrence: monthly
recurrence_day: 15
tags: [admin]
---
# Monthly Report

## Instructions
When completing this task:
1. Update the `due:` date to next month
2. Add completion date to History section

## History
- 2024-12-15: Completed
- 2024-11-15: Completed
```

## Task Creation Guidelines

**CRITICAL: Preserve user's exact text formatting**

When the user provides notes, content, or task details:
- Use their EXACT text - preserve capitalization, punctuation, line breaks exactly as given
- Do NOT capitalize the first letter if they didn't
- Do NOT add periods at the end if they didn't include them
- Do NOT add section headers like "## Notes" unless they provided them
- Do NOT reformat or "clean up" their text in any way

### Simple tasks
Just the essentials:
- due date
- tags
- minimal notes

### Complex tasks
Include:
- Checklist section
- Notes section
- Resources/links section (if needed)

### Recurring tasks
Include:
- recurrence field
- Instructions section
- History section

### Idea files
Include:
- status field (in-progress, noodling, or someday)
- tags
- notes/description
- No due date (if it gets a due date, move to tasks/)

## Tagging Conventions

- Use semantic tags that describe the task category, context, or project
- Keep tags lowercase and hyphenated for multi-word tags
- Be consistent with existing tags in the project
