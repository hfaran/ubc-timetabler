from timetabler.ssc import SSCConnection


class Schedule(object):
    def __init__(self, courses, term=2, sessyr=2014, sesscd="W"):
        """Schedule

        :param courses: ["CPSC 304", ...]
        """
        self.courses = courses
        self.term = str(term)
        self.sessyr = str(sessyr)
        self.sesscd = sesscd
        self.ssc_conn = SSCConnection()
