import os
import time
import logging

import requests
from bs4 import BeautifulSoup

from .course import Lecture, Lab, Tutorial, Course, Discussion
from timetabler.util import chunks


class SSCConnection(object):
    """Connection to UBC SSC

    :param cache_period: Life of cache before invalidation (number of seconds);
        if this is set to None, cache is never automatically invalidated
    """

    def __init__(self, cache_period=3600):
        self.base_url = "https://courses.students.ubc.ca/cs/main"
        self.cache_period = cache_period
        self.cache_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "__cache__"
        )
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)

    ##################
    # Public Methods #
    ##################

    def get_course(self, course_name="CPSC 304", session="2014W", refresh=False):
        dept, course_num = course_name.split()
        sessyr, sesscd = session[:4], session[-1]
        page = self._get_course_page(dept, course_num, sessyr, sesscd, invalidate=refresh)
        activities = self._activities_from_page(page)

        lectures = [a for a in activities if isinstance(a, Lecture)]
        labs = [a for a in activities if isinstance(a, Lab)]
        tutorials = [a for a in activities if isinstance(a, Tutorial)]
        discussions = [a for a in activities if isinstance(a, Discussion)]

        course = Course(
            dept=dept,
            number=course_num,
            lectures=lectures,
            labs=labs,
            tutorials=tutorials,
            discussions=discussions
        )
        return course

    ###################
    # Private Methods #
    ###################

    def _activities_from_page(self, page):
        """Get list of ``Activity`` subclasses from data in ``page``

        :rtype: [Activity, ...]
        """
        attrs = {
            u'Status': 0,
            u'Section': 4,
            u'Activity': 7,
            u'Term': 8,
            u'Interval': 9,  # Either 9 or 10?
            u'Days': 11,
            u'Start Time': 12,
            u'End Time': 13,
            u'Comments': 14
        }

        def activity_from_data(data):
            """Return an ``Activity`` subclass generated from ``data``"""
            # Make copy
            data = data[:]
            # Fill in anything missing with empty string
            # (This is to handle the case of the last activity which may have had comments section
            # stripped from it)
            data_length = len(data)
            if data_length < 15:
                num_missing = 15 - data_length
                data += ['' for i in xrange(num_missing)]
            # Generate a mapping of the data using ``attrs`` defined below
            data_dict = {k: data[v].strip(u'\n \xa0') for k, v in attrs.iteritems()}
            # Find the appropriate Activity subclass (Lab/Lecture etc.)
            try:
                activity_cls = {
                    u'Lecture': Lecture,
                    u'Laboratory': Lab,
                    u'Tutorial': Tutorial,
                    u'Discussion': Discussion
                }[data_dict["Activity"]]
            except KeyError:
                logging.info("Invalid Activity type of {}; skipping.".format(data_dict["Activity"]))
                return None
            # Create and return activity
            activity = activity_cls(
                status=data_dict["Status"],
                section=data_dict["Section"],
                term=data_dict["Term"],
                days=data_dict["Days"],
                start_time=data_dict["Start Time"],
                end_time=data_dict["End Time"],
                comments=data_dict["Comments"]
            )
            return activity

        soup = BeautifulSoup(page)
        t = soup.text
        # Get rid of the top of the page
        t = t.split("Status\nSection")[-1]
        # Get rid of the bottom of the page
        t = "".join(
            t.split("Browse    Standard Timetables")[:-1]
        )  # The list should be length 1 but "".join to do it cleanly
        # Strip outer stuff (newlines, spaces, etc.)
        t = t.strip(u'\n \xa0')
        # Split by newlines to start and give an almost "cell-by-cell" list for the table
        t = t.split('\n')
        # Strip sections and spaces so that after this we are actually left with a list of all course stuff
        itert = iter(t)
        current = next(itert)
        while current in attrs.keys() + [u'']:
            current = next(itert)
        t = [current] + list(itert)
        logging.info(t)
        # Create and return list of activities
        return filter(lambda a: a is not None, [activity_from_data(data_chunk) for data_chunk in chunks(t, 15)])


    def _get_course_page(self, dept="CPSC", course_num="304", sessyr="2014", sesscd="W", invalidate=False):
        """Get course page from SSC

        Retrieved pages are cached for a ``self.cache_period``, and then invalidated.

        :type  dept: str
        :type  course: str|int
        :type  sessyr: str|int
        :type  sesscd: str
        :type  invalidate: bool
        :param invalidate: If this is set, existing cache for the page will be invalidated
        :returns: Text of SSC course page for given course
        """
        page_name = "_".join(map(lambda x: str(x).lower(), [dept, course_num, sessyr, sesscd]))
        # Attempt to retrieve already cached page
        page = self._retrieve_cached_page(page_name, invalidate=invalidate)
        # If not already cached, retrieve, cache, and return
        if page is None:
            logging.info("Page was not found in cache or was invalidated; retrieving from remote and caching...")
            r = requests.get(self.base_url, params=dict(
                pname="subjarea",
                tname="subjareas",
                req="3",
                dept=dept,
                course=course_num,
                sessyr=sessyr,
                sesscd=sesscd
            ))
            page_data = r.text
            self._cache_page(page_name, page_data)
            return page_data
        else:
            logging.info("Valid existing page was found in cache; retrieving from file...")
            return page

    def _cache_page(self, name, text):
        """Stores page with name ``name`` and contents ``text`` to the cache folder"""
        filename = os.path.join(self.cache_path, name)
        with open(filename, 'w+') as f:
            f.write(text)

    def _retrieve_cached_page(self, name, invalidate=False):
        """Retrieves page ``name`` from cache"""
        filename = os.path.join(self.cache_path, name)
        # First case, cache does not already exist
        if not os.path.exists(filename):
            return None
        # Check if existing cache is stale
        last_modified = os.path.getmtime(filename)
        period = time.time() - last_modified
        logging.info("Page was last fetched {:.0f} seconds ago.".format(period))
        # If cache is stale, or an invalidation was requested, remove
        if any([(self.cache_period) and (period > self.cache_period), invalidate]):
            os.remove(filename)
            return None
        # Cache exists, and is valid, so return it
        with open(filename, 'r') as f:
            return f.read()
