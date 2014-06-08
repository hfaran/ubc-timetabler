class Course(object):
    def __init__(self, dept, number,
                 lectures=None, labs=None, tutorials=None, discussions=None):
        self.dept = dept
        self.number = number
        self.lectures = lectures if lectures else []
        assert all(isinstance(l, Lecture) for l in self.lectures)
        self.labs = labs if labs else []
        assert all(isinstance(l, Lab) for l in self.labs)
        self.tutorials = tutorials if tutorials else []
        assert all(isinstance(l, Tutorial) for l in self.tutorials)
        self.discussions = discussions if discussions else []
        assert all(isinstance(l, Discussion) for l in self.discussions)
        self._num_section_constraints = [
            (l[0].__class__, 1)
            for l in [self.labs, self.lectures,
                      self.tutorials, self.discussions]
            if l
        ]

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
    def __init__(self, status, section, term, days, start_time, end_time, comments):
        self.status = status  # e.g, "Restricted"
        self.section = section  # e.g., "EECE 310 L1A"
        self.term = int(term)  # e.g., 2
        self.days = set(days.split())  # e.g., {"Mon", "Wed"}
        self.start_time = start_time  # e.g., "13:00"
        self.end_time = end_time
        self.comments = comments

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
