import os
import time
import requests


class SSCConnection(object):
    """Connection to UBC SSC

    :param cache_period: Life of cache before invalidation (number of seconds)
    """
    def __init__(self, cache_period=86400):
        self.base_url = "https://courses.students.ubc.ca/cs/main"
        self.cache_period = cache_period
        self.cache_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "__cache__"
        )
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)

    def get_course_page(self, dept="CPSC", course="304", sessyr="2014", sesscd="W"):
        """Get course page from SSC

        Retrieved pages are cached for a ``self.cache_period``, and then invalidated.

        :type dept: str
        :type course: str|int
        :type sessyr: str|int
        :type sesscd: str
        :returns: Text of SSC course page for given course
        """
        page_name = "_".join(map(lambda x: str(x).lower(), [dept, course, sessyr, sesscd]))
        # Attempt to retrieve already cached page
        page = self._retrieve_cached_page(page_name)
        # If not already cached, retrieve, cache, and return
        if page is None:
            r = requests.get(self.base_url, params=dict(
                pname="subjarea",
                tname="subjareas",
                req="3",
                dept=dept,
                course=course,
                sessyr=sessyr,
                sesscd=sesscd
            ))
            page_data = r.text
            self._cache_page(page_name, page_data)
            return page_data
        else:
            return page

    def _cache_page(self, name, text):
        filename = os.path.join(self.cache_path, name)
        with open(filename, 'w+') as f:
            f.write(text)

    def _retrieve_cached_page(self, name):
        filename = os.path.join(self.cache_path, name)
        # First case, cache does not already exist
        if not os.path.exists(filename):
            return None
        # Check if existing cache is invalid (if so, remove and return None)
        last_modified = os.path.getmtime(filename)
        period = time.time() - last_modified
        if period > self.cache_period:
            os.remove(filename)
            return None
        # Cache exists, and is valid, so return it
        with open(filename, 'r') as f:
            return f.read()