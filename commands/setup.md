---
description: Configure a task management system in the current folder
---

# Setup Wizard

Configure a task system for the task-management plugin.

This command is **additive**. It configures one task system by writing a marker file
into that system's root folder. Running it again in a different folder adds a second
system; it never removes or rewrites the first. There is no registry of roots — the
marker file *is* the registration.

If a global config already exists at `~/.claude/task-management-config/config.yaml`,
leave it alone. Never overwrite it.

## Process

### Step 1: Determine the tasks root

The tasks root is the folder that contains the task subfolders (`tasks/`, `ideas/`,
and so on).

Start by checking whether the current directory is already a configured root:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/show-config.py
```

- If it reports a root and `source: marker`, this folder (or a parent) is already
  configured. Show the user what it resolved and ask whether they want to reconfigure
  it or set up a *different* folder.
- If it errors with "No task system found", proceed.

Then ask the user for the tasks root path, defaulting to the current directory.

Example: `/Users/username/Vaults/Work/Tasks`

### Step 2: Confirm folder structure

Show the default folder names and ask whether to customize:

```yaml
tasks: "tasks"           # Items with due dates
ideas: "ideas"           # Projects without due dates
templates: "templates"   # Reusable task templates
memories: "memories"     # Reference items (not actionable)
bugs: "bugs"             # Issues to fix
completed: "completed"   # Archived one-time tasks
import: "import"         # Staging area for triage
```

Most users keep the defaults.

### Step 3: Ask link format

- **obsidian** — wiki-style links: `[[task-name]]`
- **markdown** — standard links: `[task-name](tasks/task-name.md)`

Default to `obsidian` if the user is unsure. For a vault shared with another person,
recommend `obsidian`, since a shared vault is by definition being read in Obsidian.

### Step 4: Ask about research-system integration

Ask the plugin whether research-system is available. Do not probe the filesystem
yourself:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/show-config.py --detect-research
```

- `research_system_installed: yes` — ask whether to enable the integration, which
  adds a research digest link to `/today` output.
- `research_system_installed: no` — default to `research_system: false`. Mention the
  one case where `true` still makes sense: if this machine receives digests from
  another machine through vault sync, `true` links the existing digest without
  generating anything. Otherwise leave it `false`.

For a root shared with another person, recommend `false`: the other person will not
have the research-system plugin, and the digest is personal.

### Step 5: Create the root and any missing folders

```bash
ls -la "<tasks_root>"
```

If the root does not exist, ask whether to create it. Create any missing folders from
step 2.

### Step 6: Write the marker file

Write `<tasks_root>/task-management-root.md`:

```markdown
---
name: <short-name, e.g. work or household>
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
  research_digest_path: "../Research/daily-digests/{date}.md"
---
# Task Management Root

Marks this folder as a task-management root. Safe to edit; do not rename or move.
```

Notes:

- `name` is what makes the file a valid marker. Without it, the file is treated as an
  ordinary note and ignored.
- The `folders` block may be omitted to accept the defaults, but it must be present if
  this root uses custom folder names. Settings do not merge — a marker supplies the
  whole set or none of it.
- The marker contains **no absolute paths**. The root is implied by the file's own
  location, so the file works unchanged on another device or under another user's home
  directory.
- Only include `research_digest_path` if `research_system` is `true`.
- It is a Markdown file rather than a dotfile so that Obsidian Sync will sync it.
  Hidden files and `.yaml` files do not sync reliably; Markdown always does.

### Step 7: Verify

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/show-config.py
```

Run this **from inside the new root**. Confirm it reports the expected path,
`source: marker`, and the chosen link format.

### Step 8: Offer a default root (only if no global config exists)

The marker handles every case where Claude is launched inside or directly above the
tasks root. For running commands from somewhere else entirely — a code project, say —
the plugin falls back to a global default.

Check first:

```bash
cat ~/.claude/task-management-config/config.yaml 2>/dev/null || echo "none"
```

- **If a config already exists:** leave it untouched. Mention that it still works and
  that this root's own settings now come from its marker.
- **If none exists:** ask whether to create one naming this root as the default:

  ```bash
  mkdir -p ~/.claude/task-management-config
  ```

  ```yaml
  # Which task system to use when the working directory is outside every tasks root.
  default_root: "<tasks_root>"
  ```

  This is optional. Skipping it means commands run from outside any tasks root will
  report an error explaining how to choose one, which is the correct behavior on a
  machine that deliberately keeps no global state.

## Example Output

```
Task Management Setup Complete!

Tasks root:   /Users/you/Vaults/Teresa-Rick/Tasks
Name:         household
Marker:       /Users/you/Vaults/Teresa-Rick/Tasks/task-management-root.md
Link format:  obsidian
Research:     disabled

Folders:
  - tasks/       (created)
  - ideas/       (created)
  - templates/   (created)
  - memories/    (created)
  - bugs/        (created)
  - completed/   (created)
  - import/      (created)

Default root: unchanged (~/.claude/task-management-config/config.yaml already
              points at /Users/you/Vaults/Work/Tasks)

To use this system, run Claude from inside this folder — or from the vault folder
directly above it. There are no flags to pass; the working directory decides.

  /task-management:today    - Generate daily task files
  /task-management:archive  - Archive completed tasks
  /task-management:ideas    - Regenerate ideas.md

To get Claude to reliably use the manage-tasks skill when creating and updating
tasks, add this to a CLAUDE.md in your tasks root: "Use the manage-tasks skill
whenever creating or updating tasks."
```
