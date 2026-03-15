from config import PARTY_LAST_ELECTION_VOTES_THRESHOLD
from party import Party

class PartyConstants:
    parties: list[Party]

    votes_last_election = {'D66': 656292,
                           'PVV': 2450878,
                           'VVD': 1589519,
                           'GLPVDA': 1643073,
                           'CDA': 345822,
                           'JA21': 71345,
                           'FVD': 232963,
                           'SGP': 217270,
                           'BBB': 485551,
                           'DENK': 246765,
                           'CU': 212532,
                           'PVDD': 235148,
                           'SP': 328225,
                           '50PLUS': 51037,
                           'VOLT': 178802,
                           'BIJ1': 44253,
                           'NSC': 1343287,
                           'BVNL': 52913,
                           'VREVDIER': 0,
                           'PIRATEN': 8890,
                           'LP': 4152,
                           'FNP': 0,
                           'DELINIE': 0,
                           'NLPLAN': 3357,
                           'VRIJVER': 0,
                           'ELLECT': 0,
                           'PVDR': 0,
                           'OVERIG': 28289
                           }

    parties = []
    for party_name, party_votes_last_election in votes_last_election.items():
        is_above_threshold = party_votes_last_election > PARTY_LAST_ELECTION_VOTES_THRESHOLD
        party = Party(party_name, party_votes_last_election, is_above_threshold_last_election=is_above_threshold)
        parties.append(party)

    votes_last_election_total = sum(votes_last_election.values())
