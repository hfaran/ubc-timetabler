from datetime import datetime
from itertools import combinations

from timetabler.scheduler import Scheduler
from timetabler.ssc.course import Lecture, Discussion
from timetabler import sort, util
from timetabler.sort import earliest_start  # Helper function (should probably be in util)


COMMUTE_HOURS = 1.75


def main():
    required = ("EECE 353", "CPSC 304", "EECE 381")
    opt = [
        "CPSC 420",
        # "GEOG 122",  # Taking CIVL200 in T1, so don't need this anymore
        "EECE 450",
        "CPSC 322",
        "CPSC 317",
        # "EECE 411",  # If this is selected, it and CPSC317 can be the only, b/c 317 is a co-req
    ]
    combs = combinations(opt, r=1)

    schedules = []
    for courses in [required + comb for comb in combs]:
        s = Scheduler(courses, session="2014W", terms=[2], refresh=True)
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
        schedules.extend(s.generate_schedules())
    return schedules


if __name__ == '__main__':
    # Setup logging
    util.setup_root_logger()

    # Get schedules (time operation)
    start_time = datetime.now()
    scheds = main()
    print("There were {} valid schedules found.".format(len(scheds)))
    print("This took {} to calculate.".format(
        datetime.now() - start_time
    ))
    # Sort and draw
    scheds = sort.even_time_per_day(scheds, commute_hrs=COMMUTE_HOURS)
    scheds = sort.sum_latest_daily_morning(scheds)
    scheds = sort.least_time_at_school(scheds, commute_hrs=COMMUTE_HOURS)
    scheds = sort.free_days(scheds)
    for sched in scheds:
        sched.draw(term=2, draw_location="browser")
        raw_input("Press ENTER to display the next schedule...")
