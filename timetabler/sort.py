"""This module contains common sorting functions useful for sorting schedules"""

def sum_latest_start_times(schedules):
    """Sort so that the sum of starting times for courses throughout the week are greatest"""
    key = lambda s: sum(int(a.start_time.replace(":", "")) for a in s.activities)
    return sorted(
        schedules,
        key=key,
        reverse=True
    )
