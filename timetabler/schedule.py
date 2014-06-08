from itertools import permutations, chain, ifilter

from timetabler.ssc import SSCConnection
from timetabler.util import check_equal


def check_conflict(act1, act2):
    return act1.start_time < act2.end_time and act1.end_time > act2.start_time


class Schedule(object):
    def __init__(self, courses, session="2014W", terms=(1, 2)):
        """Schedule

        :param courses: ["CPSC 304", ...]
        """
        self.ssc_conn = SSCConnection()
        self.courses = {c: self.ssc_conn.get_course(c, session) for c in courses}
        self.terms = terms
        self.session = session

    def generate_schedules(self):
        """Generate valid schedules"""
        # TODO: Use an actual algorithm and not something that's like n^n

        schedules_by_course = {}
        for name, course in self.courses.items():
            acts = course.labs + course.lectures + course.tutorials
            r = sum(c[1] for c in course.constraints)
            perms = permutations(acts, r)
            # Makes sure:
            # * constraints from Course are met
            # * all activities are in terms that we want (according to self.terms)
            # * all activities themselves are in the same term
            filter_func = lambda combo: all([
                all(
                    sum(int(isinstance(act, constraint[0])) for act in combo) == constraint[1]
                    for constraint in course.constraints
                ),
                all(act.term in self.terms for act in combo),
                check_equal([act.term for act in combo])
            ])
            filtered_perms = set(ifilter(filter_func, perms))
            schedules_by_course[name] = filtered_perms

        all_scheds = permutations(chain(*schedules_by_course.values()), r=len(schedules_by_course))
        print len(list(all_scheds))



        return schedules_by_course
