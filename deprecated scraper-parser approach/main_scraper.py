"""
You can probably ignore this script.
It was used to call the Scraper, which would then scrape the election results.
Since then, main_api became the main approach of obtaining the election results.
"""
import copy

from config import URL_SCRAPER
from file import File
from parser import Parser
from scraper import Scraper

def main():
    with Scraper(URL_SCRAPER, interval=1) as scraper:

        previous_party_snapshots = {}
        # Return a new HTML every time the page updates.
        for html in scraper.poll_changes():
            snapshot = Parser.parse_page(html)

            if previous_party_snapshots != snapshot.party_snapshots:
                previous_party_snapshots = copy.deepcopy(snapshot.party_snapshots)

                snapshot.predict_votes_and_percentages()
                snapshot_dict = snapshot.to_dict()

                file = File("data")
                file.dump_to_json(snapshot_dict)
                file.dump_to_jsonl(snapshot_dict)
                file.compress_jsonl_to_gz()
                file.upload_json_to_s3()
                file.upload_gz_to_s3()


if __name__ == "__main__":
    main()
