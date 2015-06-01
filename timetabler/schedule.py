import tempfile
import os
from uuid import uuid4

from prettytable import PrettyTable

from timetabler.util import iter_time, DAY_LIST


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

    def activities_for_day(self, day):
        return [a for a in self.activities if day in a.days]

    def activity_at_time(self, time="09:00", day="Mon", term=1):
        res = [a for a in self.activities if all([
            a.start_time <= time,
            a.end_time > time,
            day in a.days,
            term == a.term
        ])]
        assert len(res) in [0, 1], ("More than one activity found at specified time. "
                                    "This likely means the code is wrong.")
        if res:
            return res[0]
        else:
            return None

    def _draw(self, term=1):
        t = PrettyTable(["Time"] + DAY_LIST)
        earliest_start_time = min(a.start_time for a in self.activities)
        latest_end_time = max(a.end_time for a in self.activities)
        time_iter = iter_time(earliest_start_time, latest_end_time)
        for time in time_iter:
            t.add_row([time] + [getattr(self.activity_at_time(time, day, term), 'section', "") for day in DAY_LIST])
        return t

    def _create_table_div(self, table):
        return "\n{}\n{}\n{}\n".format(
            '<div class="CSSTableGenerator">',
            table.get_html_string(),
            '</div>'
        )

    def draw(self, terms=(1,), draw_location="browser"):
        """Draw schedule

        :type terms: tuple or list
        :param term: Terms for which you would like to draw the schedule
        :param draw_location: "browser"|"terminal"
        :returns: List of tables
        :rtype: list
        """
        assert draw_location in ["browser", "terminal"]
        tables = {term: self._draw(term) for term in terms}
        if draw_location=="browser":
            tempdir = tempfile.gettempdir()
            tempfile_loc = os.path.join(tempdir, "ubc-timetabler_{}.html".format(uuid4().hex))
            with open(tempfile_loc, 'w+') as f:
                html = "{}{}{}".format(
                """<html>

                    <head>
                        <!-- Bring to you by http://www.CSSTableGenerator.com -->
                        <link rel="stylesheet" \
                        href="https://raw.githubusercontent.com/hfaran/ubc-timetabler/master/css/table.css" \
                        type="text/css"/>
                    </head>

                    <body>
                    """,
                "</br></br></br>\n".join(map(self._create_table_div, tables.itervalues())),
                """
                    </body>

                </html>"""
                )
                f.write(html)
            import webbrowser
            webbrowser.open('file://' + os.path.realpath(tempfile_loc))
        elif draw_location=="terminal":
            for term, table in tables.iteritems():
                print("Courses for Term {}: {}".format(
                    term,
                    ", ".join({" ".join(act.section.split()[:2])
                               for act in self.activities if act.term == term})
                ))
                print(table)

        return tables
