#!/usr/bin/env python2

from datetime import datetime
from itertools import combinations

from timetabler.scheduler import Scheduler
from timetabler.ssc.course import Lecture, Discussion, Lab
from timetabler import sort, util
from timetabler.sort import earliest_start  # Helper function (should probably be in util)


COMMUTE_HOURS = 1.75
SESSION = "2015W"
TERMS = (1, 2)


def main():
    required = (
        "CPEN 321",  # Software Engineering
        "CPEN 421",  # Software Project Management
        "CPEN 422",  # Software Testing and Analysis
        # "APSC 486",  # NVD
        "CPEN 492",  # CPEN Capstone
        "CPEN 481",  # Economic Analysis of Engineering Projects
        "APSC 450"  # Professional Engineering Practice
    )
    opt = [
        "CPEN 442",  # Introduction to Computer Security
        "CPSC 312",  # Functional programming
        "CPSC 340",  # Machine Learning and Data Mining
    ]
    num_required_from_opt = 2
    combs = list(combinations(opt, r=num_required_from_opt))

    schedules = []
    for courses in [required + comb for comb in combs]:
        s = Scheduler(courses, session=SESSION, terms=TERMS, refresh=False)
        # I don't want any classes that start before 9:00AM
        s.add_constraint(lambda sched: earliest_start(sched.activities) >= 9)
        # Add GEOG122 constraints if we need to
        if "GEOG 122" in courses:
            # STTs are for Vantage College students
            s.courses["GEOG 122"].add_constraint(
                lambda acts: all(a.status not in [u"STT"] for a in acts)
            )
            # Default sections contained a Tutorial but that is for Vantage
            # students, so removing that and only setting Lecture and Discussion
            s.courses["GEOG 122"].num_section_constraints = [
                (Lecture, 1), (Discussion, 1)
            ]

        # Add statuses for courses that shouldn't be considered
        bad_statuses = (
            "Full",
            # "Blocked",
        )
        schedules.extend(s.generate_schedules(bad_statuses=bad_statuses))
    return schedules


if __name__ == '__main__':
    # Setup logging
    util.setup_root_logger('ERROR')

    # Get schedules (time operation)
    start_time = datetime.now()
    scheds = main()
    print("There were {} valid schedules found.".format(len(scheds)))
    print("This took {} to calculate.".format(
        datetime.now() - start_time
    ))
    # Sort and draw
    scheds = sort.free_days(scheds)
    scheds = sort.even_time_per_day(scheds, commute_hrs=COMMUTE_HOURS)
    scheds = sort.sum_latest_daily_morning(scheds)
    scheds = sort.least_time_at_school(scheds, commute_hrs=COMMUTE_HOURS)
    for i, sched in enumerate(scheds):
        sched.draw(terms=TERMS, draw_location="terminal")
        if i < len(scheds) - 1:
            raw_input("Press ENTER to display the next schedule...")
