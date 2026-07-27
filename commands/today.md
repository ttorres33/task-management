---
description: Generate today.md, this-week.md, and next-week.md files
---

# today

Generate `today.md`, `this-week.md`, and `next-week.md`.

## Process

### Step 1: Generate Daily Task Files

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-daily-files.py
```

This resolves which task system to act on from the current working directory, then:

1. Normalizes dates in all task files
2. Calculates this week's and next week's dates
3. Archives completed tasks (moves them to `completed/`)
4. Generates all three files

It prints the resolved root before writing anything — include that line in your
summary so it is always clear which system was touched.

### Step 2: Research Digest (Optional)

Ask the plugin what this root is allowed to do. Do not check the config yourself, and
do not look for the research-system plugin yourself — this command resolves it:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/show-config.py
```

Read the `research:` line from the output and act on it:

- **`research: off`** — stop here. Nothing to do.
- **`research: generate`** — run `/research-system:generate-research-digest`, then add
  the Research section as described below.
- **`research: link-only`** — do **not** run the digest command; this machine does not
  have the research-system plugin. If `research_digest_exists: yes`, add the Research
  section anyway, linking the existing digest. If `no`, stop here.

If the output includes a `NOTICE:` block, surface it to the user verbatim. It means
the integration is enabled but the plugin was not detected, which is worth knowing
rather than silently working around.

To add the Research section, append it to `today.md` after the "In Progress Ideas"
section, linking the path from the `research_digest:` line and using the format from
the `link_format:` line.

## Example Output - today.md

```markdown
---
date: 2026-03-11
---
# Today - Wednesday, March 11

## Overdue
- [ ] [[old-task]] (due: 2026-03-06)
- [ ] [[another-overdue]] (due: 2026-03-09)

## Due Today
- [ ] [[give-dog-flea-medicine]]
- [ ] [[bbc-sale]]

## In Progress Ideas
- [[next-ai-project]]
- [[course-redesign]]

## Research
- [ ] [Review today's research digest](../Research/daily-digests/2026-03-11.md)
```

## Example Output - this-week.md

```markdown
---
week_start: 2026-03-09
week_end: 2026-03-15
---
# This Week - Week ending March 15

## Thursday, March 12
- [ ] [[client-meeting]]
```

## Example Output - next-week.md

```markdown
---
week_start: 2026-03-16
week_end: 2026-03-22
---
# Next Week - Week of March 16

## Monday, March 16
- [ ] [[quarterly-planning]]
```
