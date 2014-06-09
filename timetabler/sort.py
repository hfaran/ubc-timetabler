"""This module contains common sorting functions useful for sorting schedules"""

from timetabler.util import DAY_LIST, strtime2num


def sum_latest_daily_morning(schedules):
    """Sort for the latest daily morning"""

    def key(s):
        total = 0
        for day in DAY_LIST:
            acts = s.activities_for_day(day)
            earliest_start_time = strtime2num(min(a.start_time for a in acts))
            total += earliest_start_time
        return total

    return sorted(schedules, key=key, reverse=True)


def least_time_at_school(schedules):
    def key(s):
        total = 0
        for day in DAY_LIST:
            acts = s.activities_for_day(day)
            earliest_start_time = strtime2num(min(a.start_time for a in acts))
            latest_end_time = strtime2num(max(a.end_time for a in acts))
            time_at_school = latest_end_time - earliest_start_time
            total += time_at_school
        return total

    return sorted(schedules, key=key)
