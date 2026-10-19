"""
This script handles local files and Cloudflare R2 uploads for the Verkiezingswinnaar project.
"""

import gzip
import json
import os
import re
import shutil
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

class File:
    filename_json: str
    filename_jsonl: str
    filename_gz: str
    backend_dir = Path(__file__).resolve().parent

    def __init__(self, filename):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        os.makedirs("debugging/", exist_ok=True)
        self.filename_json = "debugging/" + filename + " " + timestamp + ".json"
        self.filename_jsonl = filename + ".jsonl"
        self.filename_gz = self.filename_jsonl + ".gz"

    def dump_to_json(self, data: dict) -> None:
        with open(self.filename_json, "a") as f:
            json.dump(data, f, indent=2)

    def dump_to_jsonl(self, data: dict) -> None:
        with open(self.filename_jsonl, "a") as f:
            json.dump(data, f, separators=(',', ':'))
            f.write("\n")

    def compress_jsonl_to_gz(self) -> None:
        with open(self.filename_jsonl, "rb") as f_in:
            with gzip.open(self.filename_gz, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out) # type: ignore

    def upload_to_cloudflare_r2(self, filename: str) -> None:
        upload_base_url = os.getenv("CLOUDFLARE_R2_UPLOAD_BASE_URL")
        legacy_upload_url = os.getenv("CLOUDFLARE_R2_UPLOAD_URL")
        write_token = os.getenv("CLOUDFLARE_R2_WRITE_TOKEN")
        missing = [
            name
            for name, value in (
                ("CLOUDFLARE_R2_UPLOAD_BASE_URL or CLOUDFLARE_R2_UPLOAD_URL", upload_base_url or legacy_upload_url),
                ("CLOUDFLARE_R2_WRITE_TOKEN", write_token),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing Cloudflare R2 configuration: " + ", ".join(missing)
            )

        object_name = os.path.basename(filename)
        allowed_name = (
            object_name == "active-elections.json"
            or re.fullmatch(r"results-[A-Z][A-Z0-9]*\.json", object_name)
            or re.fullmatch(r"data-[A-Z][A-Z0-9]*\.jsonl\.gz", object_name)
            or object_name == "data-test.jsonl.gz"
        )
        if not allowed_name:
            raise ValueError("The R2 Worker only accepts election settings, results, and election feed files")

        if upload_base_url:
            base = urlsplit(upload_base_url)
            if base.scheme != "https" or not base.netloc:
                raise ValueError("CLOUDFLARE_R2_UPLOAD_BASE_URL must be an HTTPS URL")
            base_path = base.path.rstrip("/")
        else:
            legacy = urlsplit(legacy_upload_url or "")
            if legacy.scheme != "https" or not legacy.netloc:
                raise ValueError("CLOUDFLARE_R2_UPLOAD_URL must be an HTTPS Worker URL")
            base_path = legacy.path.rsplit("/", 1)[0]
            base = legacy
        upload_url = urlunsplit((base.scheme, base.netloc, f"{base_path}/{object_name}", "", ""))

        file_path = Path(filename)
        if not file_path.is_file():
            file_path = self.backend_dir / filename
        if not file_path.is_file():
            raise FileNotFoundError(filename)

        content_type = "application/gzip" if object_name.endswith(".gz") else "application/json"
        with file_path.open("rb") as feed:
            response = requests.put(
                upload_url,
                data=feed,
                headers={"Authorization": f"Bearer {write_token}", "Content-Type": content_type},
                timeout=60,
            )
        response.raise_for_status()
        print(filename + " uploaded")

    def upload_gz_to_cloudflare_r2(self) -> None:
        self.upload_to_cloudflare_r2(self.filename_gz)

    def delete_jsonl(self):
        if os.path.exists(self.filename_jsonl):
            os.remove(self.filename_jsonl)
