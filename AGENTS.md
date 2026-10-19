# AI contributor guide

This file is the working guide for AI assistants and other contributors in this repository. Read it before changing code. The Git repository root is this `Backend` directory.

## Project purpose

This Python backend reads election result data, estimates vote totals, and publishes JSON snapshots consumed by VerkiezingsWinnaar.nl. Keep election calculations explainable and preserve compatibility with the frontend's existing JSON format unless a change explicitly includes a coordinated schema update.

## Start here

- `main_api.py`: primary polling entry point; retrieves party and municipality result data, computes snapshots, writes output, and uploads compressed data to Cloudflare R2.
- `snapshot.py`: prediction calculations and serialized top-level snapshot schema.
- `party_snapshot.py`: per-party metrics and serialization.
- `party.py`, `party_constants.py`, `config.py`: party metadata, historical vote totals, thresholds, and environment configuration.
- `file.py`: local output, compression, and Cloudflare R2 publishing.
- `main_replay_elections.py`: replay entry point for saved JSONL elections; currently writes and uploads snapshots too.
- `replay/`: captured election data. `testdata/`: synthetic development data, despite election-like filenames.

## Working conventions

- Match the existing Python style and keep changes focused. There is no declared Python version, dependency manifest, formatter, or test suite in the repository; do not invent project-wide tooling or claim checks that were not run.
- Use descriptive names that reflect the Dutch election domain and the existing JSON/API field names. Explain non-obvious election rules near the calculation they affect.
- Keep calculations deterministic for a given input. Avoid silently changing rounding, thresholds, municipality inclusion rules, or party identities.
- Preserve the JSON keys and meanings emitted by `Snapshot.to_dict()` and `PartySnapshot.to_dict()` unless the task explicitly requires a schema change. Treat serialized output as a frontend contract.
- Do not edit captured replay/test data to make a calculation appear correct. If a fixture truly needs a change, explain why and keep the change minimal.
- Do not put credentials, private API URLs, or tokens in source or documentation. `.env` is ignored; refer to `URL_API` and `URL_API_INDEX` by name only.

## Election-data invariants

- `main_api.py` builds municipality lookup by `cbs_code` and reads result status (`Nulstand`, `Tussenstand`, `Eindstand`) to decide which figures feed each total.
- A municipality is currently included in party totals only when both current- and previous-election votes are positive. `Nulstand` is skipped. Full and partial totals intentionally differ.
- Turnout correction is capped at 1 and returns 0 when previous-election turnout is 0.
- `PartySnapshot.factor` is current votes divided by previous votes, or 0 when previous votes are 0. Avoid introducing unguarded divisions in prediction paths; snapshots can be empty or contain zero totals.
- Party historical totals and the threshold in `party_constants.py` / `config.py` affect whether a party is predicted from historical growth or from current share. These are domain assumptions, not generic tuning knobs.

## Safe development workflow

1. Read the affected calculation and its serializer before editing; check callers and JSON keys.
2. Prefer replay/testdata and pure calculation paths for local inspection. Do not run `main_api.py` or `main_replay_elections.py` as routine verification: both are infinite polling/replay loops and can perform Cloudflare R2 uploads.
3. Do not call external APIs, upload/delete remote election data, change Cloudflare resources, or publish a new feed unless the user explicitly requested that operation.
4. If asked to run a script, first verify its side effects and use a bounded, local-only check when possible.
5. Review the resulting diff for unintended changes, especially to fixture files, output schema, `.env`, and generated `data.jsonl`/compressed files.

## Current limitations to keep in mind

- Runtime dependencies are declared in `pyproject.toml` and pinned by `uv.lock`.
- `main_api.py` and the replay script write local snapshots and upload gzip output to Cloudflare R2.
- The README's setup and high-level architecture notes are incomplete; verify commands against code before relying on them.
- Seat allocation is not implemented (`Snapshot.determine_seats()` is a placeholder).
