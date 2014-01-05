import unittest
from datetime import timedelta
from ics.parse import ParseError
from ics.utils import parse_duration

class TestParseDuration(unittest.TestCase):
    dataset_simple = {
        'P1W': (7, 0), 'P1D': (1, 0), '-P1D': (-1, 0),
        'P1H': (0, 3600), 'P1M': (0, 60), 'P1S': (0, 1),
        'PT1H': (0, 3600), 'PT1M': (0, 60), 'PT1S': (0, 1),
        'PT': (0, 0)
    }

    dataset_combined = {
        "P1D1WT1H": (8, 3600), "P1DT1H1W": (8, 3600), "P1DT1H1M1W": (8, 3660),
        "P1DT1H1M1S1W": (8, 3661), "P1DT1H": (1, 3600), "P1DT1H1M": (1, 3660),
        "PT1S1M": (0, 61)
    }

    def run_on_dataset(self, dataset):
        for test in dataset:
            expected = dataset[test]
            self.assertEqual(parse_duration(test), timedelta(*expected))

    def test_simple(self):
        self.run_on_dataset(self.dataset_simple)

    def test_combined(self):
        self.run_on_dataset(self.dataset_combined)

    def test_noP(self):
        self.assertRaises(ParseError, parse_duration, 'caca')

    def test_twoLetters(self):
        self.assertRaises(ParseError, parse_duration, 'P1DF')

    def test_twoOccurences(self):
        self.assertRaises(ParseError, parse_duration, 'P1D1D')
