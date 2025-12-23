#!/usr/bin/env python3
"""
CLI utility to display current and next week dates.
"""

from dates import get_week_dates

dates = get_week_dates()

print(f"Today: {dates['today_weekday']}, {dates['today_formatted']} ({dates['today']})")
print()
print("This Week:")
print(f"  Monday:    {dates['this_week_start']}")
print(f"  Sunday:    {dates['this_week_end']}")
print(f"  Tomorrow:  {dates['tomorrow']}")
print()
print("Next Week:")
print(f"  Monday:    {dates['next_week_start']}")
print(f"  Sunday:    {dates['next_week_end']}")
