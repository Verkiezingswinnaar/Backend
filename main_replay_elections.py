"""
With this script, you can replay elections by loading one of the files in the replay or testdata folders.
The files in the replay folder correspond to actual elections. The files in the testdata folder are fake data.
Note: For the "TK2025-10-29.jsonl" file, the earliest results that I have available are from about 01:30 AM onwards.
At this point, about 40% of the results were reported.
"""

import json
import time

from file import File
from party_constants import PartyConstants
from party_snapshot import PartySnapshot
from snapshot import Snapshot

REPLAY_ELECTION_PATH = "./replay/TK2025-10-29.jsonl"

def main():
    replay_previous_election = []
    with open(REPLAY_ELECTION_PATH, "r") as f:
        for line in f:
            replay_previous_election.append(json.loads(line))

    file = File("data")
    while True:
        file.delete_jsonl()
        execute_replay(replay_previous_election, file)
        time.sleep(60)

def execute_replay(replay_previous_election: list, file: File):
    for snapshot_replay in replay_previous_election:
        snapshot = Snapshot()
        snapshot.timestamp = snapshot_replay["timestamp"]
        for party_name, party_snapshot_replay in snapshot_replay["party_snapshots"].items():

            party_snapshot = PartySnapshot(party_snapshot_replay["votes_this_election"],
                                           party_snapshot_replay["votes_last_election"])
            party_object = next((p for p in PartyConstants.parties if p.name == party_name), None)
            snapshot.party_snapshots[party_object] = party_snapshot

        snapshot.predict_votes_and_percentages()
        snapshot_dict = snapshot.to_dict()

        file.dump_to_json(snapshot_dict)
        file.dump_to_jsonl(snapshot_dict)
        file.compress_jsonl_to_gz()
        # file.upload_json_to_s3()
        file.upload_gz_to_s3()

        time.sleep(10)

if __name__ == "__main__":
    main()
