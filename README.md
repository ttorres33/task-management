# task-management

A Claude Code plugin for markdown-based task management. Generates daily/weekly task views, archives completed tasks, and tracks ideas.

## Installation

```bash
claude plugins add teresa-torres-plugins/task-management
```

After installation, run the setup wizard:

```
/task-management:setup
```

## Configuration

Configuration is stored in `~/.claude/task-management-config/config.yaml`:

```yaml
paths:
  tasks_root: "/path/to/your/Tasks"

folders:
  tasks: "tasks"
  ideas: "ideas"
  templates: "templates"
  memories: "memories"
  bugs: "bugs"
  completed: "completed"
  import: "import"

links:
  format: "obsidian"       # "obsidian" for [[wiki-links]] or "markdown" for [text](path)

integrations:
  research_system: false   # Set to true to include research digest in /today
```

### Link Format

The plugin supports two link formats:

- **obsidian** (default) - Wiki-style links: `[[task-name]]`
- **markdown** - Standard markdown links: `[task-name](tasks/task-name.md)`

Choose "obsidian" if you use Obsidian or another wiki-link aware editor. Choose "markdown" for standard markdown compatibility.

### Research System Integration

If you have the `research-system` plugin installed and want `/today` to include a research digest section, set `integrations.research_system: true`.

## Commands

### `/task-management:setup`

Interactive setup wizard to configure your tasks root folder and directory structure.

### `/task-management:today`

Generate daily task files:
- `today.md` - Overdue tasks, tasks due today, in-progress ideas
- `this-week.md` - Tasks for remaining days this week
- `next-week.md` - Tasks for next week

Also archives completed tasks and normalizes date formats.

### `/task-management:this-week`

Generate this week's task list (excluding today).

### `/task-management:next-week`

Generate next week's task list.

### `/task-management:archive`

Move completed one-time tasks from `tasks/` to `completed/`. Recurring tasks are never archived.

### `/task-management:ideas`

List ideas organized by status:
- In Progress - Actively working on
- Noodling - Exploring, might become in-progress

### `/task-management:clean-imports`

Move reviewed files from `import/` to their appropriate folders based on `type:` field.

### `/task-management:about`

Show this documentation.

## Skills

### `manage-tasks`

Task conventions and file organization rules. Claude uses this skill when creating or modifying task files to ensure consistent formatting.

To get Claude to reliably use this skill, try putting the following in your Tasks root directory CLAUDE.md: "Use the manage-tasks skill whenever creating or updating tasks."

## File Structure

The plugin expects this folder structure in your tasks root:

```
Tasks/
├── tasks/          # Items with due dates
├── ideas/          # Projects without due dates
├── templates/      # Reusable task templates
├── memories/       # Reference items (not actionable)
├── bugs/           # Issues to fix
├── completed/      # Archived one-time tasks
├── import/         # Staging area for triage
├── today.md        # Generated daily
├── this-week.md    # Generated daily
└── next-week.md    # Generated daily
```

## Task File Format

Each task is a markdown file with YAML frontmatter:

```yaml
---
type: task
due: 2025-01-15
tags: [project, urgent]
---
# Task Title

Task content here.
```

### Fields

**Required:**
- `type` - task, idea, template, memory, or bug

**Optional:**
- `due: YYYY-MM-DD` - Due date (required for tasks)
- `completed: YYYY-MM-DD` - Completion date
- `recurrence: weekly | biweekly | monthly | quarterly | yearly`
- `status: in-progress | noodling | someday` - For ideas only
- `tags: [tag1, tag2]` - Categorization

## License

MIT
