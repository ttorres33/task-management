---
description: Show plugin documentation and usage
allowed-tools: [Read, AskUserQuestion]
model: haiku
---

# About Task Management

Help the user learn about the Task Management plugin interactively.

## Step 1: Read the README

Read `${CLAUDE_PLUGIN_ROOT}/README.md` to understand the full documentation.

## Step 2: Present Overview and Ask What They Want to Learn

Present a brief welcome and list the main topics:

```
Welcome to Task Management! This plugin helps you manage markdown-based tasks with daily/weekly views.

What would you like to learn about?
```

Use AskUserQuestion with these options:
- **Quick Start** - How to install and get started
- **Commands** - List of all available slash commands
- **Task Format** - How to structure task files
- **Configuration** - How to configure paths and folders
- **Full Documentation** - Show the complete README

## Step 3: Show Relevant Section

Extract and display the relevant section from the README you read in Step 1. Do NOT hardcode content - always pull from the README so users see the latest documentation.

Based on the user's choice, find and display:

- **Quick Start**: The "## Installation" section plus the first paragraph about running setup
- **Commands**: The "## Commands" section from README
- **Task Format**: The "## Task File Format" section from README
- **Configuration**: The "## Configuration" section from README
- **Full Documentation**: Output the entire README

## Step 4: Offer to Continue

After showing the requested section, ask if they want to learn about another topic or if they have questions.
