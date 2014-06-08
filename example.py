from datetime import datetime

from timetabler.schedule import Schedule


def main():
    s = Schedule(["EECE 353", "CPSC 304", "EECE 381", "GEOG 122"],
                 session="2014W", terms=[2])
    s.courses["GEOG 122"].add_constraint(
        lambda acts: all(a.status not in [u"STT"] for a in acts)
    )
    scheds = s.generate_schedules()


if __name__ == '__main__':
    start_time = datetime.now()
    main()
    print(datetime.now() - start_time)
