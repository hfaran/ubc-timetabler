"""This module contains common sorting functions useful for sorting schedules"""
from __future__ import division

from timetabler.util import DAY_LIST, strtime2num, stddev


def sum_latest_daily_morning(schedules):
    """Sort for the latest daily morning"""

    def key(s):
        total = 0
        num_days = 0
        for day in DAY_LIST:
            acts = s.activities_for_day(day)
            if not acts:
                continue  # It's a free day!
            earliest_start_time = earliest_start(acts)
            total += earliest_start_time
            num_days += 1
        return total/num_days

    return sorted(schedules, key=key, reverse=True)


def least_time_at_school(schedules, commute_hrs=0):
    """Sorts schedules for least time spend at school (including daily commute)

    :type commute_hrs: int or float
    :param commute_hrs: Time in hours for ONE-WAY commute
    """
    def key(s):
        total = 0
        for day in DAY_LIST:
            acts = s.activities_for_day(day)
            if not acts:
                continue  # It's a free day!
            earliest_start_time = earliest_start(acts)
            latest_end_time = latest_end(acts)
            time_at_school = (latest_end_time - earliest_start_time) + \
                             (2 * commute_hrs)
            total += time_at_school
        return total

    return sorted(schedules, key=key)


def even_time_per_day(schedules, commute_hrs=0):
    """Sorts by standard deviation of time at school per day

    As a result, sorting by this gives the most "even" schedule
        in regards to time spent at school every day of the week

    :type commute_hrs: int or float
    :param commute_hrs: Time in hours for ONE-WAY commute
    """

    def key(s):
        time_at_school_week = []
        for day in DAY_LIST:
            acts = s.activities_for_day(day)
            if not acts:
                continue  # It's a free day!
            earliest_start_time = earliest_start(acts)
            latest_end_time = latest_end(acts)
            time_at_school = (latest_end_time - earliest_start_time) + \
                             (2 * commute_hrs)
            time_at_school_week.append(time_at_school)
        return stddev(time_at_school_week)

    return sorted(schedules, key=key)


def free_days(schedules):
    """Optimizes for days off (i.e., no classes on that day)"""
    return sorted(schedules, key=lambda s: sum(1 for day in DAY_LIST if s.activities_for_day(day)))


###########
# Helpers #
###########

def earliest_start(activities):
    return strtime2num(min(a.start_time for a in activities))


def latest_end(activities):
    return strtime2num(max(a.end_time for a in activities))
