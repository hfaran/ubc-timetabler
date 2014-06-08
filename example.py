from datetime import datetime

from timetabler.schedule import Schedule

start_time = datetime.now()

s = Schedule(["EECE 353", "CPSC 304", "EECE 381", "GEOG 122"], terms=[2])
scheds = s.generate_schedules()

print(datetime.now() - start_time)
