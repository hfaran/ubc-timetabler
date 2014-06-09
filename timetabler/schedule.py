class Schedule(object):
    def __init__(self, sched):
        """Schedule

        e.g. for ``sched``:
        ((Lab<status='Restricted', section='EECE 381 L2A', term='2', days='[u'Tue', u'Thu']', start_time='16:00', end_time='19:00'>,
          Lecture<status='Restricted', section='EECE 381 201', term='2', days='[u'Mon']', start_time='9:00', end_time='11:00'>),
         (Lab<status='Restricted', section='EECE 353 L2C', term='2', days='[u'Thu']', start_time='14:00', end_time='16:00'>,
          Lecture<status='', section='EECE 353 201', term='2', days='[u'Tue', u'Thu']', start_time='14:00', end_time='15:30'>),
         (Lecture<status='', section='CPSC 304 201', term='2', days='[u'Tue', u'Thu']', start_time='11:00', end_time='12:30'>,
          Tutorial<status='', section='CPSC 304 T2A', term='2', days='[u'Fri']', start_time='14:00', end_time='15:00'>))
        """
        self._sched = sched
        self.activities = [act for crs in sched for act in crs]
