from __future__ import unicode_literals, absolute_import
import os
import unittest
from six import PY2

from ics.parse import string_to_container


class TestFunctional(unittest.TestCase):

    def test_gehol(self):
        # convert ics to utf8: recode l9..utf8 *.ics
        cal = os.path.join(os.path.dirname(__file__), "gehol", "BA1.ics")
        with open(cal) as ics:
            ics = ics.read()
            if PY2:
                ics = ics.decode('utf-8')

            ics = string_to_container(ics)[0]
            self.assertTrue(ics)


if __name__ == '__main__':
    unittest.main()
