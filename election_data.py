"""Load active election settings and per-election result files."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parent
ELECTION_ID_PATTERN = re.compile(r"^[A-Z0-9]+$")
ELECTION_TYPES = {"municipal", "provincial", "national", "other"}


@dataclass(frozen=True)
class ActiveElections:
    current: str
    previous: str


@dataclass(frozen=True)
class ElectionResults:
    id: str
    name: str
    label: str
    election_type: str
    votes: dict[str, int]
    seats: dict[str, int]

    @property
    def total_votes(self) -> int:
        return sum(self.votes.values())


def _read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to read election data from {path.name}") from error


def _validate_election_id(election_id: Any, field_name: str) -> str:
    if not isinstance(election_id, str) or not ELECTION_ID_PATTERN.fullmatch(election_id):
        raise ValueError(f"{field_name} must be an uppercase election ID such as TK2025")
    return election_id


def load_active_elections(path: Path | None = None) -> ActiveElections:
    settings_path = path or BACKEND_DIR / "active-elections.json"
    data = _read_json(settings_path)
    if not isinstance(data, dict):
        raise ValueError("active-elections.json must contain an object")
    current = _validate_election_id(data.get("current"), "current")
    previous = _validate_election_id(data.get("previous"), "previous")
    if current == previous:
        raise ValueError("Current and previous election IDs must be different")
    return ActiveElections(current=current, previous=previous)


def _vote_map(value: Any, field_name: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    result: dict[str, int] = {}
    for party_code, count in value.items():
        if not isinstance(party_code, str) or not party_code:
            raise ValueError(f"{field_name} contains an invalid party code")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{field_name}.{party_code} must be a non-negative integer")
        result[party_code] = count
    return result


def load_election_results(election_id: str, results_dir: Path | None = None) -> ElectionResults:
    safe_id = _validate_election_id(election_id, "election ID")
    base_dir = results_dir or BACKEND_DIR
    path = base_dir / f"results-{safe_id}.json"
    data = _read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain an object")
    if data.get("id") != safe_id:
        raise ValueError(f"{path.name} has an election ID that does not match its filename")

    election_type = data.get("type")
    if election_type not in ELECTION_TYPES:
        raise ValueError(f"{path.name} has an unsupported election type")
    name = data.get("name")
    label = data.get("label")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{path.name} must include an election name")
    if not isinstance(label, str) or not label.strip():
        raise ValueError(f"{path.name} must include an election label")

    return ElectionResults(
        id=safe_id,
        name=name,
        label=label,
        election_type=election_type,
        votes=_vote_map(data.get("votes"), "votes"),
        seats=_vote_map(data.get("seats", {}), "seats"),
    )
