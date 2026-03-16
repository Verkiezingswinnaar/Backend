"""
Main script to extract and process the election results.

Requires URL_API and URL_API_INDEX to be set in a '.env' file before execution.
"""

import copy
import json
import time
from typing import Any

import requests

from config import URL_API_INDEX, MINIMUM_NUMBER_OF_MUNICIPALITIES, MINIMUM_NUMBER_OF_VOTES
from file import File
from party import Party
from party_snapshot import PartySnapshot
from snapshot import Snapshot

def main():
    party_names = ['D66', 'PVV', 'VVD', 'GLPVDA', 'CDA', 'JA21', 'FVD', 'SGP', 'DENK', 'CU', 'PVDD', 'SP', '50PLUS', 'VOLT']

    parties = []
    for party_name in party_names:
        parties.append(Party(party_name, 0, False))

    previous_party_snapshots = {}

    while True:
        index_page = get_index_page()
        municipalities = transform_index_to_municipalities(index_page)
        party_pages = get_party_pages(parties)
        snapshot = create_snapshot(party_pages, municipalities)

        if snapshot.party_snapshots != previous_party_snapshots and snapshot.party_snapshots != {}:
            previous_party_snapshots = copy.deepcopy(snapshot.party_snapshots)

            dump_files_for_debugging(party_pages, index_page)

            snapshot_dict = snapshot.to_dict()

            file = File("data")
            file.dump_to_json(snapshot_dict)
            file.dump_to_jsonl(snapshot_dict)
            file.compress_jsonl_to_gz()
            # file.upload_json_to_s3()
            file.upload_gz_to_s3()
            print("Uploaded results")

        time.sleep(60)

def get_party_pages(parties) -> dict[Party, Any]:
    pages = {}
    for party in parties:
        url = party.get_api_url()
        response = requests.get(url)

        if response.status_code == 200:
            party_results = response.json()  # Parse JSON response
            pages[party] = party_results

        else:
            print(f"Error: {response.status_code} for party {party.name}" )

    return pages

def get_index_page() -> dict[str, Any]:
    index_page = {}

    url = URL_API_INDEX
    response = requests.get(url)

    if response.status_code == 200:
        index_page = response.json()  # Parse JSON response
    else:
        print(f"Error: {response.status_code} for retrieving index")

    return index_page

def transform_index_to_municipalities(index_page) -> dict[str, Any]:
    municipality_list = index_page["gemeentes"]
    municipalities = {d["gemeente"]["cbs_code"]: d for d in municipality_list}
    return municipalities

def create_snapshot(pages: dict[Party, Any], municipalities: dict[str, Any]) -> Snapshot:
    snapshot = Snapshot()

    for party, party_results in pages.items():
        results = party_results["uitslagen"]
        totals = calculate_party_totals(results, municipalities)

        if has_significant_input(totals):
            snapshot.party_snapshots[party] = PartySnapshot(
                totals["this_election"],
                totals["last_election"],
                totals["last_election_corrected"],
                totals["this_election_with_partials"],
                totals["last_election_with_partials"],
            )
    return snapshot

def calculate_party_totals(results: list[dict], municipalities: dict[str, Any]) -> dict:
    totals = {
        "this_election": 0,
        "last_election": 0,
        "municipalities": 0,
        # At the moment, the below 3 values are only used for testing/development.
        # The plan is to use last_election_corrected and this_election_with_partials for the next release.
        # Those values represent a good balance between accuracy and completeness
        "last_election_corrected": 0,
        "this_election_with_partials": 0,
        "last_election_with_partials": 0,
    }

    for result in results:
        votes_this, votes_last = extract_votes(result)

        municipality = municipalities[result["cbs_code"]]
        status = municipality["status"]

        if (not participated_in_both_elections(votes_this, votes_last) and
                # In some cases, a municipality still has a "Nulstand" status even though the results from this year have been reported.
                # In this case, we still skip the municipality, as the various values in 'totals' could get misaligned.
                status != "Nulstand"):
            continue

        totals["municipalities"] += 1

        totals["this_election_with_partials"] += votes_this
        totals["last_election_with_partials"] += votes_last

        if status == "Eindstand":
            totals["this_election"] += votes_this
            totals["last_election"] += votes_last
            totals["last_election_corrected"] += votes_last

        # The double if is intentional here. We want to sum both "Eindstand" and "Tussenstand" results for the correction.
        if status == "Tussenstand":
            totals["last_election_corrected"] += votes_last * turnout_ratio(municipality)

    return totals

def extract_votes(result: dict) -> tuple[int, int]:
    return (
        result["huidige_verkiezing"]["stemmen"],
        result["vorige_verkiezing"]["stemmen"],
    )

def participated_in_both_elections(votes_this: int, votes_last: int) -> bool:
    return votes_this > 0 and votes_last > 0


def turnout_ratio(municipality: dict) -> float:
    partial_turnout_this_election = municipality["huidige_verkiezing"]["opkomst_promillage"]
    turnout_last_election = municipality["vorige_verkiezing"]["opkomst_promillage"]

    if turnout_last_election == 0:
        return 0

    return min(partial_turnout_this_election / turnout_last_election, 1)


def has_significant_input(totals: dict) -> bool:
    return (
        totals["municipalities"] > MINIMUM_NUMBER_OF_MUNICIPALITIES
        and totals["this_election"] > MINIMUM_NUMBER_OF_VOTES
    )

def dump_files_for_debugging(pages: dict[Party, Any], index_page: dict):
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    for party, page in pages.items():
        filename = "debugging/" + "results " + timestamp + " " + party.name + ".json"

        with open(filename, "a") as f:
            json.dump(page, f, indent=2)

    filename = "debugging/" + "results " + timestamp + " index.json"
    with open(filename, "a") as f:
        json.dump(index_page, f, indent=2)

if __name__ == "__main__":
    main()
    # file = File("data")
    # file.compress_jsonl_to_gz()
    # file.upload_gz_to_s3()

