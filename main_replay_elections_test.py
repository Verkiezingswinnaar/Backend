"""Replay one historical election feed for frontend/R2 testing.

Unlike main_replay_elections.py this helper is single-pass, defaults to local
output, and restricts R2 mode to the dedicated data-test.jsonl.gz object.
"""

import argparse
import gzip
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from party_constants import PartyConstants
from party_snapshot import PartySnapshot
from snapshot import Snapshot


BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_FIXTURE = BACKEND_DIR / "testdata" / "GR2026-03-17.jsonl"
DEFAULT_OUTPUT = BACKEND_DIR / "data-TK2025.jsonl.gz"
TEST_OBJECT_NAME = "data-test.jsonl.gz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("local", "r2"), nargs="?", default="local")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE,
                        help=f"JSONL election fixture (default: {DEFAULT_FIXTURE.name})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Local gzip output path (used in local mode and retained in R2 mode)")
    parser.add_argument("--interval", type=float, default=4.0,
                        help="Seconds between visible snapshots (default: 4)")
    return parser.parse_args()


def load_snapshots(path: Path) -> list[str]:
    snapshots: list[str] = []
    with path.open("r", encoding="utf-8") as feed:
        for line_number, line in enumerate(feed, start=1):
            if not line.strip():
                continue
            try:
                snapshot = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on line {line_number} in {path}") from error
            if not isinstance(snapshot, dict) or not isinstance(snapshot.get("timestamp"), (int, float)):
                raise ValueError(f"Line {line_number} in {path} is not a snapshot")
            prepared = prepare_snapshot(snapshot)
            snapshots.append(json.dumps(prepared, separators=(",", ":"), ensure_ascii=False))
    if not snapshots:
        raise ValueError(f"No snapshots found in {path}")
    return snapshots


def prepare_snapshot(source: dict) -> dict:
    """Apply the same forecast calculation as the original election replay."""
    snapshot = Snapshot()
    snapshot.timestamp = int(source["timestamp"])
    unmodeled_parties: dict[str, dict] = {}
    for party_name, values in source.get("party_snapshots", {}).items():
        party = next((item for item in PartyConstants.parties if item.name == party_name), None)
        if party is None:
            # Some fixtures include OVERIG, which has no historical Party
            # object because it is not forecast as an individual party. Keep
            # its recorded values without trying to calculate a forecast.
            unmodeled_parties[party_name] = values
            continue
        snapshot.party_snapshots[party] = PartySnapshot(
            values.get("votes_this_election", 0),
            values.get("votes_last_election", 0),
        )
    try:
        snapshot.predict_votes_and_percentages()
    except ZeroDivisionError:
        # The earliest fixture snapshots can have no usable votes yet. Keep
        # their source values, which the frontend presents as no forecast.
        return source

    prepared = snapshot.to_dict()
    prepared["party_snapshots"].update(unmodeled_parties)
    optional_fields = (
        "municipalities",
        "votes_last_election_corrected",
        "votes_this_election_with_partials",
        "votes_last_election_with_partials",
    )
    for party_name, values in source.get("party_snapshots", {}).items():
        result_values = prepared["party_snapshots"].get(party_name)
        if result_values is None:
            continue
        for field in optional_fields:
            if field in values:
                result_values[field] = values[field]
            else:
                result_values.pop(field, None)
    return prepared


def upload_test_feed(path: Path) -> None:
    upload_url = os.getenv("CLOUDFLARE_R2_TEST_UPLOAD_URL", "")
    write_token = os.getenv("CLOUDFLARE_R2_WRITE_TOKEN", "")
    parsed = urlparse(upload_url)
    if not upload_url or not write_token:
        raise RuntimeError("Set CLOUDFLARE_R2_TEST_UPLOAD_URL and CLOUDFLARE_R2_WRITE_TOKEN for R2 mode")
    if parsed.scheme != "https" or parsed.path.rstrip("/").split("/")[-1] != TEST_OBJECT_NAME:
        raise ValueError(f"R2 mode only permits an HTTPS upload URL ending in /{TEST_OBJECT_NAME}")
    with path.open("rb") as compressed_feed:
        response = requests.put(
            upload_url,
            data=compressed_feed,
            headers={"Authorization": f"Bearer {write_token}", "Content-Type": "application/gzip"},
            timeout=30,
        )
    response.raise_for_status()


def run_replay(mode: str, fixture: Path, output: Path, interval: float) -> None:
    if interval < 0:
        raise ValueError("--interval must be zero or greater")
    lines = load_snapshots(fixture)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path = output.with_suffix("")
    jsonl_path.write_text("", encoding="utf-8")

    print(f"Replaying {len(lines)} snapshots from {fixture} in {mode} mode.", flush=True)
    for index, line in enumerate(lines, start=1):
        with jsonl_path.open("a", encoding="utf-8", newline="\n") as feed:
            feed.write(line + "\n")
        with jsonl_path.open("rb") as source, output.open("wb") as destination:
            with gzip.GzipFile(fileobj=destination, mode="wb", mtime=0) as compressed:
                while chunk := source.read(1024 * 1024):
                    compressed.write(chunk)
        if mode == "r2":
            upload_test_feed(output)
        print(f"Snapshot {index}/{len(lines)} - {time.strftime('%H:%M:%S')}", flush=True)
        if index < len(lines) and interval:
            time.sleep(interval)
    print(f"Replay complete. Feed available at {output}", flush=True)


if __name__ == "__main__":
    try:
        arguments = parse_args()
        run_replay(arguments.mode, arguments.fixture.resolve(), arguments.output, arguments.interval)
    except (OSError, ValueError, RuntimeError, requests.RequestException) as error:
        print(f"Replay failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
