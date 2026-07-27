#!/usr/bin/env python3
"""
Rendering for the four generated files: today.md, this-week.md, next-week.md, ideas.md.

this-week and next-week used to be two near-identical functions -- same day loop,
same per-day block, differing only in heading text, date range, and an empty-week
case. Splitting them into separate scripts as-written would have copied that
duplication into separate files, so the shared shape lives in render_week().

These functions return strings and never touch the filesystem, which is what makes
them testable against a captured baseline.
"""

from datetime import datetime

import taskquery
from dates import format_date_header, generate_days_between

DATE_FMT = "%Y-%m-%d"


def render_today(dates):
    """
    Render today.md. Returns (content, counts).

    `counts` carries the overdue / due-today / research / ideas totals so the caller
    can report them without re-running the queries.
    """
    today = dates["today"]
    today_datetime = datetime.strptime(today, DATE_FMT)

    overdue = taskquery.get_overdue_tasks(today)
    due_today = taskquery.get_tasks_for_date(today)
    research = taskquery.get_research_tasks()
    ideas = taskquery.get_in_progress_ideas()

    content = f"---\ndate: {today}\n---\n"
    content += f"# Today - {format_date_header(today_datetime)}\n\n"

    if overdue:
        content += "## Overdue\n"
        for filename, due_date in overdue:
            content += f"- [ ] {taskquery.format_link(filename, 'tasks')} (due: {due_date})\n"
        content += "\n"

    content += "## Due Today\n"
    for filename in due_today:
        content += f"- [ ] {taskquery.format_link(filename, 'tasks')}\n"
    content += "\n"

    if ideas:
        content += "## In Progress Ideas\n"
        for filename in ideas:
            content += f"- {taskquery.format_link(filename, 'ideas')}\n"
        content += "\n"

    if research:
        content += "## Research\n"
        for filename in research:
            content += f"- [ ] {taskquery.format_link(filename, 'tasks')}\n"

    counts = {
        "overdue": len(overdue),
        "due_today": len(due_today),
        "research": len(research),
        "ideas": len(ideas),
    }
    return content, counts


def render_week(days, week_start, week_end, heading, empty_message=None):
    """
    Render a week view. Returns (content, task_count).

    `empty_message` is emitted only when `days` itself is empty -- the "today is
    Sunday, nothing left this week" case. A week that has days but no tasks on any
    of them renders as just the heading, which is what the previous code did.
    """
    content = f"---\nweek_start: {week_start}\nweek_end: {week_end}\n---\n"
    content += f"# {heading}\n\n"

    if not days:
        if empty_message:
            content += empty_message
        return content, 0

    total = 0
    for day in days:
        tasks = taskquery.get_tasks_for_date(day.strftime(DATE_FMT))
        if not tasks:
            continue
        content += f"## {format_date_header(day)}\n"
        for filename in tasks:
            content += f"- [ ] {taskquery.format_link(filename, 'tasks')}\n"
        content += "\n"
        total += len(tasks)

    return content, total


def render_this_week(dates):
    """Render this-week.md: tomorrow through Sunday. Returns (content, count, days)."""
    tomorrow = dates["tomorrow"]
    week_end = dates["this_week_end"]

    week_end_date = datetime.strptime(week_end, DATE_FMT)
    heading = f"This Week - Week ending {week_end_date.strftime('%B %-d')}"

    if datetime.strptime(tomorrow, DATE_FMT) > week_end_date:
        days = []
    else:
        days = generate_days_between(tomorrow, week_end)

    content, total = render_week(
        days, dates["this_week_start"], week_end, heading,
        empty_message="No tasks remaining this week.\n",
    )
    return content, total, days


def render_next_week(dates):
    """Render next-week.md: next Monday through Sunday. Returns (content, count, days)."""
    week_start = dates["next_week_start"]
    week_end = dates["next_week_end"]

    week_start_date = datetime.strptime(week_start, DATE_FMT)
    heading = f"Next Week - Week of {week_start_date.strftime('%B %-d')}"

    days = generate_days_between(week_start, week_end)
    content, total = render_week(days, week_start, week_end, heading)
    return content, total, days


def render_ideas():
    """
    Render ideas.md: links grouped by status. Returns (content, counts).

    Both headings are always emitted, even when empty. This is a standalone report
    rather than a daily view, and an empty "Noodling" section is information.

    Only 'in progress' and 'noodling' appear. 'someday' and unstatused ideas are
    deliberately excluded -- this file answers "what am I actively working on or
    actively exploring", not "what ideas exist".
    """
    in_progress = taskquery.get_ideas_by_status("in progress")
    noodling = taskquery.get_ideas_by_status("noodling")

    content = "# Ideas\n\n"

    content += "## In Progress\n"
    for filename in in_progress:
        content += f"- {taskquery.format_link(filename, 'ideas')}\n"
    content += "\n"

    content += "## Noodling\n"
    for filename in noodling:
        content += f"- {taskquery.format_link(filename, 'ideas')}\n"

    return content, {"in_progress": len(in_progress), "noodling": len(noodling)}
