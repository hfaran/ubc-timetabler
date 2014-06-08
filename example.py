from timetabler.ssc_conn import SSCConnection
s = SSCConnection()
p = s.get_course_page()
print(s.activities_from_page(p))

