from config import PARTY_LAST_ELECTION_VOTES_THRESHOLD
from election_data import load_active_elections, load_election_results
from party import Party


class PartyConstants:
    active_elections = load_active_elections()
    previous_results = load_election_results(active_elections.previous)
    votes_last_election = previous_results.votes
    seats_last_election = previous_results.seats
    parties = []
    for party_name, party_votes_last_election in votes_last_election.items():
        parties.append(
            Party(
                party_name,
                party_votes_last_election,
                is_above_threshold_last_election=(
                    party_votes_last_election > PARTY_LAST_ELECTION_VOTES_THRESHOLD
                ),
            )
        )
    votes_last_election_total = previous_results.total_votes
