""""
Deprecated. Got replaced by the API approach in main_api.py.
"""

import time
from typing import Generator

from camoufox.sync_api import Camoufox

class Scraper:
    def __init__(self, url: str, interval: float = 1.0):
        self.url = url
        self.interval = interval
        self.browser = None
        self.page = None

    # Called when 'with' is called in the other thread
    def __enter__(self):
        self.browser = Camoufox().__enter__()
        self.page = self.browser.new_page()
        self.page.goto(self.url)
        self.page.wait_for_load_state()

        # Sleep for 2 seconds to ensure that the JavaScript is properly loaded in.
        time.sleep(2)

        return self

    # Code to call when 'with' is exited. Not really needed as this script never exits the 'with' block
    # But good practice to do so anyway.
    def __exit__(self, exc_type, exc, tb):
        if self.browser:
            self.browser.__exit__(exc_type, exc, tb)

    # Check the page for any changes. Yield them if there are indeed changes.
    def poll_changes(self) -> Generator[str, None, None]:
        previous = None

        while True:
            current = self.page.content()

            if current != previous:
                yield current
                previous = current

            time.sleep(self.interval)

