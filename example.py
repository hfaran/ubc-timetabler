# from timetabler.ssc import SSCConnection
# s = SSCConnection()
# c = s.get_course("EECE 310", "2014W")
from pprint import pprint
from timetabler.schedule import Schedule
s = Schedule(["EECE 353", "CPSC 304", "EECE 381"], terms=[2])
scheds = s.generate_schedules()
#pprint(scheds, indent=4)
