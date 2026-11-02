import unittest
from team_stats_helpers import is_fourth_down_attempt

class FourthDownAttemptTests(unittest.TestCase):
    def test_run_and_pass_are_attempts(self):
        self.assertTrue(is_fourth_down_attempt("run"))
        self.assertTrue(is_fourth_down_attempt("pass"))

    def test_punts_and_field_goals_are_excluded(self):
        for play_type in ("punt", "field_goal", "extra_point", "kickoff", "no_play", "qb_kneel", ""):
            with self.subTest(play_type=play_type):
                self.assertFalse(is_fourth_down_attempt(play_type))

if __name__ == "__main__":
    unittest.main()
