import os
import time
import logging
import cookielib
import urllib2
import urllib
import re
from itertools import chain
from getpass import getpass

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
import filecache

from .course import Lecture, Lab, Tutorial, Course, Discussion
from timetabler.util import chunks


## Misc SSC notes
#
# req=1 gives you subject code page (i.e., CPSC)
# req=3 for viewing course page (i.e. CPSC 314)
# req=5 for viewing INDIVIDUAL section of a course (i.e, CPSC 314 101)
#
# Use get_worklists() to get list of worklists; can then use them to add
# courses to worklists by navigating to worklist first
# and THEN doing submit=save for courses to add to worklist


class SSCConnection(object):
    """Connection to UBC SSC

    :param cache_period: Life of cache before invalidation (number of seconds);
        if this is set to None, cache is never automatically invalidated
    """

    def __init__(self, cache_period=3600):
        self.base_url = "https://courses.students.ubc.ca"
        self.main_url = "{}/cs/main".format(self.base_url)
        self.cache_period = cache_period
        self.cache_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "__cache__"
        )
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)
        self.cookies = None
        self.worklists = {}

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

    def create_worklist(self, name, session="2015W"):
        """Creates a worklist with ``name`` for ``session``

        :type name: str
        :type session: str
        """
        # Must first be authorized
        assert self.cookies, "Unauthorized"
        # First we navigate to the session so the SSC knows which session to
        # create the worklist for
        self._navigate_to_session(session=session)
        # Finally, can make the post request to create the worklist
        op_url = "https://courses.students.ubc.ca/cs/main"
        op_data = {
            "attrWorklistName": name,
            "submit": "Create New Worklist",
            "pname": "wlist",
            "tname": "wlist",
            "attrSelectedWorklist": "-1"
        }
        self._post(url=op_url, params=op_data)

    def get_worklists(self, session="2015W"):
        """Retrieve name:url map for worklists for the given session

        :type session: str
        :rtype: dict
        :returns: e.g., {"fooworklist": "https://courses.students.ubc.ca
            /cs/main?pname=wlist&tname=wlist&attrSelectedWorklist=1000656166"}
        """
        # Grab page that has worklists list in it
        resp = self._navigate_to_session(session)
        text = resp.text
        soup = BeautifulSoup(text)
        # Navigate through tree to find list and a create a map of worklist
        # name to URL
        worklist_div = soup.find("div", {"class": "worklist-sidebar docs-sidebar"})
        worklist_map = {}
        for item in worklist_div.contents[0].contents:
            if isinstance(item, NavigableString):
                continue
            else:
                item = item.contents[0]
                name, link = item["title"], item["href"]
                if name not in ["New Worklist"]:
                    worklist_map[name] = "{}{}".format(self.base_url, link)
        return worklist_map

    def authorize(self, username=None, password=None):
        """Authorize this connection for personal SSC use

        If either password or username are not provided, a prompt
        is given for the missing value(s).

        :type username: str|None
        :type password: str|None
        """
        if username is None:
            username = raw_input("Username: ")
        if password is None:
            password = getpass()
        self.cookies = self._auth(username, password)

    def add_course_to_worklist(self, section, session, worklist):
        """Add provided ``section`` of course to worklist for the given session

        :type session: str
        :type section: str
        :type worklist: str
        """
        # First, we visit the worklist page to ensure we're on the correct
        # worklist
        self._navigate_to_worklist(session=session, worklist=worklist)
        # First navigate to section page itself
        self._navigate_to_section_page(section=section)
        # Then, navigate to the page with submit=save to save it in the
        # worklist
        self._navigate_to_section_page(section=section, submit="save")

    ###################
    # Private Methods #
    ###################

    def _get(self, *args, **kwargs):
        return self._authreq(requests.get, *args, **kwargs)

    def _post(self, *args, **kwargs):
        return self._authreq(requests.post, *args, **kwargs)

    def _authreq(self, func, *args, **kwargs):
        assert self.cookies, "Unauthorized"
        logging.info("Making request {}({}{}{})".format(
            func.__name__,
            ",".join(args),
            ", " if kwargs else "",
            ",".join("{}={}".format(k, v) for k, v in kwargs.items())
        ))
        return func(*args, cookies=self.cookies, **kwargs)

    def _navigate_to_section_page(self, section, session=None, submit=None):
        """Perform a GET on section page with various params

        :param section: e.g, "CPEN 422 101"
        :param session: e.g., "2015W"
            WARNING: this *resets* the selected worklist;
            do not add this if you want to stay on the existing session,
            and existing worklist. You should navigate to the worklist
            first and then do not provide this.
        :param submit: Provide this as "save" if you wish to add to current
            worklist
        """
        # Note: expand this list when supporting more options
        assert submit in [None, "save"]

        dept, course, section = section.split()
        params = dict(
            pname="subjarea",
            tname="subjareas",
            req="5",
            dept=dept,
            course=course,
            section=section
        )
        if session:
            sessyr, sesscd = session[:-1], session[-1]
            params.update(dict(
                sessyr=sessyr,
                sesscd=sesscd,
            ))
        if submit is not None:
            params["submit"] = submit
        return self._get(self.main_url, params=params)

    def _navigate_to_worklist(self, session, worklist):
        self._navigate_to_session(session)
        if session not in self.worklists:
            self.worklists[session] = self.get_worklists(session)
        worklist_url = self.worklists[session][worklist]
        return self._get(worklist_url)

    def _navigate_to_session(self, session="2015W"):
        sessyr, sesscd = session[:-1], session[-1]
        ref_url = "https://courses.students.ubc.ca/cs/main?sessyr={sessyr}" \
                  "&sesscd={sesscd}".format(
            sesscd=sesscd,
            sessyr=sessyr
        )
        return self._get(ref_url)

    def _auth(self, cwl_user, cwl_pass):
        """Performs SSC auth and returns CookieJar

        This is basically taken verbatim from
        https://github.com/cyrussassani/ubc-coursecheck/blob/master/ubcCourseChecker.py
        because SSC auth is a PTFO and it was impossible to get working with
        requests

        :type cwl_pass: str
        :type cwl_user: str
        :rtype: cookielib.CookieJar
        """
        # Cookie / Opener holder
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        # Login Header
        opener.addheaders = [('User-agent', 'UBC-Login')]

        # Install opener
        urllib2.install_opener(opener)

        # Form POST URL
        postURL = "https://cas.id.ubc.ca/ubc-cas/login/"

        # First request form data
        formData = {
            'username': cwl_user,
            'password': cwl_pass,
            'execution': 'e1s1',
            '_eventId': 'submit',
            'lt': 'xxxxxx',
            'submit': 'Continue >'
        }

        # Encode form data
        data = urllib.urlencode(formData)

        # First request object
        req = urllib2.Request(postURL, data)

        # Submit request and read data
        resp = urllib2.urlopen(req)
        respRead = resp.read()

        # Find the ticket number
        ticket = "<input type=\"hidden\" name=\"lt\" value=\"(.*?)\" />"
        t = re.search(ticket, respRead)

        # Extract jsession ID
        firstRequestInfo = str(resp.info())
        jsession = "Set-Cookie: JSESSIONID=(.*?);"
        j = re.search(jsession, firstRequestInfo)

        # Second request form data with ticket
        formData2 = {
            'username': cwl_user,
            'password': cwl_pass,
            'execution': 'e1s1',
            '_eventId': 'submit',
            'lt': t.group(1),
            'submit': 'Continue >'
        }

        # Form POST URL with JSESSION ID
        postURL2 = "https://cas.id.ubc.ca/ubc-cas/login;jsessionid=" + j.group(
            1)

        # Encode form data
        data2 = urllib.urlencode(formData2)

        # Submit request
        req2 = urllib2.Request(postURL2, data2)
        urllib2.urlopen(req2)

        # Perform login
        loginURL = "https://courses.students.ubc.ca/cs/secure/login"
        urllib2.urlopen(loginURL)

        return cj

    @staticmethod
    @filecache.filecache(filecache.FOREVER)
    def _activities_from_page(page):
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

        def activities_from_data(data):
            """Return list of ``Activity`` subclasses generated from ``data``"""
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
            data_dict = {k: data[v].encode('utf-8').strip(u'\n \xa0'.encode('utf-8'))
                         for k, v in attrs.iteritems()}
            # Find the appropriate Activity subclass (Lab/Lecture etc.)
            try:
                activity_cls = {
                    'Lecture': Lecture,
                    'Lecture-Laboratory': Lecture,
                    'Laboratory': Lab,
                    'Tutorial': Tutorial,
                    'Discussion': Discussion
                }[data_dict["Activity"]]
            except KeyError:
                logging.info("Invalid Activity type of {}; skipping."
                             .format(data_dict["Activity"]))
                return []
            # Create and return activity (or two if in both terms)
            terms = map(int, data_dict["Term"].split('-'))
            is_multi_term = len(terms) >= 2
            activities = []
            for term in terms:
                activity = activity_cls(
                    status=data_dict["Status"],
                    section=data_dict["Section"],
                    term=term,
                    days=data_dict["Days"],
                    start_time=data_dict["Start Time"],
                    end_time=data_dict["End Time"],
                    comments=data_dict["Comments"],
                    is_multi_term=is_multi_term
                )
                activities.append(activity)
            return activities

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
        return list(chain.from_iterable(
            activities_from_data(data_chunk)
            for data_chunk in chunks(t, 15)
        ))


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
            r = requests.get(self.main_url, params=dict(
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
