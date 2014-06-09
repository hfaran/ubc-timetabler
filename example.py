from datetime import datetime

from timetabler.scheduler import Scheduler
from timetabler.ssc.course import Lecture, Discussion


def main():
    s = Scheduler(["EECE 353", "CPSC 304", "EECE 381", "CPSC 317", "GEOG 122"],
                 session="2014W", terms=[2], refresh=False)
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
    # Sort so that the sum of starting times for courses
    #   throughout the week are greatest
    key = lambda s: sum(int(a.start_time.replace(":", "")) for a in s.activities)
    scheds = sorted(
        scheds,
        key=key,
        reverse=True
    )
    print("There were {} valid schedules found.".format(len(scheds)))
    print("Schedule with latest starting times...")
    print("This took {} to calculate.".format(
        datetime.now() - start_time
    ))
    for sched in scheds:
        sched.draw(term=2)
        raw_input("Press ENTER to display the next schedule...")
