"""Opt-in integration test for the public website feed served from R2."""

import gzip
import os
import unittest
from pathlib import Path

import requests
from dotenv import load_dotenv

from election_data import load_active_elections
from file import File


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPOSITORY_ROOT / ".env")


class R2PublicFeedIntegrationTest(unittest.TestCase):
    """Upload the active election feed, then fetch it through the public R2 URL."""

    def setUp(self) -> None:
        if os.getenv("RUN_R2_INTEGRATION") != "1":
            self.skipTest("Set RUN_R2_INTEGRATION=1 to use the live R2 bucket")

        required = (
            "CLOUDFLARE_R2_UPLOAD_BASE_URL or CLOUDFLARE_R2_UPLOAD_URL",
            "CLOUDFLARE_R2_WRITE_TOKEN",
            "CLOUDFLARE_R2_FEED_URL",
        )
        missing = [name for name in required if not any(os.getenv(option) for option in name.split(" or "))]
        if missing:
            self.skipTest("Missing configuration: " + ", ".join(missing))

        self.current_election = load_active_elections().current
        self.feed_path = REPOSITORY_ROOT / f"data-{self.current_election}.jsonl.gz"
        if not self.feed_path.is_file():
            self.skipTest("Create data.jsonl.gz before running the live R2 test")

    def test_upload_feed_and_retrieve_it_as_the_website_does(self) -> None:
        feed = File(f"data-{self.current_election}")
        feed.upload_gz_to_cloudflare_r2()

        response = requests.get(os.environ["CLOUDFLARE_R2_FEED_URL"], timeout=30)
        response.raise_for_status()

        expected = self.feed_path.read_bytes()
        self.assertEqual(response.content, expected)
        self.assertTrue(gzip.decompress(response.content))


if __name__ == "__main__":
    unittest.main()
