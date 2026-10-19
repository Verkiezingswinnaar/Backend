import unittest

from election_data import load_active_elections, load_election_results
from party_constants import PartyConstants


class ElectionDataTests(unittest.TestCase):
    def test_active_ids_select_individual_election_files(self):
        active = load_active_elections()
        self.assertEqual(active.current, "TK2025")
        self.assertEqual(active.previous, "TK2023")
        current = load_election_results(active.current)
        previous = load_election_results(active.previous)
        self.assertEqual(current.id, active.current)
        self.assertEqual(previous.id, active.previous)
        self.assertEqual(current.election_type, "national")

    def test_tk2023_archive_contains_official_totals_and_overig(self):
        previous = load_election_results("TK2023")
        self.assertEqual(previous.total_votes, 10_432_726)
        self.assertEqual(previous.votes["OVERIG"], 28_289)
        self.assertEqual(sum(previous.seats.values()), 150)
        self.assertEqual(previous.seats["PVV"], 37)
        self.assertEqual(previous.seats["NSC"], 20)

    def test_replay_party_roster_includes_overig(self):
        self.assertIn("OVERIG", PartyConstants.votes_last_election)
        self.assertIn("OVERIG", {party.name for party in PartyConstants.parties})


if __name__ == "__main__":
    unittest.main()
