from itertools import combinations, chain, ifilter

from timetabler.ssc import SSCConnection
from timetabler.util import check_equal, all_unique
from timetabler.schedule import Schedule


DEBUG = True


class Scheduler(object):
    def __init__(self, courses, session="2014W", terms=(1, 2), refresh=False):
        """Schedule

        :type  courses: list
        :param courses: ["CPSC 304", ...]
        :type  session: str|unicode
        :param session: Session you want to schedule for
        :type  terms: tuple|list
        :param terms: List of terms you want to schedule courses in;
            i.e., [1] for only first term, [1, 2] for whole session etc.
        :param refresh: Invalidate all cached data for relevant courses
        """
        self.ssc_conn = SSCConnection()
        self.courses = {c: self.ssc_conn.get_course(c, session, refresh=refresh)
                        for c in courses}
        self.terms = terms
        self.session = session

    ##################
    # Public Methods #
    ##################

    def generate_schedules(self):
        """Generate valid schedules"""
        # TODO: Use a legit scheduling algorithm and not brute force?
        schedules_by_course = {}
        for name, course in self.courses.items():
            acts = course.activities
            r = sum(c[1] for c in course.num_section_constraints)
            combs = combinations(acts, r)
            # Makes sure:
            # * num_section_constraints from Course are met
            # * all activities are in terms that we want (according to self.terms)
            # * all activities themselves are in the same term
            # * no activities are included that are Full/Blocked
            # * all constraints from the course are satisfied
            filter_func = lambda combo: all([
                all(
                    sum(int(isinstance(act, constraint[0])) for act in combo) == constraint[1]
                    for constraint in course.num_section_constraints
                ),
                all(act.term in self.terms for act in combo),
                check_equal([act.term for act in combo]),
                all(a.status not in [u"Full", u"Blocked"] for a in combo),
                all(c(combo) for c in course.constraints)
            ])
            filtered_combs = ifilter(filter_func, combs)
            # Do non-lazy list() to actually create and set schedules for course; up until this
            #   this point, everything has been lazy for performance
            schedules_by_course[name] = list(filtered_combs)

        all_scheds = combinations(chain.from_iterable(schedules_by_course.values()),
                                  r=len(schedules_by_course))
        # Makes sure:
        # * Schedules don't have recurring courses
        # * Don't have conflicts
        filter_func = lambda s: all([
            all_unique(a.section for t in s for a in t),
            not self._check_schedule_conflicts(s)
        ])
        filtered_all_scheds = ifilter(filter_func, all_scheds)
        schedules = [Schedule(sched) for sched in filtered_all_scheds]
        if DEBUG: print("Found {} valid schedules.".format(len(schedules)))

        return schedules

    ###################
    # Private Methods #
    ###################

    @classmethod
    def _check_conflict(cls, act1, act2):
        """Checks for a scheduling conflict between two Activity instances"""
        return all([
            # Check time conflict
            act1.start_time < act2.end_time,
            act1.end_time > act2.start_time,
            # Check if they are on the same day(s)
            act1.days & act2.days,  # set intersection
            # Check that they are in the same term
            act1.term == act2.term
        ])

    @classmethod
    def _check_conflicts(cls, current_act, other_acts):
        """Check for scheduling conflicts between ``current_act`` and ``other_acts``

        :type  current_act: Activity
        :type  other_acts: [Activity, ...]
        """
        return any(cls._check_conflict(current_act, other_act) for other_act in other_acts)

    @classmethod
    def _check_schedule_conflicts(cls, schedule):
        """Check for conflicts in ``schedule``"""
        acts = [a for t in schedule for a in t]
        for current_act in acts:
            other_acts = (a for a in acts if a != current_act)
            if cls._check_conflicts(current_act, other_acts):
                return True
        else:
            return False