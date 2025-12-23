#!/usr/bin/env python3
"""
Date calculation utilities for task-management plugin.
"""

from datetime import datetime, timedelta


def get_week_dates():
    """
    Calculate current week and next week dates.

    Returns dict with:
        today: date string (YYYY-MM-DD)
        today_formatted: formatted date (e.g., "October 3")
        today_weekday: day name (e.g., "Thursday")
        tomorrow: date string (YYYY-MM-DD)
        this_week_start: Monday of current week (YYYY-MM-DD)
        this_week_end: Sunday of current week (YYYY-MM-DD)
        next_week_start: Monday of next week (YYYY-MM-DD)
        next_week_end: Sunday of next week (YYYY-MM-DD)
    """
    today = datetime.now().date()

    # weekday() returns 0=Monday, 6=Sunday
    current_weekday = today.weekday()

    # Calculate this week's Monday and Sunday
    this_week_monday = today - timedelta(days=current_weekday)
    this_week_sunday = this_week_monday + timedelta(days=6)

    # Calculate next week's Monday and Sunday
    next_week_monday = this_week_sunday + timedelta(days=1)
    next_week_sunday = next_week_monday + timedelta(days=6)

    # Tomorrow
    tomorrow = today + timedelta(days=1)

    return {
        'today': str(today),
        'today_formatted': today.strftime('%B %-d'),
        'today_weekday': today.strftime('%A'),
        'tomorrow': str(tomorrow),
        'this_week_start': str(this_week_monday),
        'this_week_end': str(this_week_sunday),
        'next_week_start': str(next_week_monday),
        'next_week_end': str(next_week_sunday),
    }
