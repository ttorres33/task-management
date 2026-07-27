# task-management

A Claude Code plugin for markdown-based task management. Generates daily/weekly task
views, archives completed tasks, and tracks ideas.

Supports any number of task systems on one machine — a work system and a household
one, for example — including systems shared with another person through a synced
Obsidian vault.

## Installation

```bash
claude plugins add teresa-torres-plugins/task-management
```

Then, from inside the folder you want to use as your tasks root:

```
/task-management:setup
```

No packages to install. The plugin runs on the Python 3 that ships with macOS and
Linux, with nothing added.

## Configuration

Configuration comes in two shapes. The normal one is a **marker file** in each tasks
root. The **global config** is a fallback for when you are working outside every tasks
root.

### The marker file

Each tasks root contains `task-management-root.md`. This file both marks the folder as
a task system and holds that system's settings:

```markdown
---
task_management_root: true
name: work
folders:
  tasks: "tasks"
  ideas: "ideas"
  templates: "templates"
  memories: "memories"
  bugs: "bugs"
  completed: "completed"
  import: "import"
links:
  format: "obsidian"
integrations:
  research_system: false
  research_digest_path: "../Research/daily-digests/{date}.md"
---
# Task Management Root

Marks this folder as a task-management root. Safe to edit; do not rename or move.
```

- **`task_management_root: true`** — required. It is what makes the file a marker
  rather than an ordinary note. A file with the marker's filename but without this key
  is ignored, silently — an Obsidian vault could plausibly hold a note called
  `task-management-root.md`, and resolving to it would mean writing generated files
  into the wrong folder. If you create a marker by hand and forget this line, the
  error will name the file and tell you what is missing.
- **`name`** — optional label. It names the root in command output and defaults to the
  folder name. Worth setting when you have more than one system, so they are tellable
  apart at a glance.
- **`folders`** — optional. Omit it to accept the defaults shown above. Include it in
  full if this root uses custom folder names: settings never merge, so a marker
  supplies either the whole set or none of it.
- **`links.format`** — `obsidian` for `[[wiki-links]]`, or `markdown` for
  `[text](path)`. Choose `obsidian` if you read these files in Obsidian.
