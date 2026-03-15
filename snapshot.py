from dataclasses import dataclass
import time

from party import Party
from party_constants import PartyConstants
from party_snapshot import PartySnapshot

@dataclass
class Snapshot:
    #Note that all the estimates are floats. They are only rounded to ints when they are turned into a json.
    timestamp: int
    snapshot_total_votes_this_election: int
    snapshot_total_votes_last_election: int
    estimated_total_votes: float
    estimated_total_votes_direct: float
    estimated_total_votes_ratio: float

    snapshot_total_votes_below_threshold: float
    estimated_total_votes_below_threshold: float
    percentage_below_threshold: float

    estimated_total_votes_above_threshold: float
    party_snapshots: dict[Party, PartySnapshot]

    def __init__(self):
        self.timestamp = int(time.time() * 1000)
        self.snapshot_total_votes_this_election = 0
        self.snapshot_total_votes_last_election = 0
        self.estimated_total_votes = 0
        self.estimated_total_votes_direct = 0
        self.estimated_total_votes_ratio = 0

        self.snapshot_total_votes_below_threshold = 0
        self.estimated_total_votes_below_threshold = 0
        self.percentage_below_threshold = 0

        self.estimated_total_votes_above_threshold = 0
        self.party_snapshots = {}

    def predict_votes_and_percentages(self) -> None:
        """
        Calculate votes, vote predictions, and percentages for each party.
        Handles both new parties, and parties that already existed in the previous election.
        Only relevant for national (and province?) elections.
        """
        total_votes_this_election = 0
        total_votes_last_election = 0
        total_votes_below_threshold = 0

        # 1️⃣ First pass: accumulate total votes
        for party, snapshot in self.party_snapshots.items():
            votes_this_election = snapshot.votes_this_election
            total_votes_this_election += votes_this_election
            total_votes_last_election += snapshot.votes_last_election
            if not party.is_above_threshold_last_election:
                total_votes_below_threshold += votes_this_election

        # 2️⃣ Predict votes for above-threshold parties
        estimated_votes_above_threshold = 0.0
        for party, snapshot in self.party_snapshots.items():
            if party.is_above_threshold_last_election:
                prediction = snapshot.factor * party.votes_last_election
                snapshot.votes_prediction = prediction
                estimated_votes_above_threshold += prediction

        # 3️⃣ Calculate percentages for below-threshold parties
        percentage_below_threshold = 0.0
        for party, snapshot in self.party_snapshots.items():
            if not party.is_above_threshold_last_election:
                snapshot.votes_percentage = snapshot.votes_this_election / total_votes_this_election
                percentage_below_threshold += snapshot.votes_percentage

        # 4️⃣ Estimate the total number of votes. We assume that the below-threshold parties have the same percentage
        # of vote in the total vote as they currently have
        estimated_votes_below_threshold = (
                (percentage_below_threshold / (1 - percentage_below_threshold))
                * estimated_votes_above_threshold
        )

        estimated_total_votes = estimated_votes_above_threshold + estimated_votes_below_threshold

        # 5️⃣ Final assignment of percentages and predicted votes
        for party, snapshot in self.party_snapshots.items():
            if party.is_above_threshold_last_election:
                snapshot.votes_percentage = snapshot.votes_prediction / estimated_total_votes
            else:
                snapshot.votes_prediction = snapshot.votes_percentage * estimated_total_votes

        # 6️⃣ Store totals
        self.snapshot_total_votes_this_election = total_votes_this_election
        self.snapshot_total_votes_last_election = total_votes_last_election
        self.snapshot_total_votes_below_threshold = total_votes_below_threshold
        self.percentage_below_threshold = percentage_below_threshold
        self.estimated_total_votes_above_threshold = estimated_votes_above_threshold
        self.estimated_total_votes_below_threshold = estimated_votes_below_threshold
        self.estimated_total_votes = estimated_total_votes
        self.estimated_total_votes_direct = total_votes_this_election / total_votes_last_election * PartyConstants.votes_last_election_total
        self.estimated_total_votes_ratio = total_votes_this_election / estimated_total_votes


    def to_dict(self) -> dict:
        party_snapshots = {}
        for party, snapshot in self.party_snapshots.items():
            party_snapshots[party.name] = snapshot.to_dict()

        snapshot_dict = {
            "timestamp": self.timestamp,
            "snapshot_total_votes_this_election": self.snapshot_total_votes_this_election,
            "snapshot_total_votes_last_election": self.snapshot_total_votes_last_election,
            "estimated_total_votes": round(self.estimated_total_votes),
            "estimated_total_votes_direct": round(self.estimated_total_votes_direct),
            "estimated_below_threshold": self.estimated_total_votes_below_threshold,
            "estimated_above_threshold": self.estimated_total_votes_above_threshold,
            "estimated_total_votes_ratio": round(self.estimated_total_votes_ratio * 10000) / 100, # Round on 2 digits
            "party_snapshots": party_snapshots
        }
        return snapshot_dict

    # Calculate the 'kiesdeler'
    def determine_seats(self):
        # To be further developed before the 2029 Tweede Kamer elections.
        # Reminder to take the d'Hondt rule into account when determining the seats each party
        return 1



