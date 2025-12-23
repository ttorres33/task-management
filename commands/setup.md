---
description: Configure task management plugin paths
---

# Setup Wizard

Configure the task-management plugin for your system.

## Process

### Step 1: Get Tasks Root Path

Ask the user for their tasks root directory path. This is the folder containing their task files and subfolders.

Example: `/Users/username/Documents/Tasks` or `/Users/username/Vaults/Work/Tasks`

### Step 2: Confirm Folder Structure

Show the user the default folder names and ask if they want to customize:

```yaml
folders:
  tasks: "tasks"           # Items with due dates
  ideas: "ideas"           # Projects without due dates
  templates: "templates"   # Reusable task templates
  memories: "memories"     # Reference items (not actionable)
  bugs: "bugs"             # Issues to fix
  completed: "completed"   # Archived one-time tasks
  import: "import"         # Staging area for triage
```

Most users will use the defaults.

### Step 3: Ask Link Format

Ask the user which link format they prefer:
- **obsidian** - Wiki-style links: `[[task-name]]`
- **markdown** - Standard markdown: `[task-name](tasks/task-name.md)`

Default to "obsidian" if user is unsure.

### Step 4: Check for Research System Plugin

Check if the research-system plugin is installed:

```bash
ls ~/.claude/plugins/research-system 2>/dev/null || ls -d ~/*/cc-plugins/research-system 2>/dev/null || echo "not found"
```

If found, ask the user if they want to enable the research-system integration (adds research digest to /today output).

### Step 5: Validate Path

Verify the tasks root path exists:

```bash
ls -la "<tasks_root_path>"
```

If it doesn't exist, ask if the user wants to create it.

### Step 6: Create Config Directory

```bash
mkdir -p ~/.claude/task-management-config
```

### Step 7: Write Config File

Create `~/.claude/task-management-config/config.yaml` with the user's settings:

```yaml
paths:
  tasks_root: "<user's path>"

folders:
  tasks: "tasks"
  ideas: "ideas"
  templates: "templates"
  memories: "memories"
  bugs: "bugs"
  completed: "completed"
  import: "import"

links:
  format: "<obsidian or markdown>"

integrations:
  research_system: <true or false>
```

### Step 8: Verify Setup

Confirm the config was written:

```bash
cat ~/.claude/task-management-config/config.yaml
```

### Step 9: Create Missing Folders

Check which folders exist and offer to create missing ones:

```bash
ls -la "<tasks_root>"
```

For any missing folders from the config, ask if user wants to create them.

## Example Output

```
Task Management Setup Complete!

Configuration saved to: ~/.claude/task-management-config/config.yaml

Tasks root: /Users/ttorres/Vaults/Work/Tasks
Link format: obsidian
Research integration: enabled

Folders:
  - tasks/       (exists)
  - ideas/       (exists)
  - templates/   (exists)
  - memories/    (exists)
  - bugs/        (exists)
  - completed/   (exists)
  - import/      (exists)

You can now use:
  /task-management:today    - Generate daily task files
  /task-management:archive  - Archive completed tasks
  /task-management:ideas    - List ideas by status

To get Claude to reliably use the manage-tasks skill when creating and updating tasks, add the following to your CLAUDE.md in your Tasks root directory: "Use the manage-tasks skill whenever creating or updating tasks."
```
