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

### Step 3: Validate Path

Verify the tasks root path exists:

```bash
ls -la "<tasks_root_path>"
```

If it doesn't exist, ask if the user wants to create it.

### Step 4: Create Config Directory

```bash
mkdir -p ~/.claude/task-management-config
```

### Step 5: Write Config File

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
```

### Step 6: Verify Setup

Confirm the config was written:

```bash
cat ~/.claude/task-management-config/config.yaml
```

### Step 7: Create Missing Folders

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
```
