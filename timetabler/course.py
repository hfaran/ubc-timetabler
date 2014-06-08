class Activity(object):
    def __init__(self, section, days, start_time, end_time):
        self.section = section
        self.days = days
        self.start_time = start_time
        self.end_time = end_time


class Lecture(Activity):
    pass


class Lab(Activity):
    pass


class Tutorial(Activity):
    pass


class Course(object):
    def __init__(self, dept, number,
                 lectures=None, labs=None, tutorials=None,
                 custom_constraints=None):
        self.dept = dept
        self.number = number
        self.lectures = lectures if lectures else []
        assert all(isinstance(l, Lecture) for l in self.lectures)
        self.labs = labs if labs else []
        assert all(isinstance(l, Lab) for l in self.labs)
        self.tutorials = tutorials if tutorials else []
        assert all(isinstance(l, Tutorial) for l in self.tutorials)
        self._constraints = custom_constraints if custom_constraints else None

    @property
    def constraints(self):
        if self._constraints is None:
            self._constraints = [
                (l[0].__class__, 1)
                for l in [self.labs, self.lectures, self.tutorials]
                if l
            ]
        return self._constraints
