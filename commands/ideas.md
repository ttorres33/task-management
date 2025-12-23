---
description: Generate a list of ideas organized by status
---

# ideas

Generate a list of ideas organized by status.

## Process

1. Use Grep to search `ideas/` folder for ideas by status:
   - Search for `^status: in progress` → list in "In Progress" section
   - Search for `^status: noodling` → list in "Noodling" section
2. Generate `ideas.md` with:
   - Heading: `# Ideas`
   - "In Progress" section with links to in-progress ideas
   - "Noodling" section with links to noodling ideas
   - Use link format from `links.format` in config

## Important

- Only shows ideas with `status: in progress` or `status: noodling`
- Ideas with `status: someday` are not included
- Ideas without status field are not included
- Helps you see what you're actively working on vs exploring

## Example Output

```markdown
# Ideas

## In Progress
- [[story-based-customer-interviews-course]]
- [[leadership-plan]]
- [[vistaly-implementation]]

## Noodling
- [[just-now-possible-podcast]]
- [[deep-dive-case-studies]]
- [[sales-pitch]]
```
