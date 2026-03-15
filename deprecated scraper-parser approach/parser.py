""""
Deprecated. Got replaced by the API approach in main_api.py.
"""

import re
from itertools import zip_longest

from bs4 import BeautifulSoup

from config import PARSER_HTML_ELEMENT_TO_EXTRACT, PARSER_HTML_CLASS_TO_EXTRACT, PARSER_REGEX
from party_constants import PartyConstants
from party_snapshot import PartySnapshot
from snapshot import Snapshot

class Parser:
    @staticmethod
    def parse_page(page) -> Snapshot:
        page_content = Parser.extract_page_content(page)

        # Sort by length descending to prevent a partial match from blocking a complete match (GLPVDA vs LP)
        parties_sorted = sorted(PartyConstants.parties, key=lambda party: party.name, reverse=True)
        escaped_parties = [re.escape(party.name) for party in parties_sorted]
        regex_string_parties = "|".join(escaped_parties)

        # Match whole words only
        regex_string = r"\b(" + regex_string_parties + r")\b"
        regex_pattern = re.compile(regex_string)

        party_name_matches = list(regex_pattern.finditer(page_content))

        snapshot = Snapshot()
        # list(zip_longest([aap, noot, mies], [noot, mies])) -> [(aap, noot), (noot, mies), (mies, None)]
        for current_party_match, next_party_match in zip_longest(party_name_matches, party_name_matches[1:]):
            party_snapshot = Parser.create_party_snapshot(page_content, current_party_match, next_party_match)

            party_name = current_party_match.group()
            party = next((p for p in PartyConstants.parties if p.name == party_name), None)
            snapshot.party_snapshots[party] = party_snapshot

        return snapshot

    @staticmethod
    def create_party_snapshot(page_content, current_party_match, next_party_match) -> PartySnapshot:
        section_start = current_party_match.start()
        section_end = next_party_match.start() if next_party_match else len(page_content)

        section_text = page_content[section_start:section_end].strip()


        snapshot_results_as_string = re.findall(PARSER_REGEX, section_text)
        snapshot_results = [int(string.replace(".", "")) for string in snapshot_results_as_string]

        snapshot_votes_this_election = snapshot_results[0] if len(snapshot_results) > 0 else 0
        snapshot_votes_last_election = snapshot_results[1] if len(snapshot_results) > 1 else 0

        return PartySnapshot(snapshot_votes_this_election, snapshot_votes_last_election)

    @staticmethod
    def extract_page_content(page) -> str:
        soup = BeautifulSoup(page, "lxml")

        # Extract the post content
        post_content = soup.find(PARSER_HTML_ELEMENT_TO_EXTRACT, class_=PARSER_HTML_CLASS_TO_EXTRACT)

        content = ""
        if post_content:
            content = post_content.get_text()

        return content