- **`integrations`** — see [Research System Integration](#research-system-integration).

The marker contains **no absolute paths**. The root is implied by the file's own
location, so the same file works on a second device, or under a different user's home
directory, unchanged.

It is a Markdown file rather than a dotfile or a `.yaml` file because Obsidian Sync
excludes hidden files and treats `.yaml` as an optional file type. Markdown always
syncs. That is what lets a marker travel to a second device or to someone you share a
vault with.

### The global config

`~/.claude/task-management-config/config.yaml` answers one question: *which task
system when the working directory is outside every tasks root?*

```yaml
default_root: "/Users/you/Vaults/Work/Tasks"
```

The older full-settings shape still works and needs no migration:

```yaml
paths:
  tasks_root: "/Users/you/Vaults/Work/Tasks"

folders:
  tasks: "tasks"
  # ...

links:
  format: "obsidian"

integrations:
  research_system: false
```

If a root has no marker of its own, it uses the global config's settings.

### Which system a command acts on

Resolution order:

| | Where it looks | Result |
|---|---|---|
| 1 | `$TASK_MANAGEMENT_ROOT` | that folder, for this one run |
| 2 | `task-management-root.md` in the current folder or any folder above it | that folder is the root |
| 3 | `task-management-root.md` in an immediate subfolder | that subfolder is the root |
| 4 | `default_root` (or `paths.tasks_root`) in the global config | that folder is the root |
| 5 | nothing found | an error explaining how to configure one |

In practice: **the directory you launch Claude from decides.** Start Claude inside
your work tasks folder and you get the work system; start it inside the household
vault and you get the household one. There are no flags to pass.

Step 3 matters when you open Claude at a *vault* root rather than inside the tasks
folder — which is the most likely thing to do with a vault someone shared with you.

Every command prints the root it resolved before writing anything:

```
Tasks root: /Users/you/Vaults/Work/Tasks  [work, via marker]
```

To see what would be used without running anything, ask Claude to run
`show-config.py` from the plugin, or use `/task-management:about`.

## Running more than one task system

You have one system working and want a second — household tasks alongside work tasks,
say.

1. **Create the new root** and its folders (`tasks/`, `ideas/`, `templates/`,
   `memories/`, `bugs/`, `completed/`, `import/`). See
   [File Structure](#file-structure).

2. **Run `/task-management:setup` from inside the new root**, or write
   `task-management-root.md` there by hand using the schema above. It needs
   `task_management_root: true` to count as a marker at all; give it a `name` that
   tells the two systems apart, since the name appears in every command's output.

   If the new root uses custom folder names, its marker must list all of them.
   Settings do not merge; the new root will not inherit `folders` from your first
   system or from the global config.

3. **Switch between them by launching Claude from inside the one you want.** No flags,
   no arguments. If you keep a personalized `/today` or other project commands in
   `.claude/commands/` inside one root, they only load in that root — which gives you
   per-system behavior for free.

4. **Decide what happens outside both.** Running a command from, say, a code project
   falls through to `default_root` in the global config. Set it to whichever system
   should be the fallback. If you would rather have no fallback at all, leave the
   global config out entirely and you will get an error naming your options instead of
   a silent write to the wrong system.

5. **Verify** by running any command from inside the new root and reading its
   resolved-root line.

Settings are per-root. Two systems can differ in link format, folder names, and
research integration.

## Sharing a task system with another person

A task system inside a synced vault works for two people with no configuration on the
second person's side.

**Prerequisite:** the tasks root sits inside a vault on Obsidian Sync (a paid feature),
or any other mechanism that syncs ordinary files. This is the one hard requirement.

**Setup:** both people install the plugin. Whoever owns the vault runs
`/task-management:setup` in the tasks root once. The second person needs no
configuration of any kind — the marker travels with the vault and holds no absolute
paths, so it resolves correctly under a different home directory and username. The
second person just opens Claude in the vault (or in the tasks folder) and runs
commands.

Things worth agreeing on up front:

- **All four generated files are shared.** `today.md`, `this-week.md`, `next-week.md`,
  and `ideas.md` are written into the root, so both people see the same generated
  views and the last person to run `/today` overwrites the previous output. Two people
  running it the same morning will produce sync conflicts on those files. Either have
  one person own daily generation, or treat the files as a shared snapshot rather than
  a personal one.

- **Archiving moves files for everyone.** `/task-management:archive` relocates
  completed tasks from `tasks/` to `completed/`, and that move syncs. Nobody should be
  surprised when a task disappears from their view.

- **Personalizations do not travel.** Anything under `.claude/` in the vault — project
  commands, skills, settings — is hidden and therefore not synced. Each person's
  customizations stay local to their machine.

- **Recommended settings:** `links.format: obsidian`, since a shared vault is by
  definition being read in Obsidian, and `research_system: false`, since the other
  person will not have the research-system plugin and the digest is personal.

## Commands

Every command resolves its task system from the working directory and reports the root
it acted on.

### `/task-management:setup`

Configure a task system in a folder by writing its marker file. Additive: running it in
a second folder adds a second system and leaves the first alone.

### `/task-management:today`

Generate the daily files:
- `today.md` — overdue tasks, tasks due today, in-progress ideas, research
- `this-week.md` — tasks for the remaining days this week
- `next-week.md` — tasks for next week

Also normalizes date formats and archives completed tasks.

### `/task-management:this-week`

Regenerate `this-week.md` only.

### `/task-management:next-week`

Regenerate `next-week.md` only.

### `/task-management:ideas`

Regenerate `ideas.md`: links to ideas grouped under **In Progress** and **Noodling**.
Ideas with `status: someday`, and ideas with no status, are excluded.

This command writes the file rather than describing its contents. Anything you add to
`ideas.md` by hand is overwritten on the next run.

### `/task-management:archive`

Move completed one-time tasks from `tasks/` to `completed/`. Recurring tasks are never
archived.

### `/task-management:clean-imports`

Move reviewed files from `import/` into the folder matching their `type:` field.

### `/task-management:about`

Show this documentation interactively.

## Research System Integration

If you use the [research-system](https://github.com/ttorres33/research-system) plugin,
setting `integrations.research_system: true` adds a research digest section to
`/today`.

The flag controls whether the digest is used at all. Whether it is *generated*
additionally depends on the research-system plugin being installed on that machine:

| flag | research-system installed | behavior |
|---|---|---|
| `true` | yes | generate a new digest, then link it |
| `true` | no | link an existing digest, generate nothing |
| `false` | — | no research section |

The split exists because the marker file syncs, and a synced file cannot carry a
per-device answer. A second device that receives digests through vault sync links them
without regenerating them.

`integrations.research_digest_path` is a root-relative template with a `{date}`
placeholder, defaulting to `"../Research/daily-digests/{date}.md"`. It is only ever
read, never written.

## Skills

### `manage-tasks`

Task conventions and file organization rules. Claude uses this skill when creating or
modifying task files to keep formatting consistent.

To get Claude to use it reliably, put this in a `CLAUDE.md` in your tasks root: "Use
the manage-tasks skill whenever creating or updating tasks."

## File Structure

Each tasks root looks like this:

```
Tasks/
├── task-management-root.md   # Marks this folder as a task system
├── tasks/          # Items with due dates
├── ideas/          # Projects without due dates
├── templates/      # Reusable task templates
├── memories/       # Reference items (not actionable)
├── bugs/           # Issues to fix
├── completed/      # Archived one-time tasks
├── import/         # Staging area for triage
├── today.md        # Generated
├── this-week.md    # Generated
├── next-week.md    # Generated
└── ideas.md        # Generated
```

## Task File Format

Each task is a markdown file with YAML frontmatter:

```yaml
---
type: task
due: 2026-03-11
tags: [project, urgent]
---
# Task Title

Task content here.
```

### Fields

**Required:**
- `type` — task, idea, template, memory, or bug

**Optional:**
- `due: YYYY-MM-DD` — due date (required for tasks)
- `completed: YYYY-MM-DD` — completion date
- `recurrence: weekly | biweekly | monthly | quarterly | yearly`
- `status: in-progress | noodling | someday` — for ideas only
- `tags: [tag1, tag2]` — categorization

Dates written as `3/11/2026` or `2026-3-11` are normalized to `2026-03-11` on the next
`/today` run.

## Upgrading from 0.3.0

If you wrote a marker file against 0.3.0, add one line to it:

```yaml
task_management_root: true
```

0.3.0 treated any `task-management-root.md` carrying a `name:` key as a marker. That
was too weak: `name:` is common enough that an ordinary note could carry it by
coincidence, and resolving to the wrong folder means writing generated files into it.
0.3.1 keys on a dedicated flag instead, and `name` became an optional label.

If you skip this, commands report that no task system was found — and the error names
the file and the missing line.

## Upgrading from 0.2.x

Nothing to do. An existing global config keeps working exactly as before, and no
migration is required.

Three things changed:

1. **The plugin no longer needs PyYAML.** If commands were failing with
   `ModuleNotFoundError: No module named 'yaml'`, they now work.

2. **`/task-management:ideas` writes `ideas.md`** instead of describing what it found.
   Its output is a plain index — links grouped by status, no per-idea descriptions.

3. **Commands require a configured root.** If you never ran `/task-management:setup`
   and relied on running commands from inside your tasks folder, you now get an error
   explaining how to configure one. Run `/task-management:setup` and you are done.

## Development

See [docs/test.md](docs/test.md) for the test suite.

## License

MIT
