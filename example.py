from datetime import datetime

from timetabler.schedule import Schedule
from timetabler.ssc.course import Lecture, Discussion


def main():
    s = Schedule(["EECE 353", "CPSC 304", "EECE 381", "GEOG 122"],
                 session="2014W", terms=[2])
    # STTs are for Vantage College students
    s.courses["GEOG 122"].add_constraint(
        lambda acts: all(a.status not in [u"STT"] for a in acts)
    )
    # Default sections Tutorial (for Vantage)
    s.courses["GEOG 122"].num_section_constraints = [
        (Lecture, 1), (Discussion, 1)
    ]
    return s.generate_schedules()


if __name__ == '__main__':
    start_time = datetime.now()
    scheds = main()
    print(datetime.now() - start_time)
