from __future__ import absolute_import, unicode_literals

import os
import unittest

from ics.grammar.parse import string_to_container


class TestFunctional(unittest.TestCase):

    def test_gehol(self):
        # convert ics to utf8: recode l9..utf8 *.ics
        cal = os.path.join(os.path.dirname(__file__), "gehol", "BA1.ics")
        with open(cal) as ics:
            ics = ics.read()
            ics = string_to_container(ics)[0]
            self.assertTrue(ics)


if __name__ == '__main__':
    unittest.main()
