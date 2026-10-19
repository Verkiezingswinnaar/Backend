from dataclasses import dataclass

@dataclass(frozen=True)
class Party:
    name: str
    votes_last_election: int
    is_above_threshold_last_election: bool

    def get_api_url(self, api_base_url: str):
        return api_base_url + self.name + ".json"
