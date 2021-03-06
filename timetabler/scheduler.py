import logging
from itertools import combinations, ifilter, product

from timetabler.ssc import SSCConnection
from timetabler.util import check_equal, all_unique
from timetabler.schedule import Schedule


class NoActivitiesError(Exception):
    """No activities for given course"""
    def __init__(self, course_name):
        self.course_name = course_name

    def __str__(self):
        return self.course_name


class Scheduler(object):
    def __init__(self, courses, session="2014W", terms=(1, 2),
                 refresh=False, duplicates=True, ssc_conn=None):
        """Schedule

        :type  courses: list|tuple
        :param courses: ["CPSC 304", ...]
        :type  session: str|unicode
        :param session: Session you want to schedule for
        :type  terms: tuple|list
        :param terms: List of terms you want to schedule courses in;
            i.e., [1] for only first term, [1, 2] for whole session etc.
        :param refresh: Invalidate all cached data for relevant courses
        :type ssc_conn: SSCConnection
        """
        self.ssc_conn = SSCConnection() if ssc_conn is None else ssc_conn
        self.courses = {c: self.ssc_conn.get_course(c, session, refresh=refresh,
                                                    duplicates=duplicates)
                        for c in courses}
        self.terms = terms
        self.session = session
        self._constraints = []

    ##################
    # Public Methods #
    ##################

    def generate_schedules(self, bad_statuses=("Full", "Blocked")):
        """Generate valid schedules"""
        schedules_by_course = {}
        for name, course in self.courses.items():
            logging.info("Generating schedules for {} ...".format(name))
            # Courses should have at least one activity
            if not course.activities:
                raise NoActivitiesError(name)
            acts = course.activities
            r = sum(c[1] for c in course.num_section_constraints)
            combs = combinations(acts, r)
            # Makes sure:
            # * num_section_constraints from Course are met
            # * all activities are in terms that we want (according to self.terms)
            # * all activities themselves are in the same term (UNLESS they're multiterm)
            # * no activities are included that are Full/Blocked
            # * all constraints from the course are satisfied
            filter_func = lambda combo: all([
                all(
                    sum(int(isinstance(act, constraint[0])) for act in combo) == constraint[1]
                    for constraint in course.num_section_constraints
                ),
                all(act.term in self.terms for act in combo),
                (check_equal([act.term for act in combo]) or
                 any(act.is_multi_term for act in combo)),
                all(a.status not in bad_statuses for a in combo),
                all(c(combo) for c in course.constraints)
            ])
            filtered_combs = filter(filter_func, combs)
            schedules_by_course[name] = filtered_combs
            logging.info("Schedules for {} generated.".format(name))

        # Get all combinations (so all possible schedules); but we still need to check for conflicts
        all_scheds = self._generate_combinations(schedules_by_course)
        # Makes sure:
        # * Schedules don't have recurring courses
        # * Don't have conflicts
        filter_func = lambda s: all([
            # all_unique(a.section for t in s for a in t),  # This seems to be unnecessary
            not self._check_schedule_conflicts(s)
        ])
        # Now we filter away all schedules that have conflicts
        filtered_all_scheds = ifilter(filter_func, all_scheds)
        logging.info("Generating all valid schedules ...")
        schedules = [Schedule(sched) for sched in filtered_all_scheds]
        # Now we filter away all the schedules that don't obey constraints
        filter_func = lambda s: all(c(s) for c in self._constraints)
        schedules = filter(filter_func, schedules)
        logging.info("Found {} valid schedules.".format(len(schedules)))

        return schedules

    def add_constraint(self, constraint):
        """Add constraint ``constraint`` to list of constraints

        :type  constraint: callable
        :param constraint: A callable that takes a Schedule
            and returns True or False depending on whether
            a constraint is met
        """
        self._constraints.append(constraint)

    ###################
    # Private Methods #
    ###################

    def _generate_combinations(self, scheds_by_course):
        """Generate all possible schedules given ``scheds_by_course``

        :type  scheds_by_course: dict
        :param scheds_by_course: Dictionary of possible schedules by course
        :rtype: list
        :return: Combination of all schedules
        """
        if not scheds_by_course:
            return []

        schedules = list(product(*scheds_by_course.itervalues()))
        return schedules


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
