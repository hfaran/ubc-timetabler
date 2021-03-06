#!/usr/bin/env python2

from time import time
import sys
import logging
from itertools import combinations
import json
import shlex
import os
from getpass import getpass

from timetabler.scheduler import Scheduler
from timetabler.ssc.course import Lecture, Discussion, Lab
from timetabler import sort, util
from timetabler.sort import earliest_start  # Helper function (should probably be in util)
from timetabler.ssc.ssc_conn import SSCConnection


COMMUTE_HOURS = 1.75
SESSION = "2015W"
TERMS = (1, 2)
# If this is set, pages will be freshly fetched from the SSC every time
# This is only recommended if it is close to course-registration time
#  and courses are being closed out (please be friendly to the SSC
#  and leave this set to False for the usual case)
NO_CACHE = False
# If this is set, sections, such as labs that are in the same slot
#  but are at different places, are only represented as the first section
#  in the set of many. This is useful to set to True closer to course
#  registration when you are actually building worklists.
ALLOW_SAME_SLOT_SECTIONS = False


def inline_write(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def get_schedules(ssc_conn):
    required = (
        ("CPEN 321", "Software Engineering"),
        ("CPEN 421", "Software Project Management"),
        ("CPEN 422", "Software Testing and Analysis"),
        # ("APSC 486", "NVD"),
        ("CPEN 492", "Software Engineering Capstone"),
        ("CPEN 481", "Economic Analysis of Engineering Projects"),
        ("APSC 450", "Professional Engineering Practice"),
    )
    opt = [
        ## CPSC
        ("CPSC 312", "Functional programming"),
        ("CPSC 340", "Machine Learning and Data Mining"),
        ("CPSC 415", "Advanced Operating Systems"),
        ("CPSC 322", "Introduction to Artificial Intelligence"),
        ("CPSC 421", "Introduction to Theory of Computing"),
        ("CPSC 418", "Parallel Computation"),
        ("CPSC 344", "Introduction to Human Computer Methods"),
        ("CPSC 314", "Computer Graphics"),
        ("CPSC 404", "Advanced Relational Databases"),
        ("CPSC 425", "Computer Vision"),
        ## CPEN
        ("CPEN 400A", "Topics in Computer Engineering (Building Modern Web Applications)"),
        ("CPEN 442", "Introduction to Computer Security"),
        ("CPEN 431", "Design of Distributed Software Applications"),
        ("CPEN 412", "Microcomputer System Design"),
        ("CPEN 411", "Computer Architecture"),
    ]
    num_required_from_opt = 2
    combs = list(combinations(opt, r=num_required_from_opt))

    schedules = []
    num_combs = len(combs)
    inline_write("Processing {} combinations".format(num_combs))
    for i, courses in enumerate([required + comb for comb in combs]):
        s = Scheduler(courses, session=SESSION, terms=TERMS, refresh=NO_CACHE,
                      duplicates=ALLOW_SAME_SLOT_SECTIONS, ssc_conn=ssc_conn)
        # I don't want any classes that start before 9:00AM
        s.add_constraint(lambda sched: earliest_start(sched.activities) >= 9)
        # Add GEOG122 constraints if we need to
        if "GEOG 122" in courses:
            # STTs are for Vantage College students
            s.courses["GEOG 122"].add_constraint(
                lambda acts: all(a.status not in [u"STT"] for a in acts)
            )
            # Default sections contained a Tutorial but that is for Vantage
            # students, so removing that and only setting Lecture and Discussion
            s.courses["GEOG 122"].num_section_constraints = [
                (Lecture, 1), (Discussion, 1)
            ]

        # Add statuses for courses that shouldn't be considered
        bad_statuses = (
            "Full",
            # "Blocked",
        )
        schedules.extend(s.generate_schedules(bad_statuses=bad_statuses))
        inline_write(".")
    sys.stdout.write("\n")
    return schedules


def repl(schedules, ssc):
    # Set up readline goodness for us so the prompts on OS X/Windows are nice
    try:
        import gnureadline
    except ImportError:
        try:
            import pyreadline
        except ImportError:
            pass

    HELP = """
    n - Next
    cw <name> - Create Worklist with name
    as <worklist> - Add Sections to worklist
    pw <session=2015W> - Print Worklists for session
    dw <name> - Delete worklist with name
    q - Quit
    help - Print help
    """
    print(HELP)

    for i, sched in enumerate(schedules):
        sched.draw(terms=TERMS, draw_location="terminal", title_format="code")
        if i < len(schedules) - 1:
            while True:
                try:
                    cmd = raw_input("> ")
                    cmd = shlex.split(cmd)
                    if not cmd:
                        continue
                    if cmd[0] == "n":
                        break
                    elif cmd[0] == "cw":
                        name = cmd[1]
                        ssc.create_worklist(name, session=SESSION)
                        print("Created worklist '{}'".format(name))
                    elif cmd[0] == "as":
                        worklist = cmd[1]
                        worklists = ssc.cache_worklists(SESSION)
                        assert worklist in worklists
                        for act in sched.activities:
                            print("Registering {}...".format(act.section))
                            ssc.add_course_to_worklist(
                                act.section,
                                SESSION,
                                worklist
                            )
                    elif cmd[0] == "pw":
                            session = cmd[1] if len(cmd) > 1 else SESSION
                            print(json.dumps(ssc.cache_worklists(session),
                                             indent=4))
                    elif cmd[0] == "dw":
                        worklist = cmd[1]
                        ssc.delete_worklist(name=worklist, session=SESSION)
                        print("Deleted worklist '{}'".format(worklist))
                    elif cmd[0] == "q":
                        sys.exit(0)
                    elif cmd[0] == "help":
                        print(HELP)
                    else:
                        print(HELP)
                except Exception as err:
                    logging.exception(err)
                    print(HELP)


def main():
    # Get SSC credentials
    CREDENTIALS_FILE = "credentials.json"
    if not os.path.exists(CREDENTIALS_FILE):
        print("Please enter your SSC username and password (these will be "
              "stored on your local filesystem as {})".format(
            os.path.abspath(CREDENTIALS_FILE)
        ))
        credentials = dict(
            username=raw_input("Username: "),
            password=getpass()
        )
        with open(CREDENTIALS_FILE, 'w+') as f:
            json.dump(credentials, f)
    else:
        credentials = json.load(open("credentials.json"))

    # Create SSC connection and log in
    ssc = SSCConnection()
    ssc.authorize(**credentials)

    # Setup logging
    util.setup_root_logger('WARNING')

    # Get schedules (time operation)
    start_time = time()
    scheds = get_schedules(ssc)
    print("There were {} valid schedules found.".format(len(scheds)))
    print("This took {:.2f} seconds to calculate.".format(
        time() - start_time
    ))
    # Sort
    # Statements in order from top-to-bottom from least-to-most important
    # i.e., put the most important at the bottom
    scheds = sort.free_days(scheds)
    scheds = sort.least_time_at_school(scheds, commute_hrs=COMMUTE_HOURS)
    scheds = sort.sum_latest_daily_morning(scheds)
    scheds = sort.even_time_per_day(scheds, commute_hrs=COMMUTE_HOURS)
    scheds = sort.even_courses_per_term(scheds)

    repl(scheds, ssc)


if __name__ == '__main__':
    main()
