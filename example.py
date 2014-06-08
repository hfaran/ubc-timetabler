from timetabler.schedule import Schedule
s = Schedule(["EECE 353", "CPSC 304", "EECE 381"], terms=[2])
scheds = s.generate_schedules()
