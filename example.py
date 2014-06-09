import json
from datetime import datetime

from timetabler.schedule import Scheduler
from timetabler.ssc.course import Lecture, Discussion


def main():
    s = Scheduler(["EECE 353", "CPSC 304", "EECE 381", "GEOG 122"],
                 session="2014W", terms=[2])
    # STTs are for Vantage College students
    s.courses["GEOG 122"].add_constraint(
        lambda acts: all(a.status not in [u"STT"] for a in acts)
    )
    # Default sections contained a Tutorial but that is for Vantage
    #   students, so removing that and only setting Lecture and Discussion
    s.courses["GEOG 122"].num_section_constraints = [
        (Lecture, 1), (Discussion, 1)
    ]
    return s.generate_schedules()


if __name__ == '__main__':
    start_time = datetime.now()
    scheds = main()
    # Unwrap activities out of course-specific tuples
    scheds = [[act for crs in sched for act in crs]
               for sched in scheds]
    # Sort so that the sum of starting times for courses
    #   throughout the week are greatest
    scheds = sorted(
        scheds,
        key=lambda s: sum(int(a.start_time.replace(":", "")) for a in s),
        reverse=True
    )
    print("Schedule with latest starting times (sum): {}".format(
        json.dumps([repr(s) for s in scheds[0]], indent=4)
    ))
    print("This took {} to calculate.".format(
        datetime.now() - start_time
    ))
