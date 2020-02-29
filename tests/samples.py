import glob
import os

import pytest

from ics.icalendar import Calendar

base_path = os.path.join(os.path.dirname(__file__), "samples")

base_fixtures = glob.glob(os.path.join(base_path, "*.ics"))
other_fixtures = glob.glob(os.path.join(base_path, "**", "*.ics"))


@pytest.mark.parametrize("input_path", base_fixtures + other_fixtures)
def test_eval(input_path):
    with open(input_path) as fd:
        Calendar.parse_multiple(fd.read())
