import os

from dotenv import load_dotenv

load_dotenv()

### General config settings
URL_API = os.getenv("URL_API")
URL_API_INDEX = os.getenv("URL_API_INDEX")

# For new parties (and parties with very little votes during the last election)
# we cannot base the prediction for that party on the votes from the last election.
PARTY_LAST_ELECTION_VOTES_THRESHOLD = 10000

# We only add a party to a snapshot if both the following 2 thresholds have been exceeded
# For now, we set both values to 0 to not lose any data and to show data as early as possible.
# It might be an option to do the filtering of the first results from the frontend (or manually during the night)
MINIMUM_NUMBER_OF_MUNICIPALITIES = 0
MINIMUM_NUMBER_OF_VOTES = 0


### Scraper & Parser config settings. Deprecated since main_api is now the primary approach for obtaining the election results.
URL_SCRAPER = os.getenv("URL_SCRAPER")

# Files to explain to the parser what to extract.
PARSER_HTML_ELEMENT_TO_EXTRACT = "div"
PARSER_HTML_CLASS_TO_EXTRACT = "min-h-screen w-full"

# Extract votes before the word 'stemmen'
# Regex:
# \d → matches a single digit (0–9)            #
# [\d.]* → matches 0 or more characters that are digits or a period (.)
# (...) only return what's between the brackets
PARSER_REGEX = r"(\d[\d.]*) stemmen"