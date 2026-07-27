---
description: Generate ideas.md, listing ideas by status
---

# ideas

Generate `ideas.md`: links to ideas grouped by status.

## Process

Run the script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-ideas.py
```

The script resolves which task system to act on from the current working directory,
then writes `ideas.md` into that root. It prints the resolved root before writing
anything — include that line in your summary so it is always clear which system was
touched.

Report the counts from the script's output. Do not add descriptions or summaries of
the individual ideas: this file is a generated index, and anything written here is
overwritten on the next run.

## What is included

- `status: in progress` (or `in-progress`) → **In Progress**
- `status: noodling` → **Noodling**

Ideas with `status: someday`, and ideas with no status field, are deliberately
excluded. This file answers "what am I actively working on or actively exploring",
not "what ideas exist".

## Example Output

```markdown
# Ideas

## In Progress
- [[story-based-customer-interviews-course]]
- [[leadership-plan]]

## Noodling
- [[just-now-possible-podcast]]
- [[deep-dive-case-studies]]
```

Both headings always appear, even when a section is empty.
