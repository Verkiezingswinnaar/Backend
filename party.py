from dataclasses import dataclass

from config import URL_API

@dataclass(frozen=True)
class Party:
    name: str
    votes_last_election: int
    is_above_threshold_last_election: bool

    def get_api_url(self):
        return URL_API + self.name + ".json"
