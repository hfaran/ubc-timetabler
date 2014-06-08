import os

import requests


class SSCConnection(object):
    def __init__(self):
        self.base_url = "https://courses.students.ubc.ca/cs/main"
        self.cache_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "__cache__"
        )
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)

    def get_course_page(self, dept="CPSC", course="304", sessyr="2014", sesscd="W"):
        page_name = "_".join(map(lambda x: str(x).lower(), [dept, course, sessyr, sesscd]))
        page = self._retrieve_cached_page(page_name)
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
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return f.read()
        else:
            return None
