import itertools
import logging
import re


class Course(object):
    def __init__(self, dept, number, title,
                 lectures=None, labs=None, tutorials=None, discussions=None,
                 duplicates=True):
        self.dept = dept
        self.number = number
        self.title = title
        self.lectures = lectures if lectures else []
        assert all(isinstance(l, Lecture) for l in self.lectures)
        self.labs = self.skip_duplicates(labs, duplicates) if labs else []
        assert all(isinstance(l, Lab) for l in self.labs)
        self.tutorials = self.skip_duplicates(tutorials, duplicates) if tutorials else []
        assert all(isinstance(l, Tutorial) for l in self.tutorials)
        self.discussions = self.skip_duplicates(discussions, duplicates) if discussions else []
        assert all(isinstance(l, Discussion) for l in self.discussions)

        collection_activities = [
            self.labs, self.lectures,
            self.tutorials, self.discussions
        ]
        # Set course for each activity
        for activity in itertools.chain(*collection_activities):
            activity.course = self
        self._num_section_constraints = [
            (l[0].__class__, (2 if l[0].is_multi_term else 1))
            for l in collection_activities
            if l
        ]
        self._constraints = []

    def skip_duplicates(self, activities, duplicates=True):
        """Skip variations of the same activities that occur at the same time

        :type  activities: list
        :param activities: [Activity]
        :type  duplicates: bool
        :param duplicates: If this is set, variant activities are not filtered
        :rtype: list
        :return: Activities with unique times
        """
        if duplicates:
            return activities
        non_duplicate_activities = []
        while activities:
            activity = activities.pop()
            pattern = activity.section[:-1] + '\w'
            if activities:
                for l in activities:
                    if re.search(pattern, l.section) and \
                        l.term == activity.term and \
                        l.days == activity.days and \
                        l.start_time == activity.start_time and \
                        l.end_time == activity.end_time:
                            logging.warning('\nDuplicates: ' + activity.section + ', ' + l.section)
                            break
                else:
                    non_duplicate_activities.append(activity)
            else:
                non_duplicate_activities.append(activity)
        return non_duplicate_activities

    @property
    def constraints(self):
        return self._constraints

    def add_constraint(self, constraint):
        """Add constraint ``constraint`` to list of constraints

        :type  constraint: callable
        :param constraint: A callable that takes a (single) list of
            Activity subtype instances that belong to this Course that we want
            to return True for in order to consider that list of
            Activities valid.
        """
        self._constraints.append(constraint)

    @property
    def num_section_constraints(self):
        """List of tuples, where each tuple is
            (Activity subtype, # of sections of that activity needed)
        """
        return self._num_section_constraints

    @num_section_constraints.setter
    def num_section_constraints(self, value):
        self._num_section_constraints = value

    @property
    def activities(self):
        return self.lectures + self.tutorials + self.labs + self.discussions


class Activity(object):
    def __init__(self, status, section, term, days, start_time, end_time,
                 comments, is_multi_term):
        self.status = status  # e.g, "Restricted"
        self.section = section  # e.g., "EECE 310 L1A"
        self.term = int(term)  # e.g., 2
        self.days = set(days.split())  # e.g., {"Mon", "Wed"}
        # zfilling is important so that > and < comparison operators work
        self.start_time = start_time.zfill(5)  # e.g., "13:00"
        self.end_time = end_time.zfill(5)
        self.comments = comments
        self.is_multi_term = is_multi_term  # boolean

        self._course = None  # Reference to Course object that has this activity

    @property
    def course(self):
        return self._course

    @course.setter
    def course(self, value):
        self._course = value

    def __repr__(self):
        return "{}<{}>".format(
            self.__class__.__name__,
            ", ".join([
                "{}='{}'".format(attr, getattr(self, attr)) for attr in
                [
                    'status',
                    'section',
                    'term',
                    'days',
                    'start_time',
                    'end_time',
                    # 'comments',
                ]
            ])
        )


class Lecture(Activity):
    pass


class Lab(Activity):
    pass


class Tutorial(Activity):
    pass


class Discussion(Activity):
    pass
