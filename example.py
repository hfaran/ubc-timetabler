from datetime import datetime

from timetabler.scheduler import Scheduler
from timetabler.ssc.course import Lecture, Discussion
from timetabler import sort


def main():
    courses = ["EECE 353", "CPSC 304", "EECE 381", "CPSC 322", "GEOG 122"]
    s = Scheduler(courses, session="2014W", terms=[2], refresh=False)

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

    return s.generate_schedules()


if __name__ == '__main__':
    # Setup logging
    import logging
    import sys

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Get schedules (time operation)
    start_time = datetime.now()
    scheds = main()
    print("There were {} valid schedules found.".format(len(scheds)))
    print("This took {} to calculate.".format(
        datetime.now() - start_time
    ))
    # Sort and draw
    scheds = sort.sum_latest_daily_morning(scheds)
    scheds = sort.least_time_at_school(scheds)

    for sched in scheds:
        sched.draw(term=2)
        raw_input("Press ENTER to display the next schedule...")
