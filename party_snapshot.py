from dataclasses import dataclass

@dataclass
class PartySnapshot:
    votes_this_election: int
    votes_last_election: int
    votes_last_election_corrected: float
    votes_this_election_with_partials: int
    votes_last_election_with_partials: int
    factor: float
    votes_percentage: float
    votes_prediction: float

    def __init__(self, votes_this_election, votes_last_election,
                 votes_last_election_corrected=0.0,
                 votes_this_election_with_partials=0, votes_last_election_with_partials=0):
        self.votes_this_election = votes_this_election
        self.votes_last_election = votes_last_election
        self.factor = self.votes_this_election / self.votes_last_election if self.votes_last_election else 0
        self.votes_percentage = 0
        self.votes_prediction = 0
        self.votes_last_election_corrected = votes_last_election_corrected
        self.votes_this_election_with_partials = votes_this_election_with_partials
        self.votes_last_election_with_partials = votes_last_election_with_partials
        
    def to_dict(self):
        party_prediction = {
            "relative_vote_change": round((self.factor - 1) * 10000) / 100, # Round on 2 digits
            "votes_percentage": round(self.votes_percentage * 10000) / 100, # Round on 2 digits
            "votes_prediction": round(self.votes_prediction),
            "votes_this_election": self.votes_this_election,
            "votes_last_election": self.votes_last_election,
            "votes_last_election_corrected": round(self.votes_last_election_corrected),
            "votes_this_election_with_partials": self.votes_this_election_with_partials,
            "votes_last_election_with_partials": self.votes_last_election_with_partials,
        }
        return party_prediction

